"""Background tasks for parsing and processing Splunk configurations."""

import logging
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

from celery import Task
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.file import File as FileModel
from app.models.ingestion_run import IngestionRun, IngestionStatus
from app.models.stanza import Stanza
from app.parser import ConfParser, ParserError
from app.storage import get_storage_backend
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task that handles database sessions properly."""

    _db: Session | None = None

    def after_return(
        self,
        status: str,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None

    @property
    def db(self) -> Session:
        """Get or create database session for this task."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.worker.tasks.parse_run",
    max_retries=3,
    default_retry_delay=60,  # 1 minute base delay
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,  # Add randomness to prevent thundering herd
)
def parse_run(self: DatabaseTask, run_id: int) -> dict[str, Any]:
    """Parse configuration files for an ingestion run.

    This task:
    1. Retrieves the uploaded archive from storage
    2. Extracts configuration files (.conf files)
    3. Parses each file using ConfParser
    4. Persists parsed stanzas to the database
    5. Updates run status to COMPLETE or FAILED

    The task is idempotent - safe to retry if interrupted.

    Args:
        run_id: ID of the ingestion run to parse

    Returns:
        dict: Results summary with counts and duration

    Raises:
        Exception: On permanent failures (will be retried up to max_retries)
    """
    start_time = time.time()
    logger.info(f"Starting parse_run task for run_id={run_id}")

    db = self.db
    settings = get_settings()

    try:
        # Fetch ingestion run
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if not run:
            error_msg = f"Ingestion run {run_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Check if already completed
        if run.status == IngestionStatus.COMPLETE:
            logger.info(f"Run {run_id} already completed, skipping")
            return {
                "run_id": run_id,
                "status": "already_completed",
                "duration_seconds": 0,
            }

        # Update status to parsing
        run.status = IngestionStatus.PARSING
        db.commit()
        logger.info(f"Updated run {run_id} status to PARSING")

        # Get uploaded files
        files = db.query(FileModel).filter(FileModel.run_id == run_id).all()
        if not files:
            error_msg = f"No files found for run {run_id}"
            logger.error(error_msg)
            run.status = IngestionStatus.FAILED
            run.notes = f"{run.notes}\n{error_msg}" if run.notes else error_msg
            db.commit()
            raise ValueError(error_msg)

        # Initialize storage backend
        storage = get_storage_backend(
            backend_type=settings.storage_backend,
            storage_path=settings.storage_path
            if settings.storage_backend == "local"
            else None,
            s3_bucket=settings.s3_bucket if settings.storage_backend == "s3" else None,
            s3_endpoint_url=settings.s3_endpoint_url
            if settings.storage_backend == "s3"
            else None,
            aws_access_key_id=settings.aws_access_key_id
            if settings.storage_backend == "s3"
            else None,
            aws_secret_access_key=settings.aws_secret_access_key
            if settings.storage_backend == "s3"
            else None,
        )

        total_stanzas = 0
        total_files_parsed = 0

        # Process each uploaded file
        for file_record in files:
            logger.info(
                f"Processing file {file_record.path} (id={file_record.id})",
                extra={"run_id": run_id, "file_id": file_record.id},
            )

            # Retrieve file from storage
            blob = storage.retrieve_blob(file_record.stored_object_key)

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                archive_path = temp_path / file_record.path

                # Save archive to temp file
                with open(archive_path, "wb") as f:
                    f.write(blob.read())

                # Extract archive
                extracted_files = _extract_archive(archive_path, temp_path)
                logger.info(
                    f"Extracted {len(extracted_files)} files from archive",
                    extra={"run_id": run_id, "file_id": file_record.id},
                )

                # Parse each .conf file
                parser = ConfParser()
                for conf_file in extracted_files:
                    if not conf_file.name.endswith(".conf"):
                        continue

                    try:
                        stanzas = parser.parse_file(str(conf_file))
                        total_files_parsed += 1

                        # Determine conf type from filename
                        conf_type = _determine_conf_type(conf_file.name)

                        # Persist stanzas
                        for stanza in stanzas:
                            stanza_record = Stanza(
                                run_id=run_id,
                                file_id=file_record.id,
                                conf_type=conf_type,
                                name=stanza.name,
                                app=stanza.provenance.app
                                if stanza.provenance
                                else None,
                                scope=stanza.provenance.scope
                                if stanza.provenance
                                else None,
                                layer=stanza.provenance.layer
                                if stanza.provenance
                                else None,
                                order_in_file=stanza.provenance.order_in_file
                                if stanza.provenance
                                else None,
                                source_path=stanza.provenance.source_path
                                if stanza.provenance
                                else str(conf_file),
                                raw_kv=dict(stanza.keys),
                            )
                            db.add(stanza_record)
                            total_stanzas += 1

                        logger.debug(
                            f"Parsed {len(stanzas)} stanzas from {conf_file.name}",
                            extra={
                                "run_id": run_id,
                                "file_id": file_record.id,
                                "conf_file": conf_file.name,
                            },
                        )

                    except ParserError as e:
                        logger.warning(
                            f"Failed to parse {conf_file.name}: {e}",
                            extra={
                                "run_id": run_id,
                                "file_id": file_record.id,
                                "conf_file": conf_file.name,
                            },
                        )
                        # Continue parsing other files

        # Update run status to complete
        run.status = IngestionStatus.COMPLETE
        db.commit()

        duration = time.time() - start_time
        result = {
            "run_id": run_id,
            "status": "completed",
            "files_parsed": total_files_parsed,
            "stanzas_created": total_stanzas,
            "duration_seconds": duration,
        }

        logger.info(
            f"Completed parse_run task for run_id={run_id}",
            extra=result,
        )

        return result

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Error in parse_run task for run_id={run_id}: {e}",
            extra={"run_id": run_id, "duration_seconds": duration},
            exc_info=True,
        )

        # Update run status to failed if this is the last retry
        if self.request.retries >= self.max_retries:
            run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
            if run:
                run.status = IngestionStatus.FAILED
                error_msg = f"Parsing failed after {self.max_retries} retries: {str(e)}"
                run.notes = f"{run.notes}\n{error_msg}" if run.notes else error_msg
                db.commit()
                logger.error(f"Marked run {run_id} as FAILED after exhausting retries")

        # Re-raise to trigger retry
        raise


def _extract_archive(archive_path: Path, extract_to: Path) -> list[Path]:
    """Extract tar.gz or zip archive and return list of extracted files.

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to

    Returns:
        List of extracted file paths

    Raises:
        ValueError: If archive format is unsupported or extraction fails
    """
    extracted_files: list[Path] = []

    try:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix == ".gz" or archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_to)
        elif archive_path.suffix == ".tar":
            with tarfile.open(archive_path, "r") as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

        # Collect all extracted files recursively
        for file_path in extract_to.rglob("*"):
            if file_path.is_file():
                extracted_files.append(file_path)

        return extracted_files

    except Exception as e:
        logger.error(f"Failed to extract archive {archive_path}: {e}")
        raise ValueError(f"Archive extraction failed: {e}") from e


def _determine_conf_type(filename: str) -> str:
    """Determine configuration type from filename.

    Args:
        filename: Configuration filename (e.g., "inputs.conf")

    Returns:
        Configuration type (inputs, props, transforms, etc.)
    """
    # Remove .conf extension
    base_name = filename.replace(".conf", "")

    # Map known types
    known_types = {
        "inputs": "inputs",
        "props": "props",
        "transforms": "transforms",
        "indexes": "indexes",
        "outputs": "outputs",
        "serverclass": "serverclasses",
    }

    return known_types.get(base_name.lower(), "other")

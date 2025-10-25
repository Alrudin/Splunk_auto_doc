"""Background tasks for parsing and processing Splunk configurations."""

import logging
import tarfile
import tempfile
import time
import traceback
import zipfile
from pathlib import Path
from typing import Any

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.file import File as FileModel
from app.models.index import Index
from app.models.ingestion_run import IngestionRun, IngestionStatus
from app.models.input import Input
from app.models.output import Output
from app.models.props import Props
from app.models.serverclass import Serverclass
from app.models.stanza import Stanza
from app.models.transform import Transform
from app.parser import ConfParser, ParserError
from app.projections.indexes import IndexProjector
from app.projections.inputs import InputProjector
from app.projections.outputs import OutputProjector
from app.projections.props import PropsProjector
from app.projections.serverclasses import ServerclassProjector
from app.projections.transforms import TransformProjector
from app.storage import get_storage_backend
from app.worker.celery_app import celery_app
from app.worker.exceptions import PermanentError, TransientError

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
    autoretry_for=(),  # We'll handle retries manually
    acks_late=True,  # Acknowledge after task completes
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
        PermanentError: For unrecoverable errors (won't retry)
        TransientError: For temporary errors (will retry with backoff)
    """
    start_time = time.time()
    logger.info(
        f"Starting parse_run task for run_id={run_id}",
        extra={"run_id": run_id, "task_id": self.request.id},
    )

    db = self.db
    settings = get_settings()

    # Heartbeat interval (update every 30 seconds for long-running tasks)
    last_heartbeat = time.time()
    heartbeat_interval = 30

    def update_heartbeat() -> None:
        """Update heartbeat timestamp for visibility timeout."""
        nonlocal last_heartbeat
        now = time.time()
        if now - last_heartbeat >= heartbeat_interval:
            try:
                run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
                if run:
                    from datetime import datetime

                    run.last_heartbeat = datetime.utcnow()
                    db.commit()
                    last_heartbeat = now
                    logger.debug(f"Updated heartbeat for run {run_id}")
            except Exception as e:
                logger.warning(f"Failed to update heartbeat: {e}")

    try:
        # Fetch ingestion run
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if not run:
            error_msg = f"Ingestion run {run_id} not found"
            logger.error(error_msg)
            raise PermanentError(error_msg)

        # Update task tracking
        from datetime import datetime

        run.task_id = self.request.id
        run.retry_count = self.request.retries

        # Check if already completed (idempotency)
        if run.status == IngestionStatus.COMPLETE:
            logger.info(f"Run {run_id} already completed, skipping")
            return {
                "run_id": run_id,
                "status": "already_completed",
                "duration_seconds": 0,
            }

        # Update status to parsing and set started timestamp
        if run.status != IngestionStatus.PARSING:
            run.status = IngestionStatus.PARSING
            run.started_at = datetime.utcnow()
        run.last_heartbeat = datetime.utcnow()
        db.commit()
        logger.info(f"Updated run {run_id} status to PARSING")

        # Get uploaded files
        files = db.query(FileModel).filter(FileModel.run_id == run_id).all()
        if not files:
            error_msg = f"No files found for run {run_id}"
            logger.error(error_msg)
            raise PermanentError(error_msg)

        # Initialize storage backend
        try:
            storage = get_storage_backend(
                backend_type=settings.storage_backend,
                storage_path=settings.storage_path
                if settings.storage_backend == "local"
                else None,
                s3_bucket=settings.s3_bucket
                if settings.storage_backend == "s3"
                else None,
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
        except Exception as e:
            logger.error(f"Failed to initialize storage backend: {e}")
            raise TransientError(f"Storage backend initialization failed: {e}") from e

        total_stanzas = 0
        total_files_parsed = 0
        parse_errors = []

        # Accumulate stanzas for bulk insert
        stanza_rows = []
        # Group parsed stanzas by conf_type for typed projection
        stanza_batches: dict[str, list[Any]] = {
            "inputs": [],
            "props": [],
            "transforms": [],
            "indexes": [],
            "outputs": [],
            "serverclasses": [],
        }

        # Process each uploaded file
        for file_record in files:
            update_heartbeat()

            logger.info(
                f"Processing file {file_record.path} (id={file_record.id})",
                extra={"run_id": run_id, "file_id": file_record.id},
            )

            try:
                # Retrieve file from storage
                blob = storage.retrieve_blob(file_record.stored_object_key)
            except Exception as e:
                logger.error(f"Failed to retrieve file from storage: {e}")
                raise TransientError(f"Storage retrieval failed: {e}") from e

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                archive_path = temp_path / file_record.path

                # Save archive to temp file
                with open(archive_path, "wb") as f:
                    f.write(blob.read())

                # Extract archive
                try:
                    extracted_files = _extract_archive(archive_path, temp_path)
                    logger.info(
                        f"Extracted {len(extracted_files)} files from archive",
                        extra={"run_id": run_id, "file_id": file_record.id},
                    )
                except ValueError as e:
                    # Archive extraction errors are permanent
                    raise PermanentError(f"Invalid archive format: {e}") from e

                # Parse each .conf file
                parser = ConfParser()
                for conf_file in extracted_files:
                    update_heartbeat()

                    if not conf_file.name.endswith(".conf"):
                        continue

                    try:
                        stanzas = parser.parse_file(str(conf_file))
                        total_files_parsed += 1

                        # Determine conf type from filename
                        conf_type = _determine_conf_type(conf_file.name)

                        # Accumulate stanzas for bulk insert
                        for stanza in stanzas:
                            # Build stanza row for bulk insert
                            stanza_row = {
                                "run_id": run_id,
                                "file_id": file_record.id,
                                "conf_type": conf_type,
                                "name": stanza.name,
                                "app": stanza.provenance.app
                                if stanza.provenance
                                else None,
                                "scope": stanza.provenance.scope
                                if stanza.provenance
                                else None,
                                "layer": stanza.provenance.layer
                                if stanza.provenance
                                else None,
                                "order_in_file": stanza.provenance.order_in_file
                                if stanza.provenance
                                else None,
                                "source_path": stanza.provenance.source_path
                                if stanza.provenance
                                else str(conf_file),
                                "raw_kv": dict(stanza.keys),
                            }
                            stanza_rows.append(stanza_row)

                            # Group parsed stanzas for typed projection
                            if conf_type in stanza_batches:
                                stanza_batches[conf_type].append(stanza)

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
                        error_detail = f"Failed to parse {conf_file.name}: {e}"
                        logger.warning(
                            error_detail,
                            extra={
                                "run_id": run_id,
                                "file_id": file_record.id,
                                "conf_file": conf_file.name,
                            },
                        )
                        parse_errors.append(error_detail)
                        # Continue parsing other files

        # Bulk insert stanzas using SQLAlchemy Core
        if stanza_rows:
            try:
                from sqlalchemy import insert

                # Check for existing stanzas to maintain idempotency
                # For simplicity in bulk insert, we'll skip if ANY stanzas exist for this run
                existing_count = (
                    db.query(Stanza).filter(Stanza.run_id == run_id).count()
                )

                if existing_count == 0:
                    # Bulk insert all stanzas at once
                    stmt = insert(Stanza).values(stanza_rows)
                    db.execute(stmt)
                    db.commit()
                    logger.info(
                        f"Bulk inserted {len(stanza_rows)} stanzas",
                        extra={"run_id": run_id},
                    )
                else:
                    logger.info(
                        f"Skipping stanza bulk insert - {existing_count} stanzas already exist for run {run_id}",
                        extra={"run_id": run_id},
                    )
            except Exception as e:
                logger.error(f"Failed to bulk insert stanzas: {e}", exc_info=True)
                raise

        # Create typed projections and bulk insert
        projection_counts = {}
        try:
            projection_counts = _bulk_insert_typed_projections(
                db, stanza_batches, run_id
            )
            db.commit()
            logger.info(
                f"Created typed projections: {projection_counts}",
                extra={"run_id": run_id},
            )
        except Exception as e:
            logger.error(f"Failed to create typed projections: {e}", exc_info=True)
            # Typed projection errors are non-fatal - stanzas are already persisted
            parse_errors.append(f"Typed projection error: {e}")

        # Update run status to complete
        run.status = IngestionStatus.COMPLETE
        run.completed_at = datetime.utcnow()

        # Store metrics
        duration = time.time() - start_time
        run.metrics = {
            "files_parsed": total_files_parsed,
            "stanzas_created": total_stanzas,
            "typed_projections": projection_counts,
            "duration_seconds": duration,
            "parse_errors": len(parse_errors),
            "retry_count": self.request.retries,
        }

        db.commit()

        result = {
            "run_id": run_id,
            "status": "completed",
            "files_parsed": total_files_parsed,
            "stanzas_created": total_stanzas,
            "typed_projections": projection_counts,
            "duration_seconds": duration,
            "parse_errors": parse_errors if parse_errors else None,
        }

        logger.info(
            f"Completed parse_run task for run_id={run_id}",
            extra=result,
        )

        return result

    except PermanentError as e:
        # Permanent errors should not be retried
        duration = time.time() - start_time
        error_msg = str(e)
        error_trace = traceback.format_exc()

        logger.error(
            f"Permanent error in parse_run task for run_id={run_id}: {error_msg}",
            extra={"run_id": run_id, "duration_seconds": duration},
            exc_info=True,
        )

        # Update run status to failed
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if run:
            from datetime import datetime

            run.status = IngestionStatus.FAILED
            run.error_message = f"Permanent error: {error_msg}"
            run.error_traceback = error_trace
            run.completed_at = datetime.utcnow()
            run.metrics = {
                "duration_seconds": duration,
                "retry_count": self.request.retries,
                "error_type": "permanent",
            }
            db.commit()
            logger.error(f"Marked run {run_id} as FAILED (permanent error)")

        # Don't retry permanent errors
        raise

    except TransientError as e:
        # Transient errors should be retried with exponential backoff
        duration = time.time() - start_time
        error_msg = str(e)
        error_trace = traceback.format_exc()

        logger.warning(
            f"Transient error in parse_run task for run_id={run_id}: {error_msg}",
            extra={
                "run_id": run_id,
                "duration_seconds": duration,
                "retry": self.request.retries,
            },
            exc_info=True,
        )

        # Update run with error details
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if run:
            from datetime import datetime

            run.error_message = (
                f"Transient error (retry {self.request.retries}): {error_msg}"
            )
            run.error_traceback = error_trace
            run.last_heartbeat = datetime.utcnow()
            db.commit()

        # Retry with exponential backoff if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            # Calculate backoff: 60s, 180s, 600s (1min, 3min, 10min)
            countdown = min(60 * (3**self.request.retries), 600)
            logger.info(
                f"Retrying run {run_id} in {countdown}s (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e, countdown=countdown) from e
        else:
            # Exhausted retries - mark as failed
            logger.error(f"Exhausted retries for run {run_id}")
            if run:
                from datetime import datetime

                run.status = IngestionStatus.FAILED
                run.error_message = (
                    f"Failed after {self.max_retries} retries: {error_msg}"
                )
                run.completed_at = datetime.utcnow()
                run.metrics = {
                    "duration_seconds": duration,
                    "retry_count": self.request.retries,
                    "error_type": "transient_exhausted",
                }
                db.commit()
            raise

    except SoftTimeLimitExceeded:
        # Task exceeded soft time limit
        duration = time.time() - start_time
        logger.error(f"Task exceeded soft time limit for run_id={run_id}")

        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        if run:
            from datetime import datetime

            run.status = IngestionStatus.FAILED
            run.error_message = "Task exceeded time limit"
            run.completed_at = datetime.utcnow()
            run.metrics = {
                "duration_seconds": duration,
                "retry_count": self.request.retries,
                "error_type": "timeout",
            }
            db.commit()
        raise

    except OperationalError as e:
        # Database errors are usually transient
        duration = time.time() - start_time
        error_msg = str(e)

        logger.error(
            f"Database error in parse_run task for run_id={run_id}: {error_msg}",
            extra={"run_id": run_id, "duration_seconds": duration},
            exc_info=True,
        )

        # Retry database errors with backoff
        if self.request.retries < self.max_retries:
            countdown = min(60 * (3**self.request.retries), 600)
            raise self.retry(
                exc=TransientError(f"Database error: {error_msg}"), countdown=countdown
            ) from e
        else:
            # Mark as failed if retries exhausted
            try:
                run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
                if run:
                    from datetime import datetime

                    run.status = IngestionStatus.FAILED
                    run.error_message = (
                        f"Database error after {self.max_retries} retries: {error_msg}"
                    )
                    run.error_traceback = traceback.format_exc()
                    run.completed_at = datetime.utcnow()
                    db.commit()
            except Exception:
                pass  # Best effort
            raise

    except Exception as e:
        # Unknown errors - treat as transient and retry
        duration = time.time() - start_time
        error_msg = str(e)
        error_trace = traceback.format_exc()

        logger.error(
            f"Unexpected error in parse_run task for run_id={run_id}: {error_msg}",
            extra={"run_id": run_id, "duration_seconds": duration},
            exc_info=True,
        )

        # Update run status to failed if this is the last retry
        if self.request.retries >= self.max_retries:
            run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
            if run:
                from datetime import datetime

                run.status = IngestionStatus.FAILED
                run.error_message = (
                    f"Unexpected error after {self.max_retries} retries: {error_msg}"
                )
                run.error_traceback = error_trace
                run.completed_at = datetime.utcnow()
                run.metrics = {
                    "duration_seconds": duration,
                    "retry_count": self.request.retries,
                    "error_type": "unexpected",
                }
                db.commit()
                logger.error(f"Marked run {run_id} as FAILED after exhausting retries")
            raise
        else:
            # Retry with backoff
            countdown = min(60 * (3**self.request.retries), 600)
            raise self.retry(
                exc=TransientError(f"Unexpected error: {error_msg}"),
                countdown=countdown,
            ) from e


def _extract_archive(archive_path: Path, extract_to: Path) -> list[Path]:
    """Extract tar.gz or zip archive and return list of extracted files.

    Security features:
    - Guards against zip bombs (max 100MB uncompressed per file, 1GB total)
    - Prevents path traversal attacks
    - Blocks symlinks
    - Enforces max file count (10,000 files)
    - Enforces max directory depth (20 levels)

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to

    Returns:
        List of extracted file paths

    Raises:
        ValueError: If archive format is unsupported or extraction fails
    """
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB per file
    MAX_TOTAL_SIZE = 1024 * 1024 * 1024  # 1 GB total
    MAX_FILE_COUNT = 10000  # Maximum files in archive
    MAX_DEPTH = 20  # Maximum directory depth

    extracted_files: list[Path] = []
    total_size = 0
    file_count = 0

    try:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                # Validate zip contents before extraction
                for info in zip_ref.infolist():
                    # Check file count
                    file_count += 1
                    if file_count > MAX_FILE_COUNT:
                        raise ValueError(
                            f"Archive contains too many files (max {MAX_FILE_COUNT})"
                        )

                    # Check for path traversal
                    member_path = Path(extract_to) / info.filename
                    if not str(member_path.resolve()).startswith(
                        str(extract_to.resolve())
                    ):
                        raise ValueError(
                            f"Path traversal detected in archive: {info.filename}"
                        )

                    # Check directory depth
                    depth = len(Path(info.filename).parts)
                    if depth > MAX_DEPTH:
                        raise ValueError(
                            f"Archive path too deep (max {MAX_DEPTH} levels): {info.filename}"
                        )

                    # Check file size (zip bomb protection)
                    if info.file_size > MAX_FILE_SIZE:
                        raise ValueError(
                            f"File too large in archive (max {MAX_FILE_SIZE / 1024 / 1024}MB): {info.filename}"
                        )

                    total_size += info.file_size
                    if total_size > MAX_TOTAL_SIZE:
                        raise ValueError(
                            f"Archive total size too large (max {MAX_TOTAL_SIZE / 1024 / 1024}MB)"
                        )

                # Extract safely
                zip_ref.extractall(extract_to)

        elif archive_path.suffix == ".gz" or archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                # Validate tar contents before extraction
                for member in tar_ref.getmembers():
                    # Check file count
                    file_count += 1
                    if file_count > MAX_FILE_COUNT:
                        raise ValueError(
                            f"Archive contains too many files (max {MAX_FILE_COUNT})"
                        )

                    # Block symlinks and hardlinks
                    if member.issym() or member.islnk():
                        raise ValueError(
                            f"Archive contains symlinks/hardlinks (security risk): {member.name}"
                        )

                    # Check for path traversal
                    member_path = Path(extract_to) / member.name
                    if not str(member_path.resolve()).startswith(
                        str(extract_to.resolve())
                    ):
                        raise ValueError(
                            f"Path traversal detected in archive: {member.name}"
                        )

                    # Check directory depth
                    depth = len(Path(member.name).parts)
                    if depth > MAX_DEPTH:
                        raise ValueError(
                            f"Archive path too deep (max {MAX_DEPTH} levels): {member.name}"
                        )

                    # Check file size
                    if member.size > MAX_FILE_SIZE:
                        raise ValueError(
                            f"File too large in archive (max {MAX_FILE_SIZE / 1024 / 1024}MB): {member.name}"
                        )

                    total_size += member.size
                    if total_size > MAX_TOTAL_SIZE:
                        raise ValueError(
                            f"Archive total size too large (max {MAX_TOTAL_SIZE / 1024 / 1024}MB)"
                        )

                # Extract safely
                tar_ref.extractall(extract_to, filter="data")

        elif archive_path.suffix == ".tar":
            with tarfile.open(archive_path, "r") as tar_ref:
                # Validate tar contents before extraction
                for member in tar_ref.getmembers():
                    # Check file count
                    file_count += 1
                    if file_count > MAX_FILE_COUNT:
                        raise ValueError(
                            f"Archive contains too many files (max {MAX_FILE_COUNT})"
                        )

                    # Block symlinks and hardlinks
                    if member.issym() or member.islnk():
                        raise ValueError(
                            f"Archive contains symlinks/hardlinks (security risk): {member.name}"
                        )

                    # Check for path traversal
                    member_path = Path(extract_to) / member.name
                    if not str(member_path.resolve()).startswith(
                        str(extract_to.resolve())
                    ):
                        raise ValueError(
                            f"Path traversal detected in archive: {member.name}"
                        )

                    # Check directory depth
                    depth = len(Path(member.name).parts)
                    if depth > MAX_DEPTH:
                        raise ValueError(
                            f"Archive path too deep (max {MAX_DEPTH} levels): {member.name}"
                        )

                    # Check file size
                    if member.size > MAX_FILE_SIZE:
                        raise ValueError(
                            f"File too large in archive (max {MAX_FILE_SIZE / 1024 / 1024}MB): {member.name}"
                        )

                    total_size += member.size
                    if total_size > MAX_TOTAL_SIZE:
                        raise ValueError(
                            f"Archive total size too large (max {MAX_TOTAL_SIZE / 1024 / 1024}MB)"
                        )

                # Extract safely
                tar_ref.extractall(extract_to, filter="data")
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

        # Collect all extracted files recursively
        for file_path in extract_to.rglob("*"):
            if file_path.is_file():
                # Final check: ensure no symlinks were created
                if file_path.is_symlink():
                    logger.warning(f"Skipping symlink: {file_path}")
                    continue
                extracted_files.append(file_path)

        logger.info(
            f"Extracted {len(extracted_files)} files from archive (total size: {total_size / 1024 / 1024:.2f}MB)"
        )
        return extracted_files

    except (tarfile.TarError, zipfile.BadZipFile) as e:
        logger.error(f"Invalid or corrupted archive {archive_path}: {e}")
        raise ValueError(f"Invalid or corrupted archive: {e}") from e
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


def _bulk_insert_typed_projections(
    db: Session,
    stanza_batches: dict[str, list[Any]],
    run_id: int,
) -> dict[str, int]:
    """Bulk insert typed projections using SQLAlchemy Core for performance.

    Args:
        db: Database session
        stanza_batches: Dictionary mapping conf_type to list of parsed stanzas
        run_id: Ingestion run ID

    Returns:
        Dictionary with counts of records created for each type

    Raises:
        Exception: If bulk insert fails
    """
    from sqlalchemy import insert

    counts = {
        "inputs": 0,
        "props": 0,
        "transforms": 0,
        "indexes": 0,
        "outputs": 0,
        "serverclasses": 0,
    }

    # Initialize projectors
    projectors = {
        "inputs": InputProjector(),
        "props": PropsProjector(),
        "transforms": TransformProjector(),
        "indexes": IndexProjector(),
        "outputs": OutputProjector(),
        "serverclasses": ServerclassProjector(),
    }

    # Process each conf type
    for conf_type, stanzas in stanza_batches.items():
        if conf_type not in projectors or not stanzas:
            continue

        projector = projectors[conf_type]
        projected_rows = []

        # Project each stanza to typed row
        for stanza in stanzas:
            try:
                projection = projector.project(stanza, run_id)
                # Some projectors (like serverclass) may return None for certain stanzas
                if projection is not None:
                    projected_rows.append(projection)
            except Exception as e:
                logger.warning(
                    f"Failed to project {conf_type} stanza '{stanza.name}': {e}",
                    extra={"run_id": run_id, "conf_type": conf_type},
                )
                # Continue with other stanzas

        # Bulk insert using SQLAlchemy Core
        if projected_rows:
            try:
                if conf_type == "inputs":
                    stmt = insert(Input).values(projected_rows)
                    db.execute(stmt)
                    counts["inputs"] = len(projected_rows)
                elif conf_type == "props":
                    stmt = insert(Props).values(projected_rows)
                    db.execute(stmt)
                    counts["props"] = len(projected_rows)
                elif conf_type == "transforms":
                    stmt = insert(Transform).values(projected_rows)
                    db.execute(stmt)
                    counts["transforms"] = len(projected_rows)
                elif conf_type == "indexes":
                    stmt = insert(Index).values(projected_rows)
                    db.execute(stmt)
                    counts["indexes"] = len(projected_rows)
                elif conf_type == "outputs":
                    stmt = insert(Output).values(projected_rows)
                    db.execute(stmt)
                    counts["outputs"] = len(projected_rows)
                elif conf_type == "serverclasses":
                    stmt = insert(Serverclass).values(projected_rows)
                    db.execute(stmt)
                    counts["serverclasses"] = len(projected_rows)

                logger.info(
                    f"Bulk inserted {len(projected_rows)} {conf_type} records",
                    extra={"run_id": run_id, "conf_type": conf_type},
                )

            except Exception as e:
                logger.error(
                    f"Failed to bulk insert {conf_type} projections: {e}",
                    extra={"run_id": run_id, "conf_type": conf_type},
                    exc_info=True,
                )
                raise

    return counts

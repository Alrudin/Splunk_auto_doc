"""Upload ingestion endpoint for handling file uploads."""

import hashlib
import io
import logging
from typing import Annotated, BinaryIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models.file import File as FileModel
from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
from app.schemas.ingestion_run import IngestionRunResponse
from app.storage import StorageBackend, StorageError, get_storage_backend

logger = logging.getLogger(__name__)

router = APIRouter()

# Chunk size for streaming uploads (8KB is optimal for most scenarios)
UPLOAD_CHUNK_SIZE = 8192


class StreamingHashWrapper(io.BufferedIOBase):
    """Wrapper that computes SHA256 hash while streaming data
    This wrapper allows us to:
    1. Stream file data without loading it all into memory
    2. Compute SHA256 hash incrementally as data passes through
    3. Count total bytes processed

    Memory-safe for files of any size.
    """

    def __init__(self, source: BinaryIO):
        """Initialize the streaming hash wrapper.

        Args:
            source: Source file-like object to read from
        """
        self.source = source
        self.hasher = hashlib.sha256()
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        """Read data from source, update hash, and return data.

        Args:
            size: Number of bytes to read (-1 for all remaining)

        Returns:
            bytes: Data read from source
        """
        chunk = self.source.read(size)
        if chunk:
            self.hasher.update(chunk)
            self.bytes_read += len(chunk)
        return chunk

    def readable(self) -> bool:
        """Indicate this stream is readable."""
        return True

    def get_hash(self) -> str:
        """Get the computed SHA256 hash.

        Returns:
            str: Hexadecimal SHA256 hash
        """
        return self.hasher.hexdigest()

    def get_size(self) -> int:
        """Get total bytes read.

        Returns:
            int: Total bytes read from source
        """
        return self.bytes_read


def get_storage() -> StorageBackend:
    """Dependency to get storage backend instance.

    Returns:
        StorageBackend: Configured storage backend instance
    """
    settings = get_settings()
    return get_storage_backend(
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


@router.post(
    "/uploads", response_model=IngestionRunResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    request: Request,
    file: Annotated[
        UploadFile, File(description="Configuration archive file (tar.gz or zip)")
    ],
    type: Annotated[IngestionType, Form(description="Type of configuration upload")],
    label: Annotated[
        str | None, Form(description="Optional human-readable label")
    ] = None,
    notes: Annotated[
        str | None, Form(description="Optional notes about this upload")
    ] = None,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> IngestionRunResponse:
    """Handle file upload and create ingestion run.

    This endpoint uses streaming to handle files of any size safely:
    1. Creates an ingestion run record with status=pending
    2. Streams the uploaded file in chunks (no full memory buffering)
    3. Computes SHA256 hash incrementally during streaming
    4. Stores the file using the storage backend (chunked writes)
    5. Persists file metadata to the database
    6. Updates run status to stored
    7. Returns the run details

    Memory-safe design:
    - Files are streamed in 8KB chunks, not loaded fully into memory
    - SHA256 hash computed incrementally as chunks are processed
    - Storage backends use efficient chunked writes (shutil.copyfileobj)
    - Handles files >1GB without memory exhaustion

    Args:
        file: Uploaded file (multipart)
        type: Type of ingestion (ds_etc, instance_etc, app_bundle, single_conf)
        label: Optional human-readable label
        notes: Optional notes
        db: Database session
        storage: Storage backend

    Returns:
        IngestionRunResponse: Created ingestion run details

    Raises:
        HTTPException: If upload or storage fails
    """
    logger.info(
        "Received upload request",
        extra={
            "upload_filename": file.filename,
            "type": type.value,
            "label": label,
        },
    )

    # Validate file was provided
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    # Create ingestion run with pending status
    run = IngestionRun(
        type=type,
        label=label,
        notes=notes,
        status=IngestionStatus.PENDING,
    )
    db.add(run)
    db.flush()  # Get the run ID without committing

    # Store run_id in request state for middleware logging
    request.state.run_id = run.id

    logger.info("Created ingestion run with status=pending", extra={"run_id": run.id})

    try:
        # Wrap the upload file for streaming with hash computation
        # This approach streams the file in chunks, computing hash as we go
        # Memory-safe for files of any size (no full file buffering)
        storage_key = f"runs/{run.id}/{file.filename}"

        # Create streaming wrapper that computes hash during upload
        stream_wrapper = StreamingHashWrapper(file.file)

        # Store file using storage backend (streams data, no full buffering)
        stored_key = storage.store_blob(stream_wrapper, storage_key)

        # Get hash and size after streaming is complete
        sha256_hash = stream_wrapper.get_hash()
        file_size = stream_wrapper.get_size()

        logger.info(
            "File processed",
            extra={
                "run_id": run.id,
                "upload_filename": file.filename,
                "size_bytes": file_size,
                "sha256": sha256_hash,
            },
        )

        logger.info(
            "Stored file in storage backend",
            extra={"run_id": run.id, "storage_key": stored_key},
        )

        # Create file record
        file_record = FileModel(
            run_id=run.id,
            path=file.filename,
            sha256=sha256_hash,
            size_bytes=file_size,
            stored_object_key=stored_key,
        )
        db.add(file_record)

        # Update run status to stored
        run.status = IngestionStatus.STORED

        # Commit transaction
        db.commit()
        db.refresh(run)

        logger.info(
            "Successfully completed upload for run",
            extra={"run_id": run.id, "status": "stored"},
        )

        return IngestionRunResponse.model_validate(run)

    except StorageError as e:
        logger.error(
            "Storage error during upload",
            extra={"run_id": run.id, "error": str(e)},
            exc_info=True,
        )
        db.rollback()

        # Update run status to failed
        run.status = IngestionStatus.FAILED
        run.notes = (
            f"Storage error: {str(e)}"
            if not run.notes
            else f"{run.notes}\nStorage error: {str(e)}"
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error during upload",
            extra={"run_id": run.id, "error": str(e)},
            exc_info=True,
        )

        db.rollback()

        # Update run status to failed
        run.status = IngestionStatus.FAILED
        run.notes = (
            f"Upload error: {str(e)}"
            if not run.notes
            else f"{run.notes}\nUpload error: {str(e)}"
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}",
        ) from e

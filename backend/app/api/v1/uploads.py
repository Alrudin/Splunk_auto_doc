"""Upload ingestion endpoint for handling file uploads."""

import hashlib
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models.file import File as FileModel
from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
from app.schemas.ingestion_run import IngestionRunResponse
from app.storage import StorageBackend, StorageError, get_storage_backend

logger = logging.getLogger(__name__)

router = APIRouter()


def get_storage() -> StorageBackend:
    """Dependency to get storage backend instance.
    
    Returns:
        StorageBackend: Configured storage backend instance
    """
    settings = get_settings()
    return get_storage_backend(
        backend_type=settings.storage_backend,
        storage_path=settings.storage_path if settings.storage_backend == "local" else None,
        s3_bucket=settings.s3_bucket if settings.storage_backend == "s3" else None,
        s3_endpoint_url=settings.s3_endpoint_url if settings.storage_backend == "s3" else None,
        aws_access_key_id=settings.aws_access_key_id if settings.storage_backend == "s3" else None,
        aws_secret_access_key=settings.aws_secret_access_key if settings.storage_backend == "s3" else None,
    )


@router.post("/uploads", response_model=IngestionRunResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: Annotated[UploadFile, File(description="Configuration archive file (tar.gz or zip)")],
    type: Annotated[IngestionType, Form(description="Type of configuration upload")],
    label: Annotated[str | None, Form(description="Optional human-readable label")] = None,
    notes: Annotated[str | None, Form(description="Optional notes about this upload")] = None,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> IngestionRunResponse:
    """Handle file upload and create ingestion run.
    
    This endpoint:
    1. Creates an ingestion run record with status=pending
    2. Computes SHA256 hash of the uploaded file
    3. Stores the file using the storage backend
    4. Persists file metadata to the database
    5. Updates run status to stored
    6. Returns the run details
    
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
    logger.info(f"Received upload request: file={file.filename}, type={type.value}, label={label}")
    
    # Validate file was provided
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
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
    
    logger.info(f"Created ingestion run {run.id} with status=pending")
    
    try:
        # Read file content and compute hash
        file_content = await file.read()
        file_size = len(file_content)
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        
        logger.info(f"File {file.filename}: size={file_size} bytes, sha256={sha256_hash}")
        
        # Reset file pointer and store blob
        await file.seek(0)
        storage_key = f"runs/{run.id}/{file.filename}"
        
        # Store file using storage backend
        # We need to wrap the UploadFile in a way that storage backend can handle
        import io
        file_obj = io.BytesIO(file_content)
        stored_key = storage.store_blob(file_obj, storage_key)
        
        logger.info(f"Stored file with key: {stored_key}")
        
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
        
        logger.info(f"Successfully completed upload for run {run.id}, status=stored")
        
        return IngestionRunResponse.model_validate(run)
        
    except StorageError as e:
        logger.error(f"Storage error for run {run.id}: {e}")
        db.rollback()
        
        # Update run status to failed
        run.status = IngestionStatus.FAILED
        run.notes = f"Storage error: {str(e)}" if not run.notes else f"{run.notes}\nStorage error: {str(e)}"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload for run {run.id}: {e}", exc_info=True)
        db.rollback()
        
        # Update run status to failed
        run.status = IngestionStatus.FAILED
        run.notes = f"Upload error: {str(e)}" if not run.notes else f"{run.notes}\nUpload error: {str(e)}"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )

"""Storage abstraction package for blob storage operations."""

from app.storage.base import StorageBackend, StorageError
from app.storage.local import LocalStorageBackend
from app.storage.s3 import S3StorageBackend


def get_storage_backend(
    backend_type: str,
    storage_path: str | None = None,
    s3_bucket: str | None = None,
    s3_endpoint_url: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> StorageBackend:
    """Factory function to create storage backend instances.

    Args:
        backend_type: Type of storage backend ("local" or "s3")
        storage_path: Base path for local storage (required if backend_type="local")
        s3_bucket: S3 bucket name (required if backend_type="s3")
        s3_endpoint_url: S3 endpoint URL for MinIO (optional)
        aws_access_key_id: AWS access key ID (optional, uses env if None)
        aws_secret_access_key: AWS secret access key (optional, uses env if None)

    Returns:
        StorageBackend: Configured storage backend instance

    Raises:
        ValueError: If backend_type is invalid or required parameters are missing
        StorageError: If backend initialization fails
    """
    if backend_type == "local":
        if not storage_path:
            raise ValueError("storage_path is required for local backend")
        return LocalStorageBackend(base_path=storage_path)

    elif backend_type == "s3":
        if not s3_bucket:
            raise ValueError("s3_bucket is required for s3 backend")
        return S3StorageBackend(
            bucket=s3_bucket,
            endpoint_url=s3_endpoint_url,
            access_key_id=aws_access_key_id,
            secret_access_key=aws_secret_access_key,
        )

    else:
        raise ValueError(f"Unsupported storage backend type: {backend_type}")


__all__ = [
    "StorageBackend",
    "StorageError",
    "LocalStorageBackend",
    "S3StorageBackend",
    "get_storage_backend",
]

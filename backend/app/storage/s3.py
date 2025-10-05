"""S3-compatible storage backend implementation (MinIO)."""

import io
from typing import Any, BinaryIO

try:
    import boto3  # type: ignore[import-untyped]
    from botocore.client import Config  # type: ignore[import-untyped]
    from botocore.exceptions import (  # type: ignore[import-untyped]
        BotoCoreError,
        ClientError,
    )
except ImportError:
    boto3 = None  # type: ignore[assignment]
    Config = None  # type: ignore[assignment, misc]
    BotoCoreError = Exception
    ClientError = Exception

from app.storage.base import StorageBackend, StorageError


class S3StorageBackend(StorageBackend):
    """S3-compatible storage implementation.

    Works with AWS S3 and MinIO. Supports streaming uploads and downloads.
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        """Initialize S3 storage backend.

        Args:
            bucket: S3 bucket name
            endpoint_url: S3 endpoint URL (for MinIO), None for AWS S3
            access_key_id: AWS access key ID (uses env if None)
            secret_access_key: AWS secret access key (uses env if None)

        Raises:
            StorageError: If initialization fails or bucket is inaccessible
        """
        self.bucket = bucket

        try:
            # Configure S3 client with signature version for MinIO compatibility
            config = Config(signature_version="s3v4")

            # Create S3 client
            client_kwargs: dict[str, Any] = {"config": config}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url
            if access_key_id:
                client_kwargs["aws_access_key_id"] = access_key_id
            if secret_access_key:
                client_kwargs["aws_secret_access_key"] = secret_access_key

            self.s3_client = boto3.client("s3", **client_kwargs)

            # Verify bucket exists/is accessible
            self.s3_client.head_bucket(Bucket=bucket)

        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"Failed to initialize S3 backend: {e}") from e

    def store_blob(self, file: BinaryIO, key: str) -> str:
        """Store a blob in S3.

        Args:
            file: Binary file object to store
            key: Object key in the bucket

        Returns:
            str: Storage key (same as input key)

        Raises:
            StorageError: If storage operation fails
        """
        try:
            self.s3_client.upload_fileobj(file, self.bucket, key)
            return key
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"Failed to store blob '{key}': {e}") from e

    def retrieve_blob(self, key: str) -> BinaryIO:
        """Retrieve a blob from S3.

        Args:
            key: Object key in the bucket

        Returns:
            BinaryIO: BytesIO object containing the blob data

        Raises:
            StorageError: If retrieval fails or key doesn't exist
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            # Read entire object into BytesIO for compatibility
            data = response["Body"].read()
            return io.BytesIO(data)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise StorageError(f"Blob '{key}' does not exist") from e
            raise StorageError(f"Failed to retrieve blob '{key}': {e}") from e
        except BotoCoreError as e:
            raise StorageError(f"Failed to retrieve blob '{key}': {e}") from e

    def delete_blob(self, key: str) -> None:
        """Delete a blob from S3.

        Args:
            key: Object key in the bucket

        Raises:
            StorageError: If deletion fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"Failed to delete blob '{key}': {e}") from e

    def exists(self, key: str) -> bool:
        """Check if a blob exists in S3.

        Args:
            key: Object key in the bucket

        Returns:
            bool: True if blob exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            # Other errors should propagate
            raise StorageError(f"Failed to check blob existence '{key}': {e}") from e
        except BotoCoreError as e:
            raise StorageError(f"Failed to check blob existence '{key}': {e}") from e

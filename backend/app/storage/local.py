"""Local filesystem storage backend implementation."""

import shutil
from pathlib import Path
from typing import BinaryIO

from app.storage.base import StorageBackend, StorageError


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation.

    Stores blobs in a local directory structure. Thread-safe for file operations.
    """

    def __init__(self, base_path: str) -> None:
        """Initialize local storage backend.

        Args:
            base_path: Root directory for storing blobs

        Raises:
            StorageError: If base_path cannot be created or accessed
        """
        self.base_path = Path(base_path).resolve()
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Failed to create storage directory: {e}") from e

    def store_blob(self, file: BinaryIO, key: str) -> str:
        """Store a blob in the local filesystem.

        Args:
            file: Binary file object to store
            key: Relative path for the blob (will be sanitized)

        Returns:
            str: Storage key (relative path from base_path)

        Raises:
            StorageError: If storage operation fails
        """
        # Sanitize key to prevent directory traversal
        safe_key = self._sanitize_key(key)
        target_path = self.base_path / safe_key

        try:
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            with open(target_path, "wb") as f:
                shutil.copyfileobj(file, f)

            return safe_key
        except OSError as e:
            raise StorageError(f"Failed to store blob '{key}': {e}") from e

    def retrieve_blob(self, key: str) -> BinaryIO:
        """Retrieve a blob from the local filesystem.

        Args:
            key: Storage key (relative path)

        Returns:
            BinaryIO: Open file handle (caller must close)

        Raises:
            StorageError: If retrieval fails or key doesn't exist
        """
        safe_key = self._sanitize_key(key)
        target_path = self.base_path / safe_key

        if not target_path.exists():
            raise StorageError(f"Blob '{key}' does not exist")

        if not target_path.is_file():
            raise StorageError(f"Blob '{key}' is not a file")

        try:
            return open(target_path, "rb")
        except OSError as e:
            raise StorageError(f"Failed to retrieve blob '{key}': {e}") from e

    def delete_blob(self, key: str) -> None:
        """Delete a blob from the local filesystem.

        Args:
            key: Storage key (relative path)

        Raises:
            StorageError: If deletion fails
        """
        safe_key = self._sanitize_key(key)
        target_path = self.base_path / safe_key

        if not target_path.exists():
            # Idempotent: deleting non-existent blob is not an error
            return

        try:
            target_path.unlink()
        except OSError as e:
            raise StorageError(f"Failed to delete blob '{key}': {e}") from e

    def exists(self, key: str) -> bool:
        """Check if a blob exists in the local filesystem.

        Args:
            key: Storage key (relative path)

        Returns:
            bool: True if blob exists, False otherwise
        """
        safe_key = self._sanitize_key(key)
        target_path = self.base_path / safe_key
        return target_path.exists() and target_path.is_file()

    def _sanitize_key(self, key: str) -> str:
        """Sanitize a storage key to prevent directory traversal.

        Args:
            key: Raw storage key

        Returns:
            str: Sanitized key safe for filesystem operations

        Raises:
            StorageError: If key is invalid or attempts traversal
        """
        # Remove leading slashes
        clean_key = key.lstrip("/")

        # Empty key after stripping is invalid
        if not clean_key:
            raise StorageError(f"Invalid storage key: '{key}' is empty")

        # Check for directory traversal attempts
        if ".." in Path(clean_key).parts:
            raise StorageError(f"Invalid storage key: '{key}' contains '..'")

        return clean_key

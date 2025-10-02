"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Abstract interface for blob storage operations.

    Defines the contract that all storage implementations must follow.
    Implementations should handle local filesystem or S3-compatible storage.
    """

    @abstractmethod
    def store_blob(self, file: BinaryIO, key: str) -> str:
        """Store a blob and return a retrievable key.

        Args:
            file: Binary file object to store
            key: Suggested key/path for the blob (implementation may modify)

        Returns:
            str: Storage key that can be used to retrieve the blob

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def retrieve_blob(self, key: str) -> BinaryIO:
        """Retrieve a blob by its storage key.

        Args:
            key: Storage key returned by store_blob()

        Returns:
            BinaryIO: File-like object containing the blob data

        Raises:
            StorageError: If retrieval fails or key doesn't exist
        """
        pass

    @abstractmethod
    def delete_blob(self, key: str) -> None:
        """Delete a blob by its storage key.

        Args:
            key: Storage key returned by store_blob()

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a blob exists.

        Args:
            key: Storage key to check

        Returns:
            bool: True if blob exists, False otherwise
        """
        pass


class StorageError(Exception):
    """Exception raised for storage operation failures."""

    pass

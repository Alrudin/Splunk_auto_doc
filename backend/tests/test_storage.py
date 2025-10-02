"""Tests for storage backend implementations."""

import io
import os
import tempfile

import pytest
from app.storage import (
    LocalStorageBackend,
    S3StorageBackend,
    StorageError,
    get_storage_backend,
)


class TestLocalStorageBackend:
    """Tests for LocalStorageBackend."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def local_backend(self, temp_storage_dir):
        """Create a LocalStorageBackend instance."""
        return LocalStorageBackend(base_path=temp_storage_dir)

    def test_init_creates_directory(self, temp_storage_dir):
        """Test that initialization creates the base directory."""
        storage_path = os.path.join(temp_storage_dir, "new_storage")
        LocalStorageBackend(base_path=storage_path)

        assert os.path.exists(storage_path)
        assert os.path.isdir(storage_path)

    def test_store_blob_basic(self, local_backend):
        """Test storing a basic blob."""
        content = b"Hello, World!"
        file_obj = io.BytesIO(content)
        key = "test_file.txt"

        stored_key = local_backend.store_blob(file_obj, key)

        assert stored_key == key
        assert local_backend.exists(key)

    def test_store_blob_with_subdirectory(self, local_backend):
        """Test storing a blob in a subdirectory."""
        content = b"Hello, World!"
        file_obj = io.BytesIO(content)
        key = "subdir/nested/test_file.txt"

        stored_key = local_backend.store_blob(file_obj, key)

        assert stored_key == key
        assert local_backend.exists(key)

    def test_store_blob_prevents_traversal(self, local_backend):
        """Test that directory traversal attempts are blocked."""
        content = b"Malicious content"
        file_obj = io.BytesIO(content)
        key = "../../../etc/passwd"

        with pytest.raises(StorageError, match="contains '..'"):
            local_backend.store_blob(file_obj, key)

    def test_retrieve_blob_basic(self, local_backend):
        """Test retrieving a stored blob."""
        content = b"Test content for retrieval"
        file_obj = io.BytesIO(content)
        key = "retrieve_test.txt"

        local_backend.store_blob(file_obj, key)
        retrieved = local_backend.retrieve_blob(key)

        assert retrieved.read() == content
        retrieved.close()

    def test_retrieve_blob_nonexistent(self, local_backend):
        """Test retrieving a non-existent blob raises error."""
        with pytest.raises(StorageError, match="does not exist"):
            local_backend.retrieve_blob("nonexistent.txt")

    def test_delete_blob_basic(self, local_backend):
        """Test deleting a blob."""
        content = b"To be deleted"
        file_obj = io.BytesIO(content)
        key = "delete_test.txt"

        local_backend.store_blob(file_obj, key)
        assert local_backend.exists(key)

        local_backend.delete_blob(key)
        assert not local_backend.exists(key)

    def test_delete_blob_idempotent(self, local_backend):
        """Test that deleting non-existent blob doesn't raise error."""
        # Should not raise an exception
        local_backend.delete_blob("nonexistent.txt")

    def test_exists_returns_false_for_nonexistent(self, local_backend):
        """Test exists() returns False for non-existent blob."""
        assert not local_backend.exists("nonexistent.txt")

    def test_exists_returns_true_for_existing(self, local_backend):
        """Test exists() returns True for existing blob."""
        content = b"Exists test"
        file_obj = io.BytesIO(content)
        key = "exists_test.txt"

        local_backend.store_blob(file_obj, key)
        assert local_backend.exists(key)

    def test_sanitize_key_removes_leading_slash(self, local_backend):
        """Test that leading slashes are removed from keys."""
        content = b"Content"
        file_obj = io.BytesIO(content)
        key = "/leading/slash/file.txt"

        stored_key = local_backend.store_blob(file_obj, key)
        assert stored_key == "leading/slash/file.txt"
        assert local_backend.exists("leading/slash/file.txt")


class TestS3StorageBackend:
    """Tests for S3StorageBackend.

    Note: These tests require a running MinIO instance or will be skipped.
    """

    @pytest.fixture
    def s3_backend(self):
        """Create an S3StorageBackend instance if MinIO is available."""
        # Try to create S3 backend with test credentials
        # This will be skipped if MinIO is not running
        try:
            backend = S3StorageBackend(
                bucket="test-bucket",
                endpoint_url="http://localhost:9000",
                access_key_id="minioadmin",
                secret_access_key="minioadmin",
            )
            yield backend
        except StorageError:
            pytest.skip("MinIO not available for S3 tests")

    def test_s3_backend_requires_bucket(self):
        """Test that S3 backend requires a bucket name."""
        with pytest.raises(TypeError):
            S3StorageBackend()  # type: ignore

    def test_store_and_retrieve_blob(self, s3_backend):
        """Test storing and retrieving a blob in S3."""
        content = b"S3 test content"
        file_obj = io.BytesIO(content)
        key = "test/s3_file.txt"

        stored_key = s3_backend.store_blob(file_obj, key)
        assert stored_key == key

        retrieved = s3_backend.retrieve_blob(key)
        assert retrieved.read() == content
        retrieved.close()

        # Cleanup
        s3_backend.delete_blob(key)

    def test_delete_blob_s3(self, s3_backend):
        """Test deleting a blob from S3."""
        content = b"To be deleted from S3"
        file_obj = io.BytesIO(content)
        key = "test/delete_s3.txt"

        s3_backend.store_blob(file_obj, key)
        assert s3_backend.exists(key)

        s3_backend.delete_blob(key)
        assert not s3_backend.exists(key)

    def test_exists_s3(self, s3_backend):
        """Test exists() for S3 backend."""
        content = b"S3 exists test"
        file_obj = io.BytesIO(content)
        key = "test/exists_s3.txt"

        assert not s3_backend.exists(key)

        s3_backend.store_blob(file_obj, key)
        assert s3_backend.exists(key)

        # Cleanup
        s3_backend.delete_blob(key)


class TestStorageFactory:
    """Tests for storage factory function."""

    def test_get_local_backend(self):
        """Test getting a local storage backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = get_storage_backend(
                backend_type="local",
                storage_path=tmpdir,
            )
            assert isinstance(backend, LocalStorageBackend)

    def test_get_local_backend_requires_path(self):
        """Test that local backend requires storage_path."""
        with pytest.raises(ValueError, match="storage_path is required"):
            get_storage_backend(backend_type="local")

    def test_get_s3_backend(self):
        """Test getting an S3 storage backend."""
        try:
            backend = get_storage_backend(
                backend_type="s3",
                s3_bucket="test-bucket",
                s3_endpoint_url="http://localhost:9000",
                aws_access_key_id="minioadmin",
                aws_secret_access_key="minioadmin",
            )
            assert isinstance(backend, S3StorageBackend)
        except StorageError:
            pytest.skip("MinIO not available for S3 factory test")

    def test_get_s3_backend_requires_bucket(self):
        """Test that S3 backend requires s3_bucket."""
        with pytest.raises(ValueError, match="s3_bucket is required"):
            get_storage_backend(backend_type="s3")

    def test_invalid_backend_type(self):
        """Test that invalid backend type raises error."""
        with pytest.raises(ValueError, match="Unsupported storage backend"):
            get_storage_backend(backend_type="invalid")


class TestStorageIntegration:
    """Integration tests for storage operations."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def local_backend(self, temp_storage_dir):
        """Create a LocalStorageBackend instance."""
        return LocalStorageBackend(base_path=temp_storage_dir)

    def test_store_multiple_files(self, local_backend):
        """Test storing multiple files."""
        files = {
            "file1.txt": b"Content 1",
            "file2.txt": b"Content 2",
            "dir/file3.txt": b"Content 3",
        }

        for key, content in files.items():
            file_obj = io.BytesIO(content)
            stored_key = local_backend.store_blob(file_obj, key)
            assert stored_key == key

        for key in files:
            assert local_backend.exists(key)

    def test_overwrite_existing_file(self, local_backend):
        """Test that storing to an existing key overwrites the file."""
        key = "overwrite_test.txt"
        content1 = b"Original content"
        content2 = b"New content"

        # Store first version
        local_backend.store_blob(io.BytesIO(content1), key)
        retrieved1 = local_backend.retrieve_blob(key)
        assert retrieved1.read() == content1
        retrieved1.close()

        # Overwrite with second version
        local_backend.store_blob(io.BytesIO(content2), key)
        retrieved2 = local_backend.retrieve_blob(key)
        assert retrieved2.read() == content2
        retrieved2.close()

    def test_large_file_handling(self, local_backend):
        """Test handling of larger files."""
        # Create a 1MB file
        size_mb = 1
        content = b"x" * (size_mb * 1024 * 1024)
        file_obj = io.BytesIO(content)
        key = "large_file.bin"

        stored_key = local_backend.store_blob(file_obj, key)
        assert stored_key == key

        retrieved = local_backend.retrieve_blob(key)
        retrieved_content = retrieved.read()
        retrieved.close()

        assert len(retrieved_content) == len(content)
        assert retrieved_content == content

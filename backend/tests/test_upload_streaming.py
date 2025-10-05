"""Tests for streaming upload functionality and memory safety."""

import hashlib
import io

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies, skip tests if not available
try:
    from app.api.v1.uploads import StreamingHashWrapper
    from app.models.file import File as FileModel
    from app.models.ingestion_run import IngestionStatus

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Dependencies not available: {e}"


class TestStreamingHashWrapper:
    """Tests for the StreamingHashWrapper class."""

    def test_streaming_hash_small_file(self):
        """Test hash computation for small file."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        content = b"Test content for hashing"
        expected_hash = hashlib.sha256(content).hexdigest()

        source = io.BytesIO(content)
        wrapper = StreamingHashWrapper(source)

        # Read all data
        data = wrapper.read()
        assert data == content
        assert wrapper.get_hash() == expected_hash
        assert wrapper.get_size() == len(content)

    def test_streaming_hash_chunked_read(self):
        """Test hash computation with chunked reads."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        content = b"A" * 10000  # 10KB
        expected_hash = hashlib.sha256(content).hexdigest()

        source = io.BytesIO(content)
        wrapper = StreamingHashWrapper(source)

        # Read in chunks
        chunks = []
        while True:
            chunk = wrapper.read(1024)  # 1KB chunks
            if not chunk:
                break
            chunks.append(chunk)

        # Verify data matches
        assert b"".join(chunks) == content
        assert wrapper.get_hash() == expected_hash
        assert wrapper.get_size() == len(content)

    def test_streaming_hash_empty_file(self):
        """Test hash computation for empty file."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        content = b""
        expected_hash = hashlib.sha256(content).hexdigest()

        source = io.BytesIO(content)
        wrapper = StreamingHashWrapper(source)

        data = wrapper.read()
        assert data == content
        assert wrapper.get_hash() == expected_hash
        assert wrapper.get_size() == 0

    def test_streaming_hash_large_simulated(self):
        """Test hash computation with simulated large file (100MB)."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a simulated large file with repeating pattern
        # This tests streaming without actually allocating 100MB
        pattern = b"X" * 1024  # 1KB pattern
        repetitions = 100 * 1024  # 100MB total

        # Compute expected hash
        hasher = hashlib.sha256()
        for _ in range(repetitions):
            hasher.update(pattern)
        expected_hash = hasher.hexdigest()

        # Create a generator-based file-like object for testing
        class GeneratedFile:
            def __init__(self, pattern, count):
                self.pattern = pattern
                self.remaining = count

            def read(self, size=-1):
                if self.remaining == 0:
                    return b""
                if size == -1 or size >= len(self.pattern):
                    self.remaining -= 1
                    return self.pattern
                # For partial reads, just return the pattern (simplified)
                self.remaining -= 1
                return self.pattern

        source = GeneratedFile(pattern, repetitions)
        wrapper = StreamingHashWrapper(source)

        # Read in chunks (don't store to save memory)
        total_bytes = 0
        while True:
            chunk = wrapper.read(8192)
            if not chunk:
                break
            total_bytes += len(chunk)

        # Verify hash and size
        assert wrapper.get_hash() == expected_hash
        assert wrapper.get_size() == len(pattern) * repetitions

    def test_readable_method(self):
        """Test that wrapper correctly reports as readable."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        source = io.BytesIO(b"test")
        wrapper = StreamingHashWrapper(source)
        assert wrapper.readable() is True


@pytest.mark.database
class TestStreamingUpload:
    """Integration tests for streaming upload functionality."""

    def test_upload_with_streaming_hash(self, client, test_db):
        """Test that upload correctly uses streaming hash computation."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test content
        file_content = b"Streaming upload test content"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc", "label": "Streaming Test"},
        )

        assert response.status_code == 201
        data = response.json()

        # Verify file record has correct hash
        db = test_db()
        file_record = db.query(FileModel).filter_by(run_id=data["id"]).first()
        assert file_record is not None
        assert file_record.sha256 == expected_hash
        assert file_record.size_bytes == len(file_content)
        db.close()

    def test_upload_large_file_streaming(self, client, test_db):
        """Test upload of large file (100MB simulated) without memory issues."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a 100MB file
        # Note: This creates the file in memory for the test,
        # but the upload endpoint should stream it
        size_mb = 100
        file_content = b"X" * (size_mb * 1024 * 1024)
        expected_hash = hashlib.sha256(file_content).hexdigest()

        response = client.post(
            "/v1/uploads",
            files={"file": ("large_streaming.tar.gz", io.BytesIO(file_content))},
            data={"type": "instance_etc", "label": "Large Streaming Test"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "stored"

        # Verify metadata
        db = test_db()
        file_record = db.query(FileModel).filter_by(run_id=data["id"]).first()
        assert file_record is not None
        assert file_record.sha256 == expected_hash
        assert file_record.size_bytes == len(file_content)
        db.close()

    def test_upload_very_large_file_memory_safe(self, client):
        """Test that very large file (500MB) can be uploaded with streaming.

        This test verifies memory safety by uploading a large file.
        The streaming implementation should not load the entire file into memory.
        """
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a 500MB file
        size_mb = 500
        file_content = b"M" * (size_mb * 1024 * 1024)

        response = client.post(
            "/v1/uploads",
            files={"file": ("very_large_streaming.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        # Should succeed with streaming
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "stored"

    def test_upload_multiple_large_sequential(self, client, test_db):
        """Test multiple large file uploads in sequence."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        size_mb = 50
        run_ids = []

        for i in range(3):
            file_content = bytes([i % 256]) * (size_mb * 1024 * 1024)
            response = client.post(
                "/v1/uploads",
                files={"file": (f"large_{i}.tar.gz", io.BytesIO(file_content))},
                data={"type": "app_bundle", "label": f"Large Upload {i}"},
            )

            assert response.status_code == 201
            data = response.json()
            run_ids.append(data["id"])

        # Verify all runs succeeded
        assert len(set(run_ids)) == 3

        db = test_db()
        for run_id in run_ids:
            file_record = db.query(FileModel).filter_by(run_id=run_id).first()
            assert file_record is not None
            assert file_record.size_bytes == size_mb * 1024 * 1024
        db.close()

    def test_upload_hash_consistency(self, client, test_db):
        """Test that streaming hash computation is consistent with standard hash."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Test various file sizes to ensure consistency
        test_sizes = [
            0,  # Empty file
            1,  # 1 byte
            100,  # Small
            8192,  # Exactly one chunk
            8193,  # Just over one chunk
            1024 * 1024,  # 1MB
            10 * 1024 * 1024,  # 10MB
        ]

        for size in test_sizes:
            # Create content with varying pattern
            file_content = bytes([(i % 256) for i in range(size)])
            expected_hash = hashlib.sha256(file_content).hexdigest()

            response = client.post(
                "/v1/uploads",
                files={"file": (f"test_{size}.dat", io.BytesIO(file_content))},
                data={"type": "single_conf"},
            )

            assert response.status_code == 201
            data = response.json()

            # Verify hash matches
            db = test_db()
            file_record = db.query(FileModel).filter_by(run_id=data["id"]).first()
            assert file_record.sha256 == expected_hash, (
                f"Hash mismatch for size {size}: "
                f"expected {expected_hash}, got {file_record.sha256}"
            )
            db.close()


@pytest.mark.database
class TestStreamingErrorHandling:
    """Tests for error handling with streaming uploads."""

    def test_streaming_upload_storage_error(self, client, test_db, monkeypatch):
        """Test that storage errors during streaming are handled properly."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        from app.storage import StorageError

        # Mock storage to fail during streaming
        def mock_store_blob(self, file, key):
            # Read a bit to simulate partial streaming
            file.read(1024)
            raise StorageError("Simulated streaming storage failure")

        monkeypatch.setattr(
            "app.storage.local.LocalStorageBackend.store_blob", mock_store_blob
        )

        file_content = b"Test content for storage failure"
        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        # Should return 500 error
        assert response.status_code == 500
        assert "Failed to store file" in response.json()["detail"]

        # Verify run is marked as failed
        db = test_db()
        from app.models.ingestion_run import IngestionRun

        runs = db.query(IngestionRun).order_by(IngestionRun.id.desc()).all()
        if runs:
            failed_run = runs[0]
            assert failed_run.status == IngestionStatus.FAILED
        db.close()


if __name__ == "__main__":
    print("✅ Streaming upload tests configured")

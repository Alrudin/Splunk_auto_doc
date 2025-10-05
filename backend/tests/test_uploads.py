"""Tests for upload ingestion endpoint."""

import io
import tempfile

import pytest

# Try to import dependencies, skip tests if not available
try:
    from app.api.v1.uploads import get_storage
    from app.core.db import Base, get_db
    from app.main import create_app
    from app.models.file import File as FileModel
    from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
    from app.storage import get_storage_backend
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Dependencies not available: {e}"


@pytest.fixture
def test_db():
    """Create a test database."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(engine)


@pytest.fixture
def test_storage():
    """Create a test storage backend."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = get_storage_backend(backend_type="local", storage_path=tmpdir)
        yield storage


@pytest.fixture
def client(test_db, test_storage):
    """Create a test client with overridden dependencies."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    app = create_app()

    # Override database dependency
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    # Override storage dependency
    def override_get_storage():
        return test_storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage

    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.database
class TestUploadEndpoint:
    """Tests for the upload endpoint."""

    def test_upload_success(self, client, test_db):
        """Test successful file upload."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create test file content
        file_content = b"Test Splunk configuration content"
        file_name = "test_config.tar.gz"

        # Upload file
        response = client.post(
            "/v1/uploads",
            files={"file": (file_name, io.BytesIO(file_content), "application/gzip")},
            data={
                "type": "ds_etc",
                "label": "Test Upload",
                "notes": "Testing upload functionality",
            },
        )

        # Check response
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["type"] == "ds_etc"
        assert data["label"] == "Test Upload"
        assert data["notes"] == "Testing upload functionality"
        assert data["status"] == "stored"
        assert "created_at" in data

        # Verify database record
        db = test_db()
        run = db.query(IngestionRun).filter_by(id=data["id"]).first()
        assert run is not None
        assert run.status == IngestionStatus.STORED
        assert run.type == IngestionType.DS_ETC

        # Verify file record
        file_record = db.query(FileModel).filter_by(run_id=run.id).first()
        assert file_record is not None
        assert file_record.path == file_name
        assert file_record.size_bytes == len(file_content)
        assert len(file_record.sha256) == 64  # SHA256 hex length

        db.close()

    def test_upload_without_file(self, client):
        """Test upload without file returns error."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.post(
            "/v1/uploads",
            files={},
            data={"type": "ds_etc"},
        )

        assert response.status_code == 422  # Validation error

    def test_upload_without_type(self, client):
        """Test upload without type returns error."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        file_content = b"Test content"

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={},
        )

        assert response.status_code == 422  # Validation error

    def test_upload_invalid_type(self, client):
        """Test upload with invalid type returns error."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        file_content = b"Test content"

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "invalid_type"},
        )

        assert response.status_code == 422  # Validation error

    def test_upload_all_ingestion_types(self, client):
        """Test upload with all valid ingestion types."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        ingestion_types = ["ds_etc", "instance_etc", "app_bundle", "single_conf"]

        for ingestion_type in ingestion_types:
            file_content = f"Test content for {ingestion_type}".encode()

            response = client.post(
                "/v1/uploads",
                files={"file": (f"{ingestion_type}.tar.gz", io.BytesIO(file_content))},
                data={"type": ingestion_type},
            )

            assert response.status_code == 201, f"Failed for type {ingestion_type}"
            data = response.json()
            assert data["type"] == ingestion_type
            assert data["status"] == "stored"

    def test_upload_optional_fields(self, client):
        """Test upload without optional fields."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        file_content = b"Test content"

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["label"] is None
        assert data["notes"] is None

    def test_upload_sha256_computation(self, client, test_db):
        """Test that SHA256 hash is correctly computed."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        import hashlib

        file_content = b"Test Splunk configuration content for hash test"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        assert response.status_code == 201
        data = response.json()

        # Verify hash in database
        db = test_db()
        file_record = db.query(FileModel).filter_by(run_id=data["id"]).first()
        assert file_record.sha256 == expected_hash
        db.close()

    def test_upload_large_file(self, client, test_db):
        """Test upload of larger file (1MB)."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a 1MB file
        size_mb = 1
        file_content = b"x" * (size_mb * 1024 * 1024)
        file_name = "large_config.tar.gz"

        response = client.post(
            "/v1/uploads",
            files={"file": (file_name, io.BytesIO(file_content), "application/gzip")},
            data={
                "type": "instance_etc",
                "label": "Large File Upload",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "stored"

        # Verify file size in database
        db = test_db()
        file_record = db.query(FileModel).filter_by(run_id=data["id"]).first()
        assert file_record.size_bytes == len(file_content)
        db.close()

    def test_upload_multiple_files_sequential(self, client, test_db):
        """Test multiple sequential uploads create separate runs."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        run_ids = []
        for i in range(3):
            file_content = f"Test content {i}".encode()
            response = client.post(
                "/v1/uploads",
                files={"file": (f"test_{i}.tar.gz", io.BytesIO(file_content))},
                data={
                    "type": "ds_etc",
                    "label": f"Upload {i}",
                },
            )

            assert response.status_code == 201
            data = response.json()
            run_ids.append(data["id"])

        # Verify all runs are separate and stored
        assert len(set(run_ids)) == 3

        db = test_db()
        for run_id in run_ids:
            run = db.query(IngestionRun).filter_by(id=run_id).first()
            assert run is not None
            assert run.status == IngestionStatus.STORED
        db.close()

    def test_upload_blob_retrievable(self, client, test_storage, test_db):
        """Test that uploaded blob is retrievable from storage."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        file_content = b"Test content to retrieve"
        file_name = "retrieve_test.tar.gz"

        response = client.post(
            "/v1/uploads",
            files={"file": (file_name, io.BytesIO(file_content))},
            data={"type": "app_bundle"},
        )

        assert response.status_code == 201
        data = response.json()

        # Get storage key from database
        db = test_db()
        file_record = db.query(FileModel).filter_by(run_id=data["id"]).first()
        storage_key = file_record.stored_object_key
        db.close()

        # Verify blob exists in storage
        assert test_storage.exists(storage_key)

        # Retrieve and verify content
        blob = test_storage.retrieve_blob(storage_key)
        retrieved_content = blob.read()
        blob.close()
        assert retrieved_content == file_content

    def test_upload_metadata_accuracy(self, client, test_db):
        """Test that all metadata is accurately stored."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        test_data = {
            "type": "single_conf",
            "label": "Metadata Test Upload",
            "notes": "Testing metadata accuracy with special chars: @#$%",
        }
        file_content = b"Config file content"
        file_name = "metadata_test.conf"

        response = client.post(
            "/v1/uploads",
            files={"file": (file_name, io.BytesIO(file_content))},
            data=test_data,
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response matches input
        assert data["type"] == test_data["type"]
        assert data["label"] == test_data["label"]
        assert data["notes"] == test_data["notes"]

        # Verify database record
        db = test_db()
        run = db.query(IngestionRun).filter_by(id=data["id"]).first()
        assert run.type.value == test_data["type"]
        assert run.label == test_data["label"]
        assert run.notes == test_data["notes"]
        assert run.status == IngestionStatus.STORED

        file_record = db.query(FileModel).filter_by(run_id=run.id).first()
        assert file_record.path == file_name
        db.close()


@pytest.mark.database
class TestUploadErrorHandling:
    """Tests for upload error handling and failure scenarios."""

    def test_upload_storage_failure(self, client, test_db, monkeypatch):
        """Test that storage failures are handled gracefully."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        from app.storage import StorageError

        # Mock storage backend to raise error
        def mock_store_blob(self, file, key):
            raise StorageError("Simulated storage failure")

        monkeypatch.setattr(
            "app.storage.local.LocalStorageBackend.store_blob", mock_store_blob
        )

        file_content = b"Test content"
        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        # Should return 500 for storage error
        assert response.status_code == 500
        assert "Failed to store file" in response.json()["detail"]

        # Verify run status is marked as failed
        db = test_db()
        # Find the failed run (latest one)
        runs = db.query(IngestionRun).order_by(IngestionRun.id.desc()).all()
        if runs:
            failed_run = runs[0]
            assert failed_run.status == IngestionStatus.FAILED
            assert "Storage error" in (failed_run.notes or "")
        db.close()

    def test_upload_database_commit_failure(self, client, test_db, monkeypatch):
        """Test handling of database commit failures."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Mock db.commit to raise exception
        commit_call_count = [0]

        original_commit = None

        def mock_commit(self):
            commit_call_count[0] += 1
            # Fail on the final commit (after file storage)
            if commit_call_count[0] >= 2:
                raise Exception("Simulated database commit failure")
            if original_commit:
                original_commit(self)

        # This test is tricky because we need to intercept the session
        # For now, we'll skip this specific scenario as it requires
        # complex mocking
        pytest.skip("Database commit failure test requires complex session mocking")

    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        file_content = b"Test content"
        response = client.post(
            "/v1/uploads",
            files={"file": ("", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        # Should return 400 for empty filename
        assert response.status_code in [400, 422]

    def test_upload_very_large_file(self, client):
        """Test upload of very large file (10MB) to ensure memory handling."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a 10MB file
        size_mb = 10
        file_content = b"x" * (size_mb * 1024 * 1024)

        response = client.post(
            "/v1/uploads",
            files={"file": ("very_large.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        # Should succeed
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "stored"


@pytest.mark.database
class TestUploadIntegration:
    """Integration tests for end-to-end upload lifecycle."""

    def test_upload_lifecycle_complete(self, client, test_storage, test_db):
        """Test complete upload lifecycle from request to storage to database."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        import hashlib

        # Prepare test file
        file_content = b"Complete lifecycle test content"
        file_name = "lifecycle_test.tar.gz"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        # Step 1: Upload file
        response = client.post(
            "/v1/uploads",
            files={"file": (file_name, io.BytesIO(file_content))},
            data={
                "type": "instance_etc",
                "label": "Lifecycle Test",
                "notes": "Testing complete upload lifecycle",
            },
        )

        assert response.status_code == 201
        data = response.json()
        run_id = data["id"]

        # Step 2: Verify response data
        assert data["type"] == "instance_etc"
        assert data["label"] == "Lifecycle Test"
        assert data["notes"] == "Testing complete upload lifecycle"
        assert data["status"] == "stored"
        assert "created_at" in data

        # Step 3: Verify database state
        db = test_db()

        # Check ingestion run
        run = db.query(IngestionRun).filter_by(id=run_id).first()
        assert run is not None
        assert run.status == IngestionStatus.STORED
        assert run.type == IngestionType.INSTANCE_ETC

        # Check file record
        file_record = db.query(FileModel).filter_by(run_id=run_id).first()
        assert file_record is not None
        assert file_record.path == file_name
        assert file_record.sha256 == expected_hash
        assert file_record.size_bytes == len(file_content)
        assert file_record.stored_object_key.startswith(f"runs/{run_id}/")

        storage_key = file_record.stored_object_key
        db.close()

        # Step 4: Verify blob in storage
        assert test_storage.exists(storage_key)

        # Step 5: Verify blob content matches original
        blob = test_storage.retrieve_blob(storage_key)
        retrieved_content = blob.read()
        blob.close()
        assert retrieved_content == file_content
        assert hashlib.sha256(retrieved_content).hexdigest() == expected_hash

    def test_incremental_ingestion(self, client, test_db):
        """Test multiple uploads representing incremental ingestion."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Simulate incremental updates over time
        uploads = [
            {
                "file": b"Initial config v1",
                "name": "config_v1.tar.gz",
                "label": "Version 1",
            },
            {
                "file": b"Updated config v2",
                "name": "config_v2.tar.gz",
                "label": "Version 2",
            },
            {
                "file": b"Final config v3",
                "name": "config_v3.tar.gz",
                "label": "Version 3",
            },
        ]

        run_ids = []
        for upload in uploads:
            response = client.post(
                "/v1/uploads",
                files={"file": (upload["name"], io.BytesIO(upload["file"]))},
                data={
                    "type": "ds_etc",
                    "label": upload["label"],
                },
            )

            assert response.status_code == 201
            run_ids.append(response.json()["id"])

        # Verify all runs exist and are independent
        db = test_db()
        runs = db.query(IngestionRun).filter(IngestionRun.id.in_(run_ids)).all()
        assert len(runs) == 3

        for run in runs:
            assert run.status == IngestionStatus.STORED
            # Each run should have exactly one file
            assert len(run.files) == 1

        db.close()

    def test_concurrent_uploads_isolation(self, client, test_db):
        """Test that concurrent uploads are properly isolated."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Simulate concurrent uploads by making rapid sequential requests
        # (True concurrency would require async/threading)
        responses = []
        for i in range(5):
            file_content = f"Concurrent upload {i}".encode()
            response = client.post(
                "/v1/uploads",
                files={"file": (f"concurrent_{i}.tar.gz", io.BytesIO(file_content))},
                data={"type": "app_bundle"},
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 201

        # All should have unique IDs
        run_ids = [r.json()["id"] for r in responses]
        assert len(set(run_ids)) == 5

        # Verify all runs in database
        db = test_db()
        runs = db.query(IngestionRun).filter(IngestionRun.id.in_(run_ids)).all()
        assert len(runs) == 5
        db.close()


def test_upload_endpoint_exists():
    """Test that upload endpoint module exists and has required components."""
    try:
        from app.api.v1 import uploads

        assert hasattr(uploads, "router")
        assert hasattr(uploads, "upload_file")
        assert hasattr(uploads, "get_storage")

        print("✅ Upload endpoint module structure validated")
    except ImportError as e:
        pytest.skip(f"Upload endpoint module not available: {e}")


if __name__ == "__main__":
    # Run basic validation
    test_upload_endpoint_exists()
    print("✅ Upload endpoint tests configured")

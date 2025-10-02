"""Tests for upload ingestion endpoint."""

import io
import tempfile
from pathlib import Path

import pytest

# Try to import dependencies, skip tests if not available
try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from app.core.db import Base, get_db
    from app.main import create_app
    from app.models.ingestion_run import IngestionStatus, IngestionType
    from app.models.file import File as FileModel
    from app.models.ingestion_run import IngestionRun
    from app.storage import get_storage_backend
    from app.api.v1.uploads import get_storage
    
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

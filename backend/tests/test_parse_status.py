"""Tests for the parse-status endpoint."""

import io
import tempfile

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies, skip tests if not available
try:
    from app.api.v1.uploads import get_storage
    from app.core.db import Base, get_db
    from app.main import create_app
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

    # Import models explicitly to ensure they are registered with Base metadata
    import app.models  # noqa: F401
    from app.models.file import File  # noqa: F401
    from app.models.ingestion_run import IngestionRun  # noqa: F401

    # Use in-memory SQLite for testing with proper configuration
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True,
    )

    # Verify models are registered before creating tables
    if not Base.metadata.tables:
        raise RuntimeError(
            "No tables found in Base.metadata - models not properly imported"
        )

    # Create tables
    Base.metadata.create_all(engine)

    # Verify tables were actually created
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "ingestion_runs" not in tables:
        raise RuntimeError(
            f"ingestion_runs table not created. Available tables: {tables}"
        )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(engine)
    engine.dispose()


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
class TestParseStatusEndpoint:
    """Tests for the GET /v1/runs/{run_id}/parse-status endpoint."""

    def test_parse_status_not_found(self, client):
        """Test parse-status for non-existent run."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get("/v1/runs/999/parse-status")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_parse_status_invalid_run_id(self, client):
        """Test parse-status with invalid run_id."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get("/v1/runs/-1/parse-status")

        assert response.status_code == 400
        data = response.json()
        assert "invalid run_id" in data["detail"].lower()

    def test_parse_status_stored(self, client):
        """Test parse-status for run in stored state."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create an upload
        file_content = b"Test Splunk configuration"
        upload_response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={
                "type": "ds_etc",
                "label": "Test Run",
            },
        )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        run_id = upload_data["id"]

        # Get parse status
        response = client.get(f"/v1/runs/{run_id}/parse-status")

        assert response.status_code == 200
        data = response.json()

        assert data["run_id"] == run_id
        assert data["status"] == "stored"
        assert data["error_message"] is None
        assert data["summary"] is None  # No metrics yet

    def test_parse_status_with_metrics(self, client, test_db):
        """Test parse-status returns metrics summary."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a run with metrics directly in database
        db = test_db()
        run = IngestionRun(
            type=IngestionType.DS_ETC,
            label="Test Run with Metrics",
            status=IngestionStatus.COMPLETE,
            metrics={
                "files_parsed": 10,
                "stanzas_created": 50,
                "typed_projections": {
                    "inputs": 5,
                    "props": 3,
                    "transforms": 2,
                },
                "parse_errors": 0,
                "duration_seconds": 12.5,
            },
        )
        db.add(run)
        db.commit()
        run_id = run.id
        db.close()

        # Get parse status
        response = client.get(f"/v1/runs/{run_id}/parse-status")

        assert response.status_code == 200
        data = response.json()

        assert data["run_id"] == run_id
        assert data["status"] == "complete"
        assert data["error_message"] is None
        assert data["summary"] is not None
        assert data["summary"]["files_parsed"] == 10
        assert data["summary"]["stanzas_created"] == 50
        assert data["summary"]["typed_projections"]["inputs"] == 5
        assert data["summary"]["parse_errors"] == 0
        assert data["summary"]["duration_seconds"] == 12.5

    def test_parse_status_failed_with_error(self, client, test_db):
        """Test parse-status for failed run with error message."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a failed run directly in database
        db = test_db()
        run = IngestionRun(
            type=IngestionType.DS_ETC,
            label="Failed Run",
            status=IngestionStatus.FAILED,
            error_message="Parse error: Invalid configuration format",
        )
        db.add(run)
        db.commit()
        run_id = run.id
        db.close()

        # Get parse status
        response = client.get(f"/v1/runs/{run_id}/parse-status")

        assert response.status_code == 200
        data = response.json()

        assert data["run_id"] == run_id
        assert data["status"] == "failed"
        assert data["error_message"] == "Parse error: Invalid configuration format"

    def test_parse_status_parsing(self, client, test_db):
        """Test parse-status for run currently being parsed."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a run in parsing state directly in database
        db = test_db()
        run = IngestionRun(
            type=IngestionType.DS_ETC,
            label="Parsing Run",
            status=IngestionStatus.PARSING,
            task_id="test-task-id-123",
        )
        db.add(run)
        db.commit()
        run_id = run.id
        db.close()

        # Get parse status
        response = client.get(f"/v1/runs/{run_id}/parse-status")

        assert response.status_code == 200
        data = response.json()

        assert data["run_id"] == run_id
        assert data["status"] == "parsing"
        assert data["error_message"] is None

    def test_parse_status_normalized(self, client, test_db):
        """Test parse-status for run in normalized state."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a run in normalized state directly in database
        db = test_db()
        run = IngestionRun(
            type=IngestionType.DS_ETC,
            label="Normalized Run",
            status=IngestionStatus.NORMALIZED,
        )
        db.add(run)
        db.commit()
        run_id = run.id
        db.close()

        # Get parse status
        response = client.get(f"/v1/runs/{run_id}/parse-status")

        assert response.status_code == 200
        data = response.json()

        assert data["run_id"] == run_id
        assert data["status"] == "normalized"

    def test_parse_status_response_structure(self, client):
        """Test parse-status response has correct structure for frontend polling."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create an upload
        file_content = b"Test Splunk configuration"
        upload_response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={"type": "ds_etc"},
        )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        run_id = upload_data["id"]

        # Get parse status
        response = client.get(f"/v1/runs/{run_id}/parse-status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure matches IngestionRunStatusResponse
        assert "run_id" in data
        assert "status" in data
        assert "error_message" in data
        assert "summary" in data

        # Verify status is a valid parse state
        valid_states = ["pending", "stored", "parsing", "normalized", "complete", "failed"]
        assert data["status"] in valid_states

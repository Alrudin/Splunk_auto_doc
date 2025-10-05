"""Tests for runs listing and detail endpoints."""

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
    # This MUST happen before create_all() is called
    # Also import the models package to ensure __init__.py runs
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
class TestRunsListEndpoint:
    """Tests for the GET /v1/runs endpoint."""

    def test_list_runs_empty(self, client):
        """Test listing runs when database is empty."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get("/v1/runs")

        assert response.status_code == 200
        data = response.json()

        assert data["runs"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 50

    def test_list_runs_after_upload(self, client):
        """Test that uploaded runs appear in the list."""
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
                "notes": "Test notes",
            },
        )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()

        # List runs
        list_response = client.get("/v1/runs")

        assert list_response.status_code == 200
        list_data = list_response.json()

        assert list_data["total"] == 1
        assert len(list_data["runs"]) == 1

        # Verify the run details match
        run = list_data["runs"][0]
        assert run["id"] == upload_data["id"]
        assert run["type"] == "ds_etc"
        assert run["label"] == "Test Run"
        assert run["notes"] == "Test notes"
        assert run["status"] == "stored"
        assert "created_at" in run

    def test_list_runs_pagination(self, client, test_db):
        """Test pagination of runs list."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create multiple runs directly in database
        db = test_db()
        for i in range(5):
            run = IngestionRun(
                type=IngestionType.DS_ETC,
                label=f"Test Run {i}",
                status=IngestionStatus.STORED,
            )
            db.add(run)
        db.commit()
        db.close()

        # Test first page with 2 per page
        response = client.get("/v1/runs?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["runs"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2

        # Test second page
        response = client.get("/v1/runs?page=2&per_page=2")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["runs"]) == 2
        assert data["page"] == 2

        # Test last page
        response = client.get("/v1/runs?page=3&per_page=2")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert len(data["runs"]) == 1
        assert data["page"] == 3

    def test_list_runs_ordering(self, client, test_db):
        """Test that runs are ordered by created_at descending (most recent first)."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create multiple runs with different timestamps
        from datetime import datetime, timedelta

        db = test_db()
        base_time = datetime.utcnow()

        run_ids = []
        for i in range(3):
            run = IngestionRun(
                type=IngestionType.DS_ETC,
                label=f"Run {i}",
                status=IngestionStatus.STORED,
            )
            db.add(run)
            db.flush()
            # Manually set created_at to ensure ordering
            run.created_at = base_time - timedelta(hours=i)
            run_ids.append(run.id)

        db.commit()
        db.close()

        # List runs
        response = client.get("/v1/runs")
        assert response.status_code == 200
        data = response.json()

        # Verify ordering: newest first (run_ids[0] should be first)
        returned_ids = [run["id"] for run in data["runs"]]
        assert (
            returned_ids == run_ids
        )  # Should be in order [0, 1, 2] (newest to oldest)

    def test_list_runs_pagination_limits(self, client):
        """Test pagination parameter validation."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Test invalid page (0)
        response = client.get("/v1/runs?page=0")
        assert response.status_code == 422  # Validation error

        # Test invalid per_page (>100)
        response = client.get("/v1/runs?per_page=101")
        assert response.status_code == 422

        # Test valid limits
        response = client.get("/v1/runs?page=1&per_page=100")
        assert response.status_code == 200


@pytest.mark.database
class TestRunDetailEndpoint:
    """Tests for the GET /v1/runs/{id} endpoint."""

    def test_get_run_success(self, client):
        """Test getting a specific run by ID."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create an upload
        file_content = b"Test Splunk configuration"
        upload_response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", io.BytesIO(file_content))},
            data={
                "type": "instance_etc",
                "label": "Detailed Test Run",
                "notes": "Test notes for detail",
            },
        )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        run_id = upload_data["id"]

        # Get run details
        detail_response = client.get(f"/v1/runs/{run_id}")

        assert detail_response.status_code == 200
        detail_data = detail_response.json()

        # Verify all fields match
        assert detail_data["id"] == run_id
        assert detail_data["type"] == "instance_etc"
        assert detail_data["label"] == "Detailed Test Run"
        assert detail_data["notes"] == "Test notes for detail"
        assert detail_data["status"] == "stored"
        assert detail_data["created_at"] == upload_data["created_at"]

    def test_get_run_matches_database(self, client, test_db):
        """Test that detail endpoint matches database row exactly."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Create a run directly in database
        db = test_db()
        run = IngestionRun(
            type=IngestionType.APP_BUNDLE,
            label="Direct DB Run",
            notes="Created directly in DB",
            status=IngestionStatus.STORED,
        )
        db.add(run)
        db.commit()

        run_id = run.id
        # db_created_at = run.created_at
        db.close()

        # Get run via API
        response = client.get(f"/v1/runs/{run_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify exact match with database
        assert data["id"] == run_id
        assert data["type"] == "app_bundle"
        assert data["label"] == "Direct DB Run"
        assert data["notes"] == "Created directly in DB"
        assert data["status"] == "stored"

        # Verify timestamp is present and properly formatted
        assert "created_at" in data
        assert data["created_at"] is not None
        # Basic timestamp format check
        assert "T" in data["created_at"]  # ISO format includes T separator

    def test_get_run_not_found(self, client):
        """Test getting a non-existent run returns 404."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get("/v1/runs/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_run_invalid_id(self, client):
        """Test getting a run with invalid ID returns 400."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        # Test negative ID
        response = client.get("/v1/runs/-1")
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()

        # Test zero ID
        response = client.get("/v1/runs/0")
        assert response.status_code == 400

    def test_get_run_all_statuses(self, client, test_db):
        """Test that runs with all statuses can be retrieved."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        db = test_db()

        # Create runs with different statuses
        statuses = [
            IngestionStatus.PENDING,
            IngestionStatus.STORED,
            IngestionStatus.FAILED,
            IngestionStatus.COMPLETE,
        ]

        run_ids = []
        for status in statuses:
            run = IngestionRun(
                type=IngestionType.DS_ETC,
                label=f"Run with {status.value} status",
                status=status,
            )
            db.add(run)
            db.flush()
            run_ids.append(run.id)

        db.commit()
        db.close()

        # Verify each run can be retrieved
        for run_id, expected_status in zip(run_ids, statuses, strict=False):
            response = client.get(f"/v1/runs/{run_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == expected_status.value


def test_runs_endpoint_exists():
    """Test that runs endpoint module exists and has required components."""
    try:
        from app.api.v1 import runs

        assert hasattr(runs, "router")
        assert hasattr(runs, "list_runs")
        assert hasattr(runs, "get_run")

        print("✅ Runs endpoint module structure validated")
    except ImportError as e:
        pytest.skip(f"Runs endpoint module not available: {e}")


if __name__ == "__main__":
    # Run basic validation
    test_runs_endpoint_exists()
    print("✅ Runs endpoint tests configured")

"""Tests for run status lifecycle and status API endpoints."""

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies, skip tests if not available
try:
    from datetime import datetime

    from app.core.db import Base, get_db
    from app.main import create_app
    from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
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

    # Create tables
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(test_db):
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

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)


def test_status_lifecycle_enum_values():
    """Test that all expected status values exist in IngestionStatus enum."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Verify all status values exist
    assert hasattr(IngestionStatus, "PENDING")
    assert hasattr(IngestionStatus, "STORED")
    assert hasattr(IngestionStatus, "PARSING")
    assert hasattr(IngestionStatus, "NORMALIZED")
    assert hasattr(IngestionStatus, "COMPLETE")
    assert hasattr(IngestionStatus, "FAILED")

    # Verify values
    assert IngestionStatus.PENDING.value == "pending"
    assert IngestionStatus.STORED.value == "stored"
    assert IngestionStatus.PARSING.value == "parsing"
    assert IngestionStatus.NORMALIZED.value == "normalized"
    assert IngestionStatus.COMPLETE.value == "complete"
    assert IngestionStatus.FAILED.value == "failed"


def test_get_run_status_endpoint(client, test_db):
    """Test GET /runs/{run_id}/status endpoint."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a test run
    db = test_db()
    run = IngestionRun(
        type=IngestionType.DS_ETC,
        label="Test Run",
        status=IngestionStatus.COMPLETE,
        metrics={
            "files_parsed": 5,
            "stanzas_created": 100,
            "typed_projections": {"inputs": 20, "props": 15},
            "parse_errors": 0,
            "duration_seconds": 10.5,
        },
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Get status
    response = client.get(f"/v1/runs/{run_id}/status")
    assert response.status_code == 200

    data = response.json()
    assert data["run_id"] == run_id
    assert data["status"] == "complete"
    assert data["error_message"] is None
    assert data["summary"] is not None
    assert data["summary"]["files_parsed"] == 5
    assert data["summary"]["stanzas_created"] == 100
    assert data["summary"]["typed_projections"]["inputs"] == 20
    assert data["summary"]["typed_projections"]["props"] == 15
    assert data["summary"]["parse_errors"] == 0
    assert data["summary"]["duration_seconds"] == 10.5


def test_get_run_status_not_found(client):
    """Test GET /runs/{run_id}/status with non-existent run."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    response = client.get("/v1/runs/99999/status")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_run_status_invalid_id(client):
    """Test GET /runs/{run_id}/status with invalid run_id."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    response = client.get("/v1/runs/0/status")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_get_run_status_with_error(client, test_db):
    """Test GET /runs/{run_id}/status for failed run with error message."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a failed run
    db = test_db()
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Failed Run",
        status=IngestionStatus.FAILED,
        error_message="Archive extraction failed",
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Get status
    response = client.get(f"/v1/runs/{run_id}/status")
    assert response.status_code == 200

    data = response.json()
    assert data["run_id"] == run_id
    assert data["status"] == "failed"
    assert data["error_message"] == "Archive extraction failed"
    assert data["summary"] is None


def test_update_run_status_endpoint(client, test_db):
    """Test PATCH /runs/{run_id}/status endpoint."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a test run
    db = test_db()
    run = IngestionRun(
        type=IngestionType.INSTANCE_ETC,
        label="Test Run",
        status=IngestionStatus.PARSING,
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Update status to normalized
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "normalized", "error_message": None},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["run_id"] == run_id
    assert data["status"] == "normalized"
    assert data["error_message"] is None

    # Verify in database
    db = test_db()
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert run.status == IngestionStatus.NORMALIZED
    db.close()


def test_update_run_status_with_error(client, test_db):
    """Test PATCH /runs/{run_id}/status with error message."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a test run
    db = test_db()
    run = IngestionRun(
        type=IngestionType.SINGLE_CONF,
        label="Test Run",
        status=IngestionStatus.PARSING,
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Update status to failed with error
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "failed", "error_message": "Manual intervention required"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["run_id"] == run_id
    assert data["status"] == "failed"
    assert data["error_message"] == "Manual intervention required"

    # Verify in database
    db = test_db()
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert run.status == IngestionStatus.FAILED
    assert run.error_message == "Manual intervention required"
    assert run.completed_at is not None  # Should auto-set completed_at
    db.close()


def test_update_run_status_sets_completed_at(client, test_db):
    """Test that PATCH sets completed_at for terminal states."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a test run
    db = test_db()
    run = IngestionRun(
        type=IngestionType.DS_ETC,
        label="Test Run",
        status=IngestionStatus.NORMALIZED,
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Update to complete
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "complete"},
    )
    assert response.status_code == 200

    # Verify completed_at was set
    db = test_db()
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert run.status == IngestionStatus.COMPLETE
    assert run.completed_at is not None
    db.close()


def test_update_run_status_not_found(client):
    """Test PATCH /runs/{run_id}/status with non-existent run."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    response = client.patch(
        "/v1/runs/99999/status",
        json={"status": "complete"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_run_status_invalid_id(client):
    """Test PATCH /runs/{run_id}/status with invalid run_id."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    response = client.patch(
        "/v1/runs/-1/status",
        json={"status": "complete"},
    )
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_status_transition_sequence(client, test_db):
    """Test a complete status transition sequence."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a run in pending state
    db = test_db()
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Transition",
        status=IngestionStatus.PENDING,
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Transition: pending → stored
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "stored"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "stored"

    # Transition: stored → parsing
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "parsing"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "parsing"

    # Transition: parsing → normalized
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "normalized"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "normalized"

    # Transition: normalized → complete
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "complete"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "complete"


def test_status_transition_to_failed(client, test_db):
    """Test transition to failed status from any state."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create a run in parsing state
    db = test_db()
    run = IngestionRun(
        type=IngestionType.INSTANCE_ETC,
        label="Test Failure",
        status=IngestionStatus.PARSING,
    )
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    # Transition to failed
    response = client.patch(
        f"/v1/runs/{run_id}/status",
        json={"status": "failed", "error_message": "Test error"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Test error"

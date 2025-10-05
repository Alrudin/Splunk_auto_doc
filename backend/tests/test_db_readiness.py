"""Tests for database readiness functionality."""

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client_no_override() -> TestClient:
    """Create test client without database overrides to test real health checks."""
    app = create_app()
    return TestClient(app)


def test_health_check_always_returns_healthy(client_no_override: TestClient) -> None:
    """Test that basic health check always returns healthy status."""
    response = client_no_override.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "splunk-auto-doc-api"
    assert "version" in data


def test_v1_health_check_returns_ok(client_no_override: TestClient) -> None:
    """Test that v1 health check returns ok status."""
    response = client_no_override.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data


def test_readiness_check_legacy_endpoint(client_no_override: TestClient) -> None:
    """Test legacy readiness check endpoint includes database check."""
    response = client_no_override.get("/health/ready")
    # May be 200 or 503 depending on test DB availability
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]

    # Status should reflect database state
    if response.status_code == 200:
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "healthy"
    else:
        assert data["status"] == "not ready"
        assert "unhealthy" in data["checks"]["database"]


def test_readiness_check_v1_endpoint(client_no_override: TestClient) -> None:
    """Test v1 readiness check endpoint includes database check."""
    response = client_no_override.get("/v1/ready")
    # May be 200 or 503 depending on test DB availability
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "timestamp" in data

    # Status should reflect database state
    if response.status_code == 200:
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "healthy"
    else:
        assert data["status"] == "not ready"
        assert "unhealthy" in data["checks"]["database"]


def test_readiness_returns_503_when_db_unavailable(monkeypatch) -> None:
    """Test that readiness check returns 503 when database is unavailable."""
    # This test verifies the behavior when DB connection fails
    from sqlalchemy import create_engine

    # Create a bad engine that will fail to connect
    bad_engine = create_engine("postgresql://invalid:invalid@localhost:9999/invalid")

    # Temporarily replace the engine
    import app.api.v1.health
    import app.health

    original_engine = app.health.engine
    original_v1_engine = app.api.v1.health.engine

    try:
        app.health.engine = bad_engine
        app.api.v1.health.engine = bad_engine

        app_test = create_app()
        client = TestClient(app_test)

        # Test legacy endpoint
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not ready"
        assert "unhealthy" in data["checks"]["database"]

        # Test v1 endpoint
        response = client.get("/v1/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not ready"
        assert "unhealthy" in data["checks"]["database"]
    finally:
        # Restore original engine
        app.health.engine = original_engine
        app.api.v1.health.engine = original_v1_engine

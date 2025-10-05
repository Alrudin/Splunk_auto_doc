"""Tests for health check endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test basic health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "splunk-auto-doc-api"
    assert "version" in data


def test_readiness_check(client: TestClient) -> None:
    """Test readiness check endpoint."""
    # Mock the database engine to simulate a healthy database connection
    with patch("app.health.engine") as mock_engine:
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = None

        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"] == "healthy"


def test_readiness_check_database_failure(client: TestClient) -> None:
    """Test readiness check endpoint when database is unhealthy."""
    # Mock the database engine to simulate a database connection failure
    with patch("app.health.engine") as mock_engine:
        mock_engine.connect.side_effect = Exception("Database connection failed")

        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not ready"
        assert "checks" in data
        assert "unhealthy" in data["checks"]["database"]

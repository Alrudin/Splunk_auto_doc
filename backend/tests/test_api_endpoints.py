"""Unit tests for API endpoints."""

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON response."""
        response = client.get("/v1/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_status_ok(self, client):
        """Test that health endpoint returns status 'ok'."""
        response = client.get("/v1/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint_includes_timestamp(self, client):
        """Test that health endpoint includes timestamp."""
        response = client.get("/v1/health")
        data = response.json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_health_endpoint_includes_version(self, client):
        """Test that health endpoint includes version."""
        response = client.get("/v1/health")
        data = response.json()
        assert "version" in data


class TestUploadEndpointUnit:
    """Unit tests for the upload endpoint structure."""

    def test_upload_endpoint_exists(self, client):
        """Test that upload endpoint is registered."""
        # This will return 422 (validation error) for GET requests
        # but confirms the endpoint exists
        response = client.get("/v1/uploads")
        # 405 Method Not Allowed or 422 Unprocessable Entity both mean endpoint exists
        assert response.status_code in [405, 422]

    def test_upload_requires_file(self, client):
        """Test that upload endpoint requires a file."""
        response = client.post("/v1/uploads")
        # Should return 422 because file is required
        assert response.status_code == 422


class TestRunsEndpointUnit:
    """Unit tests for the runs endpoint structure."""

    def test_runs_list_endpoint_exists(self, client):
        """Test that runs list endpoint is registered."""
        response = client.get("/v1/runs")
        # Should return 200 with empty list or actual data
        assert response.status_code == 200

    def test_runs_list_returns_json(self, client):
        """Test that runs list returns JSON."""
        response = client.get("/v1/runs")
        assert response.headers["content-type"] == "application/json"

    def test_runs_list_structure(self, client):
        """Test that runs list has expected structure."""
        response = client.get("/v1/runs")
        data = response.json()
        
        # Should have pagination fields
        assert "runs" in data
        assert isinstance(data["runs"], list)
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_runs_detail_nonexistent_returns_404(self, client):
        """Test that getting a non-existent run returns 404."""
        response = client.get("/v1/runs/99999")
        assert response.status_code == 404

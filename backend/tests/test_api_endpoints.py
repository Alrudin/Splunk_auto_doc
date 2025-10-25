"""Unit tests for API endpoints."""


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

    def test_runs_summary_endpoint_exists(self, client):
        """Test that run summary endpoint is registered."""
        # Should return 404 for non-existent run, confirming endpoint exists
        response = client.get("/v1/runs/99999/summary")
        assert response.status_code == 404

    def test_runs_summary_nonexistent_returns_404(self, client):
        """Test that getting summary for non-existent run returns 404."""
        response = client.get("/v1/runs/99999/summary")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_runs_summary_invalid_id_returns_400(self, client):
        """Test that invalid run_id returns 400."""
        response = client.get("/v1/runs/0/summary")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "positive integer" in data["detail"].lower()

    def test_runs_summary_structure(self, client, db_session):
        """Test that run summary has expected structure."""
        from app.models.ingestion_run import (
            IngestionRun,
            IngestionStatus,
            IngestionType,
        )

        # Create a test run
        run = IngestionRun(
            type=IngestionType.DS_ETC,
            status=IngestionStatus.COMPLETE,
            label="Test Run",
        )
        db_session.add(run)
        db_session.commit()

        response = client.get(f"/v1/runs/{run.id}/summary")
        assert response.status_code == 200
        data = response.json()

        # Should have all required fields
        assert "run_id" in data
        assert data["run_id"] == run.id
        assert "status" in data
        assert data["status"] == "complete"
        assert "stanzas" in data
        assert "inputs" in data
        assert "props" in data
        assert "transforms" in data
        assert "indexes" in data
        assert "outputs" in data
        assert "serverclasses" in data

        # All counts should be integers
        assert isinstance(data["stanzas"], int)
        assert isinstance(data["inputs"], int)
        assert isinstance(data["props"], int)
        assert isinstance(data["transforms"], int)
        assert isinstance(data["indexes"], int)
        assert isinstance(data["outputs"], int)
        assert isinstance(data["serverclasses"], int)

        # For new run with no data, all counts should be 0
        assert data["stanzas"] == 0
        assert data["inputs"] == 0
        assert data["props"] == 0
        assert data["transforms"] == 0
        assert data["indexes"] == 0
        assert data["outputs"] == 0
        assert data["serverclasses"] == 0

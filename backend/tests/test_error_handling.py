"""Integration tests for error handling across the application."""

import pytest


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422 Unprocessable Entity."""
        response = client.post(
            "/v1/uploads",
            data=b"not json",
            headers={"Content-Type": "application/json"}
        )
        # FastAPI returns 422 for validation errors
        assert response.status_code in [400, 422]

    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/v1/nonexistent")
        assert response.status_code == 404

    def test_invalid_run_id_format(self, client):
        """Test that invalid run ID format is handled."""
        response = client.get("/v1/runs/not-a-number")
        assert response.status_code in [404, 422]

    def test_runs_pagination_validation(self, client):
        """Test that pagination parameters are validated."""
        # Test negative page number
        response = client.get("/v1/runs?page=-1")
        # Should either reject or default to page 1
        assert response.status_code in [200, 422]
        
        # Test invalid per_page
        response = client.get("/v1/runs?per_page=0")
        assert response.status_code in [200, 422]

    def test_upload_empty_file(self, client):
        """Test handling of empty file upload."""
        import io
        
        empty_file = io.BytesIO(b"")
        response = client.post(
            "/v1/uploads",
            files={"file": ("empty.tar.gz", empty_file, "application/gzip")},
            data={
                "ingestion_type": "instance_etc",
                "label": "Empty File Test",
            }
        )
        # Should handle empty file gracefully
        assert response.status_code in [200, 400, 422]

    def test_upload_missing_metadata(self, client):
        """Test upload with missing required metadata."""
        import io
        
        test_file = io.BytesIO(b"test content")
        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", test_file, "application/gzip")},
            # Missing ingestion_type
        )
        # Should return 422 for missing required field
        assert response.status_code == 422

    def test_upload_invalid_ingestion_type(self, client):
        """Test upload with invalid ingestion type."""
        import io
        
        test_file = io.BytesIO(b"test content")
        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", test_file, "application/gzip")},
            data={
                "ingestion_type": "invalid_type",
                "label": "Invalid Type Test",
            }
        )
        # Should return 422 for invalid enum value
        assert response.status_code == 422

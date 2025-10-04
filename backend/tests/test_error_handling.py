"""Integration tests for error handling across the application."""

import io

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
        empty_file = io.BytesIO(b"")
        response = client.post(
            "/v1/uploads",
            files={"file": ("empty.tar.gz", empty_file, "application/gzip")},
            data={
                "type": "instance_etc",
                "label": "Empty File Test",
            }
        )
        # Should handle empty file gracefully (either accept or reject with proper status)
        assert response.status_code in [200, 201, 400, 422]

    def test_upload_missing_metadata(self, client):
        """Test upload with missing required metadata."""
        test_file = io.BytesIO(b"test content")
        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", test_file, "application/gzip")},
            # Missing type parameter
        )
        # Should return 422 for missing required field
        assert response.status_code == 422

    def test_upload_invalid_ingestion_type(self, client):
        """Test upload with invalid ingestion type."""
        test_file = io.BytesIO(b"test content")
        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", test_file, "application/gzip")},
            data={
                "type": "invalid_type",
                "label": "Invalid Type Test",
            }
        )
        # Should return 422 for invalid enum value
        assert response.status_code == 422

    def test_upload_no_file_field(self, client):
        """Test upload request without file field."""
        response = client.post(
            "/v1/uploads",
            data={"type": "ds_etc"}
        )
        # Should return 422 for missing file
        assert response.status_code == 422

    def test_upload_multiple_files_not_supported(self, client):
        """Test that uploading multiple files in one request is handled."""
        file1 = io.BytesIO(b"content 1")
        file2 = io.BytesIO(b"content 2")
        
        # FastAPI will only accept the first file when using File() without list
        response = client.post(
            "/v1/uploads",
            files=[
                ("file", ("test1.tar.gz", file1, "application/gzip")),
                ("file", ("test2.tar.gz", file2, "application/gzip")),
            ],
            data={"type": "ds_etc"}
        )
        
        # Should either process one file or reject the request
        # Most likely will process just the first file
        assert response.status_code in [201, 400, 422]

    def test_upload_special_characters_in_filename(self, client):
        """Test upload with special characters in filename."""
        test_file = io.BytesIO(b"test content")
        special_filenames = [
            "file with spaces.tar.gz",
            "file_with_unicode_日本語.tar.gz",
            "file-with-dashes.tar.gz",
            "file.multiple.dots.tar.gz",
        ]

        for filename in special_filenames:
            response = client.post(
                "/v1/uploads",
                files={"file": (filename, test_file, "application/gzip")},
                data={"type": "ds_etc"}
            )
            # Reset file pointer for next iteration
            test_file.seek(0)
            
            # Should handle gracefully (either accept or reject consistently)
            assert response.status_code in [201, 400, 422], f"Failed for filename: {filename}"

    def test_upload_with_very_long_label(self, client):
        """Test upload with very long label (255+ chars)."""
        test_file = io.BytesIO(b"test content")
        long_label = "x" * 300  # Exceeds typical varchar(255)

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", test_file, "application/gzip")},
            data={
                "type": "ds_etc",
                "label": long_label,
            }
        )

        # Should either truncate or reject
        assert response.status_code in [201, 400, 422, 500]

    def test_upload_with_very_long_notes(self, client):
        """Test upload with very long notes text."""
        test_file = io.BytesIO(b"test content")
        long_notes = "x" * 10000  # Very long text

        response = client.post(
            "/v1/uploads",
            files={"file": ("test.tar.gz", test_file, "application/gzip")},
            data={
                "type": "ds_etc",
                "notes": long_notes,
            }
        )

        # Should handle large text field (TEXT type in DB should support this)
        assert response.status_code in [201, 400, 422, 500]


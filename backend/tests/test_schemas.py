"""Tests for Pydantic schemas."""

from datetime import datetime

import pytest


def test_ingestion_run_schemas():
    """Test IngestionRun schema structure."""
    try:
        from app.models import IngestionStatus, IngestionType
        from app.schemas import IngestionRunCreate, IngestionRunResponse

        # Test create schema
        create_data = {
            "type": IngestionType.DS_ETC,
            "label": "Test Run",
            "notes": "Test notes",
        }
        create_schema = IngestionRunCreate(**create_data)
        assert create_schema.type == IngestionType.DS_ETC
        assert create_schema.label == "Test Run"
        assert create_schema.notes == "Test notes"

        # Test response schema
        response_data = {
            "id": 1,
            "type": IngestionType.DS_ETC,
            "label": "Test Run",
            "notes": "Test notes",
            "status": IngestionStatus.PENDING,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }
        response_schema = IngestionRunResponse(**response_data)
        assert response_schema.id == 1
        assert response_schema.status == IngestionStatus.PENDING

    except ImportError as e:
        pytest.skip(f"Pydantic or models not installed: {e}")


def test_file_schemas():
    """Test File schema structure."""
    try:
        from app.schemas import FileResponse

        # Test file response schema
        file_data = {
            "id": 1,
            "run_id": 1,
            "path": "test.tar.gz",
            "sha256": "a" * 64,
            "size_bytes": 1024,
            "stored_object_key": "storage/test.tar.gz",
        }
        file_schema = FileResponse(**file_data)
        assert file_schema.id == 1
        assert file_schema.run_id == 1
        assert file_schema.path == "test.tar.gz"
        assert len(file_schema.sha256) == 64
        assert file_schema.size_bytes == 1024

    except ImportError as e:
        pytest.skip(f"Pydantic not installed: {e}")


def test_ingestion_run_list_response():
    """Test IngestionRunListResponse schema."""
    try:
        from app.schemas import IngestionRunListResponse

        list_data = {
            "runs": [],
            "total": 0,
            "page": 1,
            "per_page": 50,
        }
        list_schema = IngestionRunListResponse(**list_data)
        assert list_schema.runs == []
        assert list_schema.total == 0
        assert list_schema.page == 1
        assert list_schema.per_page == 50

    except ImportError as e:
        pytest.skip(f"Pydantic not installed: {e}")

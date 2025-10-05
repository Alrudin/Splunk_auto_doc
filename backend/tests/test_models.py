"""Tests for database models."""

from datetime import datetime

import pytest

# These tests will work once dependencies are installed
# For now they serve as documentation of expected behavior


def test_ingestion_run_model():
    """Test IngestionRun model structure and relationships."""
    try:
        from app.models import IngestionRun, IngestionStatus, IngestionType

        # Test enum values
        assert IngestionType.DS_ETC.value == "ds_etc"
        assert IngestionType.INSTANCE_ETC.value == "instance_etc"
        assert IngestionType.APP_BUNDLE.value == "app_bundle"
        assert IngestionType.SINGLE_CONF.value == "single_conf"

        assert IngestionStatus.PENDING.value == "pending"
        assert IngestionStatus.STORED.value == "stored"
        assert IngestionStatus.FAILED.value == "failed"
        assert IngestionStatus.COMPLETE.value == "complete"

        # Test model attributes
        assert hasattr(IngestionRun, "__tablename__")
        assert IngestionRun.__tablename__ == "ingestion_runs"
        assert hasattr(IngestionRun, "id")
        assert hasattr(IngestionRun, "created_at")
        assert hasattr(IngestionRun, "type")
        assert hasattr(IngestionRun, "label")
        assert hasattr(IngestionRun, "status")
        assert hasattr(IngestionRun, "notes")
        assert hasattr(IngestionRun, "files")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_file_model():
    """Test File model structure and relationships."""
    try:
        from app.models import File

        # Test model attributes
        assert hasattr(File, "__tablename__")
        assert File.__tablename__ == "files"
        assert hasattr(File, "id")
        assert hasattr(File, "run_id")
        assert hasattr(File, "path")
        assert hasattr(File, "sha256")
        assert hasattr(File, "size_bytes")
        assert hasattr(File, "stored_object_key")
        assert hasattr(File, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_model_relationships():
    """Test that model relationships are correctly defined."""
    try:
        from app.models import File, IngestionRun

        # Check relationship names
        assert hasattr(IngestionRun, "files")
        assert hasattr(File, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_ingestion_run_repr():
    """Test IngestionRun string representation."""
    try:
        from app.models import IngestionRun, IngestionStatus, IngestionType

        # Create a mock instance (not saved to DB)
        run = IngestionRun(
            id=1,
            type=IngestionType.DS_ETC,
            status=IngestionStatus.PENDING,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        repr_str = repr(run)
        assert "IngestionRun" in repr_str
        assert "id=1" in repr_str
        assert "ds_etc" in repr_str
        assert "pending" in repr_str

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_file_repr():
    """Test File string representation."""
    try:
        from app.models import File

        # Create a mock instance (not saved to DB)
        file = File(
            id=1,
            run_id=1,
            path="test.tar.gz",
            sha256="a" * 64,
            size_bytes=1024,
            stored_object_key="storage/test.tar.gz",
        )

        repr_str = repr(file)
        assert "File" in repr_str
        assert "id=1" in repr_str
        assert "run_id=1" in repr_str
        assert "test.tar.gz" in repr_str

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")

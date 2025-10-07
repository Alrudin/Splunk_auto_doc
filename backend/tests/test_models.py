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


def test_stanza_model():
    """Test Stanza model structure."""
    try:
        from app.models import Stanza

        # Test model attributes
        assert hasattr(Stanza, "__tablename__")
        assert Stanza.__tablename__ == "stanzas"
        assert hasattr(Stanza, "id")
        assert hasattr(Stanza, "run_id")
        assert hasattr(Stanza, "file_id")
        assert hasattr(Stanza, "conf_type")
        assert hasattr(Stanza, "name")
        assert hasattr(Stanza, "app")
        assert hasattr(Stanza, "scope")
        assert hasattr(Stanza, "layer")
        assert hasattr(Stanza, "order_in_file")
        assert hasattr(Stanza, "source_path")
        assert hasattr(Stanza, "raw_kv")
        assert hasattr(Stanza, "ingestion_run")
        assert hasattr(Stanza, "file")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_input_model():
    """Test Input model structure."""
    try:
        from app.models import Input

        # Test model attributes
        assert hasattr(Input, "__tablename__")
        assert Input.__tablename__ == "inputs"
        assert hasattr(Input, "id")
        assert hasattr(Input, "run_id")
        assert hasattr(Input, "source_path")
        assert hasattr(Input, "stanza_type")
        assert hasattr(Input, "index")
        assert hasattr(Input, "sourcetype")
        assert hasattr(Input, "disabled")
        assert hasattr(Input, "kv")
        assert hasattr(Input, "app")
        assert hasattr(Input, "scope")
        assert hasattr(Input, "layer")
        assert hasattr(Input, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_props_model():
    """Test Props model structure."""
    try:
        from app.models import Props

        # Test model attributes
        assert hasattr(Props, "__tablename__")
        assert Props.__tablename__ == "props"
        assert hasattr(Props, "id")
        assert hasattr(Props, "run_id")
        assert hasattr(Props, "target")
        assert hasattr(Props, "transforms_list")
        assert hasattr(Props, "sedcmds")
        assert hasattr(Props, "kv")
        assert hasattr(Props, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_transform_model():
    """Test Transform model structure."""
    try:
        from app.models import Transform

        # Test model attributes
        assert hasattr(Transform, "__tablename__")
        assert Transform.__tablename__ == "transforms"
        assert hasattr(Transform, "id")
        assert hasattr(Transform, "run_id")
        assert hasattr(Transform, "name")
        assert hasattr(Transform, "dest_key")
        assert hasattr(Transform, "regex")
        assert hasattr(Transform, "format")
        assert hasattr(Transform, "writes_meta_index")
        assert hasattr(Transform, "writes_meta_sourcetype")
        assert hasattr(Transform, "kv")
        assert hasattr(Transform, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_index_model():
    """Test Index model structure."""
    try:
        from app.models import Index

        # Test model attributes
        assert hasattr(Index, "__tablename__")
        assert Index.__tablename__ == "indexes"
        assert hasattr(Index, "id")
        assert hasattr(Index, "run_id")
        assert hasattr(Index, "name")
        assert hasattr(Index, "kv")
        assert hasattr(Index, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_output_model():
    """Test Output model structure."""
    try:
        from app.models import Output

        # Test model attributes
        assert hasattr(Output, "__tablename__")
        assert Output.__tablename__ == "outputs"
        assert hasattr(Output, "id")
        assert hasattr(Output, "run_id")
        assert hasattr(Output, "group_name")
        assert hasattr(Output, "servers")
        assert hasattr(Output, "kv")
        assert hasattr(Output, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_serverclass_model():
    """Test Serverclass model structure."""
    try:
        from app.models import Serverclass

        # Test model attributes
        assert hasattr(Serverclass, "__tablename__")
        assert Serverclass.__tablename__ == "serverclasses"
        assert hasattr(Serverclass, "id")
        assert hasattr(Serverclass, "run_id")
        assert hasattr(Serverclass, "name")
        assert hasattr(Serverclass, "whitelist")
        assert hasattr(Serverclass, "blacklist")
        assert hasattr(Serverclass, "app_assignments")
        assert hasattr(Serverclass, "kv")
        assert hasattr(Serverclass, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")


def test_milestone2_relationships():
    """Test that Milestone 2 model relationships are correctly defined."""
    try:
        from app.models import (
            Index,
            IngestionRun,
            Input,
            Output,
            Props,
            Serverclass,
            Stanza,
            Transform,
        )

        # Check IngestionRun has all new relationships
        assert hasattr(IngestionRun, "stanzas")
        assert hasattr(IngestionRun, "inputs")
        assert hasattr(IngestionRun, "props")
        assert hasattr(IngestionRun, "transforms")
        assert hasattr(IngestionRun, "indexes")
        assert hasattr(IngestionRun, "outputs")
        assert hasattr(IngestionRun, "serverclasses")

        # Check all typed models have ingestion_run relationship
        assert hasattr(Stanza, "ingestion_run")
        assert hasattr(Input, "ingestion_run")
        assert hasattr(Props, "ingestion_run")
        assert hasattr(Transform, "ingestion_run")
        assert hasattr(Index, "ingestion_run")
        assert hasattr(Output, "ingestion_run")
        assert hasattr(Serverclass, "ingestion_run")

    except ImportError as e:
        pytest.skip(f"SQLAlchemy not installed: {e}")

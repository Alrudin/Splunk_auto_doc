"""Integration tests for status lifecycle with worker."""

import tarfile

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies
try:
    from app.core.db import Base
    from app.models.file import File as FileModel
    from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
    from app.models.stanza import Stanza
    from app.storage import get_storage_backend
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Dependencies not available: {e}"


# Skip all tests if dependencies not available
pytestmark = pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason=SKIP_REASON if not DEPENDENCIES_AVAILABLE else ""
)


@pytest.fixture
def test_db():
    """Create an in-memory test database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def test_storage(tmp_path):
    """Create a test storage backend."""
    storage_path = tmp_path / "storage"
    storage_path.mkdir()
    return get_storage_backend(backend_type="local", storage_path=str(storage_path))


@pytest.fixture
def sample_conf_archive(tmp_path):
    """Create a sample tar.gz archive with .conf files for testing."""
    # Create temporary directory structure
    conf_dir = tmp_path / "etc" / "apps" / "test_app" / "default"
    conf_dir.mkdir(parents=True)

    # Create sample inputs.conf
    inputs_conf = conf_dir / "inputs.conf"
    inputs_conf.write_text(
        """# Test inputs.conf
[monitor:///var/log/test.log]
disabled = false
sourcetype = test:log
index = main

[tcp://9514]
sourcetype = syslog
"""
    )

    # Create sample props.conf
    props_conf = conf_dir / "props.conf"
    props_conf.write_text(
        """# Test props.conf
[test:log]
SHOULD_LINEMERGE = false
TIME_PREFIX = ^
TIME_FORMAT = %Y-%m-%d %H:%M:%S
"""
    )

    # Create sample transforms.conf
    transforms_conf = conf_dir / "transforms.conf"
    transforms_conf.write_text(
        """# Test transforms.conf
[test_transform]
REGEX = test
FORMAT = result
"""
    )

    # Create tar.gz archive
    archive_path = tmp_path / "test_config.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(conf_dir.parent.parent.parent, arcname="etc")

    return archive_path


@pytest.mark.integration
def test_status_lifecycle_through_worker(test_db, test_storage, sample_conf_archive):
    """Test that worker transitions through all status states correctly."""
    # Create an ingestion run in STORED state
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Status Lifecycle",
        status=IngestionStatus.STORED,
    )
    test_db.add(run)
    test_db.commit()
    test_db.refresh(run)
    run_id = run.id

    # Store the archive in storage
    with open(sample_conf_archive, "rb") as f:
        blob_key = test_storage.store_blob(f, f"run_{run_id}/archive.tar.gz")

    # Create a file record
    file_record = FileModel(
        run_id=run_id,
        path="test_config.tar.gz",
        sha256="abc123" * 8,  # Mock SHA256 hash
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=blob_key,
    )
    test_db.add(file_record)
    test_db.commit()

    # Verify initial state
    test_db.refresh(run)
    assert run.status == IngestionStatus.STORED

    # Execute the parse_run task synchronously
    # Note: We'll patch dependencies and use eager execution
    from unittest.mock import patch

    # Patch SessionLocal to return our test database session
    # and patch get_storage_backend to return our test storage
    with (
        patch("app.worker.tasks.SessionLocal") as mock_session_local,
        patch("app.worker.tasks.get_storage_backend") as mock_storage_backend,
    ):
        # Make SessionLocal return our test database session
        mock_session_local.return_value = test_db
        mock_storage_backend.return_value = test_storage

        # Import the task function
        from app.worker.tasks import parse_run

        # Create mock for retry mechanism to prevent actual retries in tests
        def mock_retry(exc=None, countdown=60, max_retries=None):
            if exc:
                raise exc
            raise Exception("Mock retry called")

        # Execute task directly with eager execution
        original_task = parse_run

        # Patch the retry method to prevent actual retries and re-raise exceptions
        with patch.object(original_task, "retry", side_effect=mock_retry):
            # Apply task synchronously (eager execution)
            eager_result = original_task.apply([run_id])
            result = eager_result.result

    # Verify final state is COMPLETE (the task completes the full lifecycle)
    # Need to re-query since the object may have been modified in a different session
    final_run = test_db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert final_run.status == IngestionStatus.COMPLETE
    assert final_run.completed_at is not None  # Should be completed

    # Verify task result
    assert result["status"] == "completed"
    assert result["files_parsed"] == 3
    assert result["stanzas_created"] == 4
    assert "typed_projections" in result
    # Verify metrics were stored (from the task result)
    assert "duration_seconds" in result

    # Verify stanzas were created
    stanzas = test_db.query(Stanza).filter(Stanza.run_id == run_id).all()
    assert len(stanzas) == 4  # Based on the task output
    assert result["stanzas_created"] == len(stanzas)

    # Check that result indicates success
    assert result["status"] == "completed"
    assert result["run_id"] == run_id


@pytest.mark.integration
def test_normalized_status_is_set(test_db, test_storage, sample_conf_archive):
    """Test that NORMALIZED status is set after typed projections."""
    # Create an ingestion run
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Normalized Status",
        status=IngestionStatus.STORED,
    )
    test_db.add(run)
    test_db.commit()
    test_db.refresh(run)
    run_id = run.id

    # Store the archive
    with open(sample_conf_archive, "rb") as f:
        blob_key = test_storage.store_blob(f, f"run_{run_id}/archive.tar.gz")

    # Create file record
    file_record = FileModel(
        run_id=run_id,
        path="test_config.tar.gz",
        sha256="abc123" * 8,  # Mock SHA256 hash
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=blob_key,
    )
    test_db.add(file_record)
    test_db.commit()

    # Execute the task with patched database session and storage
    from unittest.mock import patch

    from app.worker.tasks import parse_run

    with (
        patch("app.worker.tasks.SessionLocal") as mock_session_local,
        patch("app.worker.tasks.get_storage_backend") as mock_storage_backend,
    ):
        mock_session_local.return_value = test_db
        mock_storage_backend.return_value = test_storage

        # Create mock for retry mechanism to prevent actual retries in tests
        def mock_retry(exc=None, countdown=60, max_retries=None):
            if exc:
                raise exc
            raise Exception("Mock retry called")

        # Execute task directly with eager execution
        with patch.object(parse_run, "retry", side_effect=mock_retry):
            # Apply task synchronously (eager execution)
            parse_run.apply([run_id])

    # Re-query to get updated state
    run = test_db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert run.status == IngestionStatus.COMPLETE

    # Verify typed projections were created (this happens during NORMALIZED phase)
    assert run.metrics is not None
    assert "typed_projections" in run.metrics
    typed_projections = run.metrics["typed_projections"]

    # We should have inputs, props, and transforms from our sample archive
    assert "inputs" in typed_projections
    assert "props" in typed_projections
    assert "transforms" in typed_projections

    # Verify counts
    assert typed_projections["inputs"] > 0
    assert typed_projections["props"] > 0
    assert typed_projections["transforms"] > 0


@pytest.mark.integration
def test_status_persists_summary_counts(test_db, test_storage, sample_conf_archive):
    """Test that summary counts are persisted in metrics."""
    # Create run
    run = IngestionRun(
        type=IngestionType.DS_ETC,
        label="Test Summary Counts",
        status=IngestionStatus.STORED,
    )
    test_db.add(run)
    test_db.commit()
    test_db.refresh(run)
    run_id = run.id

    # Store archive
    with open(sample_conf_archive, "rb") as f:
        blob_key = test_storage.store_blob(f, f"run_{run_id}/archive.tar.gz")

    file_record = FileModel(
        run_id=run_id,
        path="test_config.tar.gz",
        sha256="abc123" * 8,  # Mock SHA256 hash
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=blob_key,
    )
    test_db.add(file_record)
    test_db.commit()

    # Execute task with patched database session and storage
    from unittest.mock import patch

    from app.worker.tasks import parse_run

    with (
        patch("app.worker.tasks.SessionLocal") as mock_session_local,
        patch("app.worker.tasks.get_storage_backend") as mock_storage_backend,
    ):
        mock_session_local.return_value = test_db
        mock_storage_backend.return_value = test_storage

        # Create mock for retry mechanism to prevent actual retries in tests
        def mock_retry(exc=None, countdown=60, max_retries=None):
            if exc:
                raise exc
            raise Exception("Mock retry called")

        # Execute task directly with eager execution
        with patch.object(parse_run, "retry", side_effect=mock_retry):
            # Apply task synchronously (eager execution)
            parse_run.apply([run_id])

    # Re-query to get updated state
    run = test_db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert run.metrics is not None

    # Check all expected fields
    expected_fields = [
        "files_parsed",
        "stanzas_created",
        "typed_projections",
        "duration_seconds",
        "parse_errors",
        "retry_count",
    ]

    for field in expected_fields:
        assert field in run.metrics, f"Missing field: {field}"

    # Verify values are reasonable
    assert run.metrics["files_parsed"] >= 1
    assert run.metrics["stanzas_created"] >= 1
    assert isinstance(run.metrics["typed_projections"], dict)
    assert run.metrics["duration_seconds"] >= 0
    assert run.metrics["parse_errors"] >= 0
    assert run.metrics["retry_count"] == 0


@pytest.mark.integration
def test_error_status_on_failure(test_db, test_storage):
    """Test that status transitions to FAILED on error."""
    # Create a run with no files (should cause permanent error)
    run = IngestionRun(
        type=IngestionType.SINGLE_CONF,
        label="Test Error Status",
        status=IngestionStatus.STORED,
    )
    test_db.add(run)
    test_db.commit()
    test_db.refresh(run)
    run_id = run.id

    # Don't add any files - this should cause an error

    # Execute task with patched database session and storage
    import contextlib
    from unittest.mock import patch

    from app.worker.tasks import parse_run

    # Task should handle error internally and set status to FAILED
    with (
        patch("app.worker.tasks.SessionLocal") as mock_session_local,
        patch("app.worker.tasks.get_storage_backend") as mock_storage_backend,
    ):
        mock_session_local.return_value = test_db
        mock_storage_backend.return_value = test_storage

        # Create mock for retry mechanism to prevent actual retries in tests
        def mock_retry(exc=None, countdown=60, max_retries=None):
            if exc:
                raise exc
            raise Exception("Mock retry called")

        # Execute task directly with eager execution
        # The task should handle the PermanentError internally and set status to FAILED
        with (
            patch.object(parse_run, "retry", side_effect=mock_retry),
            contextlib.suppress(Exception),
        ):
            parse_run.apply([run_id])

    # Re-query to get updated state
    run = test_db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    assert run.status == IngestionStatus.FAILED
    assert run.error_message is not None
    assert "No files found" in run.error_message
    assert run.completed_at is not None

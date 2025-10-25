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
    from app.worker.tasks import parse_run
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
    """Create an in-memory test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


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


def create_test_task(test_db, task_id="test-task-id"):
    """Helper to create a DatabaseTask for testing.

    Args:
        test_db: Test database session
        task_id: Mock Celery task ID

    Returns:
        DatabaseTask instance ready for testing
    """
    from app.worker.tasks import DatabaseTask

    task = DatabaseTask()
    task._db = test_db

    # Mock the request object that Celery would provide
    class MockRequest:
        id = task_id
        retries = 0

    task.request = MockRequest()
    return task


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
        size=sample_conf_archive.stat().st_size,
        stored_object_key=blob_key,
    )
    test_db.add(file_record)
    test_db.commit()

    # Verify initial state
    test_db.refresh(run)
    assert run.status == IngestionStatus.STORED

    # Execute the parse_run task synchronously
    # Note: We're calling the task function directly instead of using celery
    # to avoid needing a running celery worker for tests
    task = create_test_task(test_db, "test-task-id")

    # Execute the task
    result = parse_run(task, run_id)

    # Verify final state is COMPLETE
    test_db.refresh(run)
    assert run.status == IngestionStatus.COMPLETE
    assert run.completed_at is not None

    # Verify metrics were stored
    assert run.metrics is not None
    assert "files_parsed" in run.metrics
    assert "stanzas_created" in run.metrics
    assert "typed_projections" in run.metrics
    assert run.metrics["files_parsed"] > 0
    assert run.metrics["stanzas_created"] > 0

    # Verify stanzas were created
    stanzas = test_db.query(Stanza).filter(Stanza.run_id == run_id).all()
    assert len(stanzas) > 0
    assert run.metrics["stanzas_created"] == len(stanzas)

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
        size=sample_conf_archive.stat().st_size,
        stored_object_key=blob_key,
    )
    test_db.add(file_record)
    test_db.commit()

    # Execute task to verify normalized status and typed projections
    task = create_test_task(test_db, "test-task-id-normalized")

    # Execute the task
    parse_run(task, run_id)

    # Check final status
    test_db.refresh(run)
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
        size=sample_conf_archive.stat().st_size,
        stored_object_key=blob_key,
    )
    test_db.add(file_record)
    test_db.commit()

    # Execute task
    task = create_test_task(test_db, "test-task-id-summary")

    parse_run(task, run_id)

    # Verify summary counts are in metrics
    test_db.refresh(run)
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

    # Execute task
    from app.worker.exceptions import PermanentError

    task = create_test_task(test_db, "test-task-id-error")

    # Task should raise PermanentError
    with pytest.raises(PermanentError):
        parse_run(task, run_id)

    # Verify status was set to FAILED
    test_db.refresh(run)
    assert run.status == IngestionStatus.FAILED
    assert run.error_message is not None
    assert "No files found" in run.error_message
    assert run.completed_at is not None

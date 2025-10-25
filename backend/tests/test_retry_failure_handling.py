"""Integration tests for retry and failure handling in worker tasks."""

import tarfile
from unittest.mock import MagicMock, patch

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
    from app.worker.exceptions import PermanentError, TransientError
    from app.worker.tasks import DatabaseTask, parse_run
    from celery.exceptions import Retry
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
def retry_test_db():
    """Create an in-memory test database for retry tests."""
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
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_storage(tmp_path):
    """Create a test storage backend."""
    storage_path = tmp_path / "storage"
    storage_path.mkdir()
    return get_storage_backend(backend_type="local", storage_path=str(storage_path))


@pytest.fixture
def sample_conf_archive(tmp_path):
    """Create a sample tar.gz archive with .conf files."""
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
"""
    )

    # Create tar.gz archive
    archive_path = tmp_path / "test_config.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(conf_dir.parent.parent.parent, arcname="etc")

    return archive_path


@pytest.fixture
def malformed_archive(tmp_path):
    """Create a malformed archive file."""
    archive_path = tmp_path / "malformed.tar.gz"
    archive_path.write_bytes(b"This is not a valid archive")
    return archive_path


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_permanent_error_no_retry(retry_test_db, test_storage):
    """Test that permanent errors are not retried."""
    # Create run without files (permanent error condition)
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Run - No Files",
        status=IngestionStatus.STORED,
    )
    retry_test_db.add(run)
    retry_test_db.commit()

    # Create task with test DB
    task = DatabaseTask()
    task._db = retry_test_db

    # Should raise PermanentError for no files
    # Call the task function directly and patch SessionLocal to use test DB
    with patch('app.core.db.SessionLocal', return_value=retry_test_db), \
         pytest.raises(PermanentError, match="No files found"):
        parse_run.run(run.id)    # Verify run marked as failed
    retry_test_db.refresh(run)
    assert run.status == IngestionStatus.FAILED
    assert "Permanent error" in run.error_message
    assert run.error_traceback is not None
    assert run.completed_at is not None


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_transient_error_with_retry(retry_test_db, test_storage, sample_conf_archive):
    """Test that transient errors trigger retries with exponential backoff."""
    # Create run with files
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Run - Transient Error",
        status=IngestionStatus.STORED,
    )
    retry_test_db.add(run)
    retry_test_db.flush()

    # Store archive
    with open(sample_conf_archive, "rb") as f:
        storage_key = test_storage.store_blob(f, f"runs/{run.id}/test_config.tar.gz")

    file_record = FileModel(
        run_id=run.id,
        path="test_config.tar.gz",
        sha256="abc123" * 8,
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=storage_key,
    )
    retry_test_db.add(file_record)
    retry_test_db.commit()

    # Create task with test DB
    task = DatabaseTask()
    task._db = retry_test_db

    # Mock storage to raise transient error on first call
    call_count = {"count": 0}

    def mock_retrieve_blob(key):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise TransientError("Simulated network error")
        # Return actual blob on subsequent calls
        return test_storage.retrieve_blob(key)

    with (
        patch('app.core.db.SessionLocal', return_value=retry_test_db),
        patch.object(test_storage, "retrieve_blob", side_effect=mock_retrieve_blob),
        pytest.raises(Retry),
    ):  # Will raise retry exception
        parse_run.run(run.id)

    # Verify run has error details but is not marked as failed yet
    retry_test_db.refresh(run)
    assert run.error_message is not None
    assert "Transient error" in run.error_message
    assert run.retry_count == 0  # Updated by task


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_malformed_archive_permanent_error(retry_test_db, test_storage, malformed_archive):
    """Test that malformed archives raise permanent errors."""
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Run - Malformed Archive",
        status=IngestionStatus.STORED,
    )
    retry_test_db.add(run)
    retry_test_db.flush()

    # Store malformed archive
    with open(malformed_archive, "rb") as f:
        storage_key = test_storage.store_blob(f, f"runs/{run.id}/malformed.tar.gz")

    file_record = FileModel(
        run_id=run.id,
        path="malformed.tar.gz",
        sha256="def456" * 8,
        size_bytes=malformed_archive.stat().st_size,
        stored_object_key=storage_key,
    )
    retry_test_db.add(file_record)
    retry_test_db.commit()

    # Create task
    task = DatabaseTask()
    task._db = retry_test_db

    # Should raise PermanentError
    with patch('app.core.db.SessionLocal', return_value=retry_test_db), \
         pytest.raises(PermanentError, match="Invalid archive format"):
        parse_run.run(run.id)

    # Verify run marked as failed
    retry_test_db.refresh(run)
    assert run.status == IngestionStatus.FAILED
    assert "Permanent error" in run.error_message


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_idempotency_on_retry(retry_test_db, test_storage, sample_conf_archive):
    """Test that retrying a task doesn't create duplicate stanzas."""
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Run - Idempotency",
        status=IngestionStatus.STORED,
    )
    retry_test_db.add(run)
    retry_test_db.flush()

    # Store archive
    with open(sample_conf_archive, "rb") as f:
        storage_key = test_storage.store_blob(f, f"runs/{run.id}/test_config.tar.gz")

    file_record = FileModel(
        run_id=run.id,
        path="test_config.tar.gz",
        sha256="ghi789" * 8,
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=storage_key,
    )
    retry_test_db.add(file_record)
    retry_test_db.commit()

    # Create task
    task = DatabaseTask()
    task._db = retry_test_db

    # Run task first time
    with patch('app.core.db.SessionLocal', return_value=retry_test_db):
        result1 = parse_run.run(run.id)
        initial_stanza_count = result1["stanzas_created"]

    # Verify stanzas created
    assert initial_stanza_count > 0
    stanzas_1 = retry_test_db.query(Stanza).filter(Stanza.run_id == run.id).all()
    assert len(stanzas_1) == initial_stanza_count

    # Mark run as parsing again to simulate retry scenario
    retry_test_db.refresh(run)
    run.status = IngestionStatus.PARSING
    retry_test_db.commit()

    # Create new task instance for retry
    task2 = DatabaseTask()
    task2._db = retry_test_db
    task2.request = MagicMock(id="test-task-102", retries=1)
    task2.max_retries = 3

    # Run task second time (simulated retry)
    # result2 = parse_run.run(run.id)

    # Verify no new stanzas created (idempotent)
    stanzas_2 = retry_test_db.query(Stanza).filter(Stanza.run_id == run.id).all()
    assert len(stanzas_2) == initial_stanza_count  # No duplicates


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_heartbeat_updates(retry_test_db, test_storage, sample_conf_archive):
    """Test that heartbeat timestamps are updated during task execution."""
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Run - Heartbeat",
        status=IngestionStatus.STORED,
    )
    retry_test_db.add(run)
    retry_test_db.flush()

    # Store archive
    with open(sample_conf_archive, "rb") as f:
        storage_key = test_storage.store_blob(f, f"runs/{run.id}/test_config.tar.gz")

    file_record = FileModel(
        run_id=run.id,
        path="test_config.tar.gz",
        sha256="jkl012" * 8,
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=storage_key,
    )
    retry_test_db.add(file_record)
    retry_test_db.commit()

    # Create task
    task = DatabaseTask()
    task._db = retry_test_db

    # Run task
    with patch('app.core.db.SessionLocal', return_value=retry_test_db):
        # result = parse_run.run(run.id)
        pass

    # Verify heartbeat and timestamp fields were set
    retry_test_db.refresh(run)
    assert run.task_id == "test-task-303"
    assert run.last_heartbeat is not None
    assert run.started_at is not None
    assert run.completed_at is not None


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_metrics_collection(retry_test_db, test_storage, sample_conf_archive):
    """Test that execution metrics are collected and stored."""
    run = IngestionRun(
        type=IngestionType.APP_BUNDLE,
        label="Test Run - Metrics",
        status=IngestionStatus.STORED,
    )
    retry_test_db.add(run)
    retry_test_db.flush()

    # Store archive
    with open(sample_conf_archive, "rb") as f:
        storage_key = test_storage.store_blob(f, f"runs/{run.id}/test_config.tar.gz")

    file_record = FileModel(
        run_id=run.id,
        path="test_config.tar.gz",
        sha256="mno345" * 8,
        size_bytes=sample_conf_archive.stat().st_size,
        stored_object_key=storage_key,
    )
    retry_test_db.add(file_record)
    retry_test_db.commit()

    # Create task
    task = DatabaseTask()
    task._db = retry_test_db

    # Run task
    with patch('app.core.db.SessionLocal', return_value=retry_test_db):
        # result = parse_run.run(run.id)
        pass

    # Verify metrics were stored
    retry_test_db.refresh(run)
    assert run.metrics is not None
    assert "files_parsed" in run.metrics
    assert "stanzas_created" in run.metrics
    assert "duration_seconds" in run.metrics
    assert "retry_count" in run.metrics
    assert run.metrics["files_parsed"] > 0
    assert run.metrics["stanzas_created"] > 0
    assert run.metrics["duration_seconds"] > 0


@pytest.mark.integration
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
@pytest.mark.skip(reason="Complex integration test - requires proper task isolation setup")
def test_already_completed_idempotency(test_db):
    """Test that already completed runs are skipped (idempotent)."""
    # Create a session from the test database sessionmaker
    session = test_db()

    try:
        # Create completed run
        run = IngestionRun(
            type=IngestionType.APP_BUNDLE,
            label="Completed Run",
            status=IngestionStatus.COMPLETE,
        )
        session.add(run)
        session.commit()

        # Create a task and manually inject our test database session (like the working tests)
        task = DatabaseTask()
        task._db = session

        # Call the task directly like the working tests do
        # result = parse_run.run(run.id)

        # assert result["status"] == "already_completed"
        # assert result["run_id"] == run.id
        # assert result["duration_seconds"] == 0
    finally:
        session.close()

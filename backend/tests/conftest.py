"""Shared pytest fixtures for all tests."""

import io
import tempfile
from collections.abc import Generator

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies, skip tests if not available
try:
    from app.api.v1.uploads import get_storage
    from app.core.db import Base, get_db
    from app.main import create_app
    from app.storage import get_storage_backend
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Dependencies not available: {e}"


@pytest.fixture(scope="function")
def test_db() -> Generator:
    """Create a test database with all models registered.

    Uses in-memory SQLite for fast, isolated testing.
    Each test gets a fresh database instance.
    """
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Import models explicitly to ensure they are registered with Base metadata
    # This MUST happen before create_all() is called
    # Also import the models package to ensure __init__.py runs
    import app.models  # noqa: F401
    from app.models.file import File  # noqa: F401
    from app.models.index import Index  # noqa: F401
    from app.models.ingestion_run import IngestionRun  # noqa: F401
    from app.models.input import Input  # noqa: F401
    from app.models.output import Output  # noqa: F401
    from app.models.props import Props  # noqa: F401
    from app.models.serverclass import Serverclass  # noqa: F401
    from app.models.stanza import Stanza  # noqa: F401
    from app.models.transform import Transform  # noqa: F401

    # Create an in-memory SQLite database engine
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,  # Use StaticPool to ensure same connection across threads
        pool_pre_ping=True,
    )

    # Verify models are registered before creating tables
    if not Base.metadata.tables:
        raise RuntimeError(
            "No tables found in Base.metadata - models not properly imported"
        )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Verify tables were actually created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "ingestion_runs" not in tables:
        raise RuntimeError(
            f"ingestion_runs table not created. Available tables: {tables}"
        )

    # Create a session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    # Clean up
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_storage() -> Generator:
    """Create a test storage backend using temporary directory.

    Automatically cleaned up after test completes.
    """
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = get_storage_backend(backend_type="local", storage_path=tmpdir)
        yield storage


@pytest.fixture(scope="function")
def db_session(test_db) -> Generator:
    """Provide a database session for tests.

    Useful for tests that need direct database access without FastAPI.
    """
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db, test_storage) -> Generator:
    """Create a FastAPI test client with overridden dependencies.

    Database and storage backends are replaced with test versions.
    """
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    app = create_app()

    # Override database dependency
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    # Override storage dependency
    def override_get_storage():
        return test_storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_tar_file() -> io.BytesIO:
    """Create a sample tar.gz file for upload tests."""
    content = b"Sample Splunk configuration content\n"
    return io.BytesIO(content)


@pytest.fixture
def sample_upload_metadata() -> dict:
    """Provide sample metadata for upload tests."""
    return {
        "ingestion_type": "instance_etc",
        "label": "Test Upload",
        "notes": "Test notes for upload",
    }


@pytest.fixture
def large_file() -> io.BytesIO:
    """Create a large file (5MB) for performance testing."""
    size_mb = 5
    content = b"x" * (size_mb * 1024 * 1024)
    return io.BytesIO(content)


@pytest.fixture
def sample_files() -> list[tuple[str, bytes]]:
    """Provide multiple sample files for batch testing."""
    return [
        ("config1.tar.gz", b"Config file 1 content"),
        ("config2.tar.gz", b"Config file 2 content"),
        ("config3.tar.gz", b"Config file 3 content"),
    ]

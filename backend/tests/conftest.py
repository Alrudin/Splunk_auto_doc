"""Shared pytest fixtures for all tests."""

import io
import tempfile
from typing import Generator

import pytest

# Try to import dependencies, skip tests if not available
try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    from app.core.db import Base, get_db
    from app.main import create_app
    from app.storage import get_storage_backend
    from app.api.v1.uploads import get_storage

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

    # Import all models to ensure they are registered with Base metadata
    import app.models  # noqa: F401

    # Use in-memory SQLite for testing with check_same_thread=False
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(engine)


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
def db_session(test_db) -> Generator[Session, None, None]:
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
def client(test_db, test_storage) -> Generator[TestClient, None, None]:
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

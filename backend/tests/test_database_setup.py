"""Test database setup and model registration for debugging CI issues."""

import pytest

# Ensure all models are imported first
import tests.ensure_models  # noqa: F401

# Try to import dependencies, skip tests if not available
try:
    from app.core.db import Base
    from app.models.file import File
    from app.models.ingestion_run import IngestionRun, IngestionStatus, IngestionType
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Dependencies not available: {e}"


def test_models_are_registered():
    """Test that all models are properly registered with SQLAlchemy Base metadata."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Check that models are registered in Base metadata
    registered_tables = list(Base.metadata.tables.keys())
    print(f"Registered tables: {registered_tables}")

    assert (
        "ingestion_runs" in registered_tables
    ), f"ingestion_runs not in {registered_tables}"
    assert "files" in registered_tables, f"files not in {registered_tables}"


def test_database_creation():
    """Test that database tables are created correctly."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip(SKIP_REASON)

    # Create test database
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,  # Set to True for SQL logging
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Verify models are in metadata before creating tables
    tables_before = list(Base.metadata.tables.keys())
    print(f"Tables in metadata before create_all: {tables_before}")
    assert (
        "ingestion_runs" in tables_before
    ), f"ingestion_runs not in metadata: {tables_before}"
    assert "files" in tables_before, f"files not in metadata: {tables_before}"

    # Create all tables
    Base.metadata.create_all(engine)

    # Verify tables exist in database
    inspector = inspect(engine)
    actual_tables = inspector.get_table_names()
    print(f"Actual tables in database: {actual_tables}")

    assert (
        "ingestion_runs" in actual_tables
    ), f"ingestion_runs table not created: {actual_tables}"
    assert "files" in actual_tables, f"files table not created: {actual_tables}"

    # Test that we can create a session and use the models
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        # First create an ingestion run (required for foreign key)
        ingestion_run = IngestionRun(
            status=IngestionStatus.PENDING, type=IngestionType.APP_BUNDLE
        )
        session.add(ingestion_run)
        session.flush()  # Get the ID

        # Test basic model instantiation with correct column names
        file_obj = File(
            run_id=ingestion_run.id,
            path="test.csv",
            sha256="a" * 64,  # 64 character hash
            size_bytes=1000,
            stored_object_key="s3://bucket/test_123.csv",
        )
        session.add(file_obj)
        session.commit()

        # Verify we can query
        files = session.query(File).all()
        assert len(files) == 1
        assert files[0].path == "test.csv"

        print("✓ Database setup and model operations successful")


if __name__ == "__main__":
    # Allow running this test directly
    test_models_are_registered()
    test_database_creation()
    print("All database setup tests passed!")

#!/usr/bin/env python3
"""Test script to verify database migration works correctly."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402


def test_migration():
    """Test that migration creates expected tables and columns."""
    settings = get_settings()

    print(f"Testing database connection: {settings.database_url.split('@')[1]}")

    try:
        engine = create_engine(settings.database_url, echo=True)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL: {version}")

        # Inspect tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\n✓ Found {len(tables)} tables: {tables}")

        # Check ingestion_runs table
        if "ingestion_runs" not in tables:
            print("✗ Table 'ingestion_runs' not found!")
            return False

        print("\n✓ Table 'ingestion_runs' exists")
        ingestion_runs_columns = [
            col["name"] for col in inspector.get_columns("ingestion_runs")
        ]
        print(f"  Columns: {ingestion_runs_columns}")

        expected_columns = ["id", "created_at", "type", "label", "status", "notes"]
        for col in expected_columns:
            if col in ingestion_runs_columns:
                print(f"  ✓ Column '{col}' exists")
            else:
                print(f"  ✗ Column '{col}' missing!")
                return False

        # Check indexes on ingestion_runs
        ingestion_runs_indexes = inspector.get_indexes("ingestion_runs")
        print(f"  Indexes: {[idx['name'] for idx in ingestion_runs_indexes]}")

        # Check files table
        if "files" not in tables:
            print("\n✗ Table 'files' not found!")
            return False

        print("\n✓ Table 'files' exists")
        files_columns = [col["name"] for col in inspector.get_columns("files")]
        print(f"  Columns: {files_columns}")

        expected_files_columns = [
            "id",
            "run_id",
            "path",
            "sha256",
            "size_bytes",
            "stored_object_key",
        ]
        for col in expected_files_columns:
            if col in files_columns:
                print(f"  ✓ Column '{col}' exists")
            else:
                print(f"  ✗ Column '{col}' missing!")
                return False

        # Check foreign key
        files_fks = inspector.get_foreign_keys("files")
        print(f"  Foreign Keys: {files_fks}")
        if files_fks:
            print("  ✓ Foreign key to ingestion_runs exists")
        else:
            print("  ✗ Foreign key missing!")
            return False

        # Check indexes on files
        files_indexes = inspector.get_indexes("files")
        print(f"  Indexes: {[idx['name'] for idx in files_indexes]}")

        print("\n✅ All migration checks passed!")
        return True

    except Exception as e:
        print(f"\n✗ Error testing migration: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)

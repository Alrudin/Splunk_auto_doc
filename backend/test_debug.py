#!/usr/bin/env python3
"""Debug test for database table creation issue."""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting debug test...")

try:
    # Test basic imports
    print("1. Testing basic imports...")
    from app.core.db import Base

    print(f"   Base imported: {Base}")

    # Test model imports
    print("2. Testing model imports...")
    from app.models.file import File
    from app.models.ingestion_run import IngestionRun

    print(f"   Models imported: IngestionRun={IngestionRun}, File={File}")

    # Check Base metadata
    print("3. Checking Base metadata...")
    print(f"   Base metadata tables: {list(Base.metadata.tables.keys())}")

    # Test database creation
    print("4. Testing database creation...")
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True,
    )

    print("   Engine created")

    # Create tables
    print("   Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Check what tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   Created tables: {tables}")

    # Test session creation
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    print(f"   Session created: {session}")

    # Test query (should work now)
    try:
        count = session.query(IngestionRun).count()
        print(f"   Query successful, count: {count}")
    except Exception as e:
        print(f"   Query failed: {e}")

    session.close()
    print("5. Test completed successfully!")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

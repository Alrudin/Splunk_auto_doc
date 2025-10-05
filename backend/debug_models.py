#!/usr/bin/env python3
"""Debug script to check model imports and metadata."""

# Import all models to ensure they are registered with Base metadata
from app.core.db import Base

print("Available tables in Base.metadata:")
for table_name, table in Base.metadata.tables.items():
    print(f"  - {table_name}: {table}")
    print(f"    Columns: {[col.name for col in table.columns]}")

print(f"\nTotal tables: {len(Base.metadata.tables)}")

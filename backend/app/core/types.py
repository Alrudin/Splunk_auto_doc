"""Custom database types for cross-database compatibility."""

from typing import Any

from sqlalchemy import JSON, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PostgreSQLJSONB
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON


class JSONB(TypeDecorator[dict[str, Any]]):
    """A cross-database compatible JSONB type.

    Uses PostgreSQL JSONB for PostgreSQL databases and JSON for others.
    Falls back to TEXT for databases that don't support JSON.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """Load the appropriate implementation based on the database dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLJSONB())
        elif dialect.name == "sqlite":
            # SQLite supports JSON as of version 3.38, but fallback to TEXT for compatibility
            try:
                return dialect.type_descriptor(SQLiteJSON())
            except AttributeError:
                return dialect.type_descriptor(Text())
        else:
            # For other databases, try JSON, fallback to TEXT
            try:
                return dialect.type_descriptor(JSON())
            except Exception:
                return dialect.type_descriptor(Text())


class ARRAY(TypeDecorator[list[Any]]):
    """A cross-database compatible ARRAY type.

    Uses PostgreSQL ARRAY for PostgreSQL databases and JSON for others.
    Falls back to TEXT for databases that don't support JSON.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """Load the appropriate implementation based on the database dialect."""
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY as PostgreSQLARRAY

            return dialect.type_descriptor(PostgreSQLARRAY(Text))
        elif dialect.name == "sqlite":
            # Store arrays as JSON in SQLite
            try:
                return dialect.type_descriptor(SQLiteJSON())
            except AttributeError:
                return dialect.type_descriptor(Text())
        else:
            # For other databases, try JSON, fallback to TEXT
            try:
                return dialect.type_descriptor(JSON())
            except Exception:
                return dialect.type_descriptor(Text())

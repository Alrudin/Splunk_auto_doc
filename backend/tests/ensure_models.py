"""
Ensure models are imported and registered with SQLAlchemy Base metadata.

This module should be imported early in test runs to ensure all models
are properly registered before any database operations.
"""

# Import all models to ensure they are registered with Base metadata
# This is critical for test databases to have all tables created

try:
    # Import individual model files
    # Import the models package
    import app.models  # noqa: F401

    # Import the Base to verify models are registered
    from app.core.db import Base
    from app.models.file import File  # noqa: F401
    from app.models.index import Index  # noqa: F401
    from app.models.ingestion_run import (  # noqa: F401
        IngestionRun,
        IngestionStatus,
        IngestionType,
    )
    from app.models.input import Input  # noqa: F401
    from app.models.output import Output  # noqa: F401
    from app.models.props import Props  # noqa: F401
    from app.models.serverclass import Serverclass  # noqa: F401
    from app.models.stanza import Stanza  # noqa: F401
    from app.models.transform import Transform  # noqa: F401

    # Verify models are registered
    _REGISTERED_TABLES = list(Base.metadata.tables.keys())

    # Milestone 1 tables
    if "ingestion_runs" not in _REGISTERED_TABLES:
        raise RuntimeError(
            f"ingestion_runs table not registered. Available: {_REGISTERED_TABLES}"
        )
    if "files" not in _REGISTERED_TABLES:
        raise RuntimeError(
            f"files table not registered. Available: {_REGISTERED_TABLES}"
        )

    # Milestone 2 tables
    milestone2_tables = [
        "stanzas",
        "inputs",
        "props",
        "transforms",
        "indexes",
        "outputs",
        "serverclasses",
    ]
    for table in milestone2_tables:
        if table not in _REGISTERED_TABLES:
            raise RuntimeError(
                f"{table} table not registered. Available: {_REGISTERED_TABLES}"
            )

    print(f"✓ Models successfully registered: {_REGISTERED_TABLES}")

except ImportError as e:
    print(f"⚠ Model import failed: {e}")
    _REGISTERED_TABLES = []

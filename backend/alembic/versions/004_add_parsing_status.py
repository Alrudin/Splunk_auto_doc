"""Add parsing status to ingestion runs

Revision ID: 004
Revises: 003
Create Date: 2025-10-23 16:31:00.000000

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add parsing status to IngestionStatus enum.

    Note: Since status is stored as a string (not a native enum),
    this migration is a no-op. The new 'parsing' status value
    will be automatically accepted by the database.

    This migration exists for documentation purposes to track
    the change in the IngestionStatus enum values.
    """
    # No-op: status field stores strings, so no schema change needed
    pass


def downgrade() -> None:
    """Remove parsing status support.

    Note: This does not remove existing 'parsing' status values
    from the database. Applications using the downgraded schema
    may encounter errors if they query runs with 'parsing' status.
    """
    # No-op: status field stores strings, so no schema change needed
    pass

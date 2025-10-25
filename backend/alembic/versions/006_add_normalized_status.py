"""Add normalized status to ingestion runs

Revision ID: 006
Revises: 005
Create Date: 2025-10-25 11:06:00.000000

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add normalized status to IngestionStatus enum.

    Note: Since status is stored as a string (not a native enum),
    this migration is a no-op. The new 'normalized' status value
    will be automatically accepted by the database.

    This migration exists for documentation purposes to track
    the change in the IngestionStatus enum values.

    The normalized status indicates that stanzas have been parsed
    and typed projections have been created, but final validation
    and summary metrics are still being computed.
    """
    # No-op: status field stores strings, so no schema change needed
    pass


def downgrade() -> None:
    """Remove normalized status support.

    Note: This does not remove existing 'normalized' status values
    from the database. Applications using the downgraded schema
    may encounter errors if they query runs with 'normalized' status.
    """
    # No-op: status field stores strings, so no schema change needed
    pass

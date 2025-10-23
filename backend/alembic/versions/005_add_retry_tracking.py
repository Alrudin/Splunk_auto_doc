"""Add retry and error tracking fields to ingestion runs

Revision ID: 005
Revises: 004
Create Date: 2025-10-23 18:52:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add retry tracking, error details, and metrics fields to ingestion_runs table."""
    # Add task tracking
    op.add_column(
        "ingestion_runs",
        sa.Column("task_id", sa.String(length=255), nullable=True),
    )

    # Add retry tracking
    op.add_column(
        "ingestion_runs",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # Add error details
    op.add_column(
        "ingestion_runs",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column("error_traceback", sa.Text(), nullable=True),
    )

    # Add timestamp tracking
    op.add_column(
        "ingestion_runs",
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add metrics tracking (JSON field)
    op.add_column(
        "ingestion_runs",
        sa.Column("metrics", sa.JSON(), nullable=True),
    )

    # Create index on task_id for faster lookups
    op.create_index(
        "idx_ingestion_runs_task_id",
        "ingestion_runs",
        ["task_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove retry tracking, error details, and metrics fields from ingestion_runs table."""
    op.drop_index("idx_ingestion_runs_task_id", table_name="ingestion_runs")
    op.drop_column("ingestion_runs", "metrics")
    op.drop_column("ingestion_runs", "completed_at")
    op.drop_column("ingestion_runs", "started_at")
    op.drop_column("ingestion_runs", "last_heartbeat")
    op.drop_column("ingestion_runs", "error_traceback")
    op.drop_column("ingestion_runs", "error_message")
    op.drop_column("ingestion_runs", "retry_count")
    op.drop_column("ingestion_runs", "task_id")

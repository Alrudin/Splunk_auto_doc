"""Add stanzas and typed configuration tables

Revision ID: 002
Revises: 001
Create Date: 2025-10-07 17:06:53.087608

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create stanzas and typed configuration tables."""
    # Create stanzas table
    op.create_table(
        "stanzas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("conf_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("app", sa.String(length=255), nullable=True),
        sa.Column("scope", sa.String(length=50), nullable=True),
        sa.Column("layer", sa.String(length=50), nullable=True),
        sa.Column("order_in_file", sa.Integer(), nullable=True),
        sa.Column("source_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "raw_kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create inputs table
    op.create_table(
        "inputs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("source_path", sa.String(length=1024), nullable=False),
        sa.Column("stanza_type", sa.String(length=255), nullable=True),
        sa.Column("index", sa.String(length=255), nullable=True),
        sa.Column("sourcetype", sa.String(length=255), nullable=True),
        sa.Column("disabled", sa.Boolean(), nullable=True),
        sa.Column(
            "kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("app", sa.String(length=255), nullable=True),
        sa.Column("scope", sa.String(length=50), nullable=True),
        sa.Column("layer", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create props table
    op.create_table(
        "props",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("target", sa.String(length=512), nullable=False),
        sa.Column(
            "transforms_list",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=True,
        ),
        sa.Column(
            "sedcmds",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=True,
        ),
        sa.Column(
            "kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create transforms table
    op.create_table(
        "transforms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("dest_key", sa.String(length=255), nullable=True),
        sa.Column("regex", sa.Text(), nullable=True),
        sa.Column("format", sa.Text(), nullable=True),
        sa.Column("writes_meta_index", sa.Boolean(), nullable=True),
        sa.Column("writes_meta_sourcetype", sa.Boolean(), nullable=True),
        sa.Column(
            "kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes table
    op.create_table(
        "indexes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create outputs table
    op.create_table(
        "outputs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("group_name", sa.String(length=255), nullable=False),
        sa.Column(
            "servers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create serverclasses table
    op.create_table(
        "serverclasses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "whitelist",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "blacklist",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "app_assignments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "kv",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop typed configuration and stanzas tables."""
    op.drop_table("serverclasses")
    op.drop_table("outputs")
    op.drop_table("indexes")
    op.drop_table("transforms")
    op.drop_table("props")
    op.drop_table("inputs")
    op.drop_table("stanzas")

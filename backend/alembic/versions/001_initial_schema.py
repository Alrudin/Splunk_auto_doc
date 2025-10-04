"""Initial schema: ingestion_runs and files tables

Revision ID: 001
Revises:
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ingestion_runs and files tables."""
    # Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on created_at for efficient queries
    op.create_index('ix_ingestion_runs_created_at', 'ingestion_runs', ['created_at'])

    # Create index on status for filtering
    op.create_index('ix_ingestion_runs_status', 'ingestion_runs', ['status'])

    # Create files table
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(length=1024), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('stored_object_key', sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(
            ['run_id'],
            ['ingestion_runs.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on run_id for efficient FK lookups
    op.create_index('ix_files_run_id', 'files', ['run_id'])

    # Create index on sha256 for deduplication checks
    op.create_index('ix_files_sha256', 'files', ['sha256'])


def downgrade() -> None:
    """Drop files and ingestion_runs tables."""
    op.drop_index('ix_files_sha256', table_name='files')
    op.drop_index('ix_files_run_id', table_name='files')
    op.drop_table('files')

    op.drop_index('ix_ingestion_runs_status', table_name='ingestion_runs')
    op.drop_index('ix_ingestion_runs_created_at', table_name='ingestion_runs')
    op.drop_table('ingestion_runs')

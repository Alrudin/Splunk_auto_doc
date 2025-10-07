"""Add performance indexes for stanzas and typed tables

Revision ID: 003
Revises: 002
Create Date: 2025-10-07 17:08:00.757164

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add indexes for query performance and JSONB search."""
    # B-tree indexes for stanzas table
    op.create_index(
        "ix_stanzas_run_id",
        "stanzas",
        ["run_id"],
    )
    op.create_index(
        "ix_stanzas_run_conf_name",
        "stanzas",
        ["run_id", "conf_type", "name"],
    )
    op.create_index(
        "ix_stanzas_run_app_scope_layer",
        "stanzas",
        ["run_id", "app", "scope", "layer"],
    )

    # GIN index for JSONB search on stanzas
    op.create_index(
        "ix_stanzas_raw_kv_gin",
        "stanzas",
        ["raw_kv"],
        postgresql_using="gin",
    )

    # B-tree indexes for inputs table
    op.create_index(
        "ix_inputs_run_id",
        "inputs",
        ["run_id"],
    )

    # GIN index for JSONB search on inputs
    op.create_index(
        "ix_inputs_kv_gin",
        "inputs",
        ["kv"],
        postgresql_using="gin",
    )

    # B-tree indexes for props table
    op.create_index(
        "ix_props_run_id",
        "props",
        ["run_id"],
    )

    # GIN index for JSONB search on props
    op.create_index(
        "ix_props_kv_gin",
        "props",
        ["kv"],
        postgresql_using="gin",
    )

    # B-tree indexes for transforms table
    op.create_index(
        "ix_transforms_run_id",
        "transforms",
        ["run_id"],
    )

    # GIN index for JSONB search on transforms
    op.create_index(
        "ix_transforms_kv_gin",
        "transforms",
        ["kv"],
        postgresql_using="gin",
    )

    # B-tree indexes for indexes table
    op.create_index(
        "ix_indexes_run_id",
        "indexes",
        ["run_id"],
    )

    # GIN index for JSONB search on indexes
    op.create_index(
        "ix_indexes_kv_gin",
        "indexes",
        ["kv"],
        postgresql_using="gin",
    )

    # B-tree indexes for outputs table
    op.create_index(
        "ix_outputs_run_id",
        "outputs",
        ["run_id"],
    )

    # GIN indexes for JSONB search on outputs
    op.create_index(
        "ix_outputs_servers_gin",
        "outputs",
        ["servers"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_outputs_kv_gin",
        "outputs",
        ["kv"],
        postgresql_using="gin",
    )

    # B-tree indexes for serverclasses table
    op.create_index(
        "ix_serverclasses_run_id",
        "serverclasses",
        ["run_id"],
    )

    # GIN indexes for JSONB search on serverclasses
    op.create_index(
        "ix_serverclasses_whitelist_gin",
        "serverclasses",
        ["whitelist"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_serverclasses_blacklist_gin",
        "serverclasses",
        ["blacklist"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_serverclasses_app_assignments_gin",
        "serverclasses",
        ["app_assignments"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_serverclasses_kv_gin",
        "serverclasses",
        ["kv"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Drop all performance indexes."""
    # Drop serverclasses indexes
    op.drop_index("ix_serverclasses_kv_gin", table_name="serverclasses")
    op.drop_index("ix_serverclasses_app_assignments_gin", table_name="serverclasses")
    op.drop_index("ix_serverclasses_blacklist_gin", table_name="serverclasses")
    op.drop_index("ix_serverclasses_whitelist_gin", table_name="serverclasses")
    op.drop_index("ix_serverclasses_run_id", table_name="serverclasses")

    # Drop outputs indexes
    op.drop_index("ix_outputs_kv_gin", table_name="outputs")
    op.drop_index("ix_outputs_servers_gin", table_name="outputs")
    op.drop_index("ix_outputs_run_id", table_name="outputs")

    # Drop indexes table indexes
    op.drop_index("ix_indexes_kv_gin", table_name="indexes")
    op.drop_index("ix_indexes_run_id", table_name="indexes")

    # Drop transforms indexes
    op.drop_index("ix_transforms_kv_gin", table_name="transforms")
    op.drop_index("ix_transforms_run_id", table_name="transforms")

    # Drop props indexes
    op.drop_index("ix_props_kv_gin", table_name="props")
    op.drop_index("ix_props_run_id", table_name="props")

    # Drop inputs indexes
    op.drop_index("ix_inputs_kv_gin", table_name="inputs")
    op.drop_index("ix_inputs_run_id", table_name="inputs")

    # Drop stanzas indexes
    op.drop_index("ix_stanzas_raw_kv_gin", table_name="stanzas")
    op.drop_index("ix_stanzas_run_app_scope_layer", table_name="stanzas")
    op.drop_index("ix_stanzas_run_conf_name", table_name="stanzas")
    op.drop_index("ix_stanzas_run_id", table_name="stanzas")

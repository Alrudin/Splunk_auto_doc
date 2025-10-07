# Database Schema Documentation

## Overview

The Splunk Auto Doc application uses PostgreSQL as its primary data store, with Alembic managing database migrations. This document describes the current database schema for Milestone 1.

## Schema Version

**Current Version**: 003 (Milestone 2 - Parser & Normalization)
**Migration Files**:
- `backend/alembic/versions/001_initial_schema.py` - Milestone 1 baseline
- `backend/alembic/versions/002_stanzas_and_typed.py` - Stanzas and typed tables
- `backend/alembic/versions/003_indexes_and_perf.py` - Performance indexes

## Tables

### ingestion_runs

Tracks uploaded configuration bundles through their lifecycle.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| created_at | TIMESTAMP WITH TIME ZONE | No | Creation timestamp (UTC) |
| type | VARCHAR(50) | No | Upload type enum |
| label | VARCHAR(255) | Yes | Optional human-readable label |
| status | VARCHAR(50) | No | Processing status enum |
| notes | TEXT | Yes | Optional notes about the run |

**Enums:**
- `type`: `ds_etc`, `instance_etc`, `app_bundle`, `single_conf`
- `status`: `pending`, `stored`, `failed`, `complete`

**Indexes:**
- `ix_ingestion_runs_created_at` on `created_at` - for time-based queries
- `ix_ingestion_runs_status` on `status` - for filtering by status

**Status Transitions (Milestone 1):**
- `pending` → `stored` (successful upload)
- `pending` → `failed` (upload error)

**Future States (Milestone 2+):**
- `stored` → `parsing` → `normalized` → `complete`

### files

Tracks uploaded files associated with ingestion runs. In Milestone 1, each run has one file (the uploaded archive). Future milestones may track individual extracted files.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| path | VARCHAR(1024) | No | Archive filename (M1) or file path |
| sha256 | VARCHAR(64) | No | SHA256 hash for deduplication |
| size_bytes | BIGINT | No | File size in bytes |
| stored_object_key | VARCHAR(512) | No | Blob storage reference key |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_files_run_id` on `run_id` - for FK lookups
- `ix_files_sha256` on `sha256` - for deduplication checks

---

## Milestone 2 Tables (Parser & Normalization)

### stanzas

Stores parsed configuration stanzas with full provenance metadata.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| file_id | INTEGER | Yes | Foreign key to files.id |
| conf_type | VARCHAR(50) | No | Configuration type |
| name | VARCHAR(512) | No | Stanza header/name |
| app | VARCHAR(255) | Yes | App name |
| scope | VARCHAR(50) | Yes | Scope: default or local |
| layer | VARCHAR(50) | Yes | Layer: system or app |
| order_in_file | INTEGER | Yes | Stanza order within file |
| source_path | VARCHAR(1024) | No | Full path to source .conf file |
| raw_kv | JSONB | Yes | Raw key-value pairs from stanza |

**Enums:**
- `conf_type`: `inputs`, `props`, `transforms`, `indexes`, `outputs`, `serverclasses`, `other`
- `scope`: `default`, `local`
- `layer`: `system`, `app`

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)
- `file_id` → `files.id` (CASCADE on delete)

**Indexes:**
- `ix_stanzas_run_id` on `run_id` - for FK lookups
- `ix_stanzas_run_conf_name` on `(run_id, conf_type, name)` - for typed queries
- `ix_stanzas_run_app_scope_layer` on `(run_id, app, scope, layer)` - for provenance queries
- `ix_stanzas_raw_kv_gin` on `raw_kv` (GIN) - for JSONB search

### inputs

Normalized Splunk inputs.conf entries with common fields extracted.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| source_path | VARCHAR(1024) | No | Path to source inputs.conf |
| stanza_type | VARCHAR(255) | Yes | Input type (monitor://, tcp://, etc.) |
| index | VARCHAR(255) | Yes | Target index |
| sourcetype | VARCHAR(255) | Yes | Sourcetype |
| disabled | BOOLEAN | Yes | Whether input is disabled |
| kv | JSONB | Yes | Additional key-value pairs |
| app | VARCHAR(255) | Yes | App name |
| scope | VARCHAR(50) | Yes | Scope: default or local |
| layer | VARCHAR(50) | Yes | Layer: system or app |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_inputs_run_id` on `run_id` - for FK lookups
- `ix_inputs_kv_gin` on `kv` (GIN) - for JSONB search

### props

Normalized Splunk props.conf entries with transforms and sedcmds.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| target | VARCHAR(512) | No | Sourcetype or source pattern |
| transforms_list | VARCHAR(255)[] | Yes | TRANSFORMS-* stanzas in order |
| sedcmds | VARCHAR(255)[] | Yes | SEDCMD-* patterns |
| kv | JSONB | Yes | Additional key-value pairs |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_props_run_id` on `run_id` - for FK lookups
- `ix_props_kv_gin` on `kv` (GIN) - for JSONB search

### transforms

Normalized Splunk transforms.conf entries with metadata fields.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| name | VARCHAR(512) | No | Transform name/stanza header |
| dest_key | VARCHAR(255) | Yes | DEST_KEY value |
| regex | TEXT | Yes | REGEX pattern |
| format | TEXT | Yes | FORMAT template |
| writes_meta_index | BOOLEAN | Yes | Writes to _MetaData:Index |
| writes_meta_sourcetype | BOOLEAN | Yes | Writes to _MetaData:Sourcetype |
| kv | JSONB | Yes | Additional key-value pairs |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_transforms_run_id` on `run_id` - for FK lookups
- `ix_transforms_kv_gin` on `kv` (GIN) - for JSONB search

### indexes

Normalized Splunk indexes.conf entries.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| name | VARCHAR(255) | No | Index name |
| kv | JSONB | Yes | Index configuration pairs |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_indexes_run_id` on `run_id` - for FK lookups
- `ix_indexes_kv_gin` on `kv` (GIN) - for JSONB search

### outputs

Normalized Splunk outputs.conf entries with server configurations.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| group_name | VARCHAR(255) | No | Output group name |
| servers | JSONB | Yes | Server list and configurations |
| kv | JSONB | Yes | Additional key-value pairs |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_outputs_run_id` on `run_id` - for FK lookups
- `ix_outputs_servers_gin` on `servers` (GIN) - for JSONB search
- `ix_outputs_kv_gin` on `kv` (GIN) - for JSONB search

### serverclasses

Normalized Splunk serverclass.conf entries with membership and app assignments.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | No | Primary key, auto-incrementing |
| run_id | INTEGER | No | Foreign key to ingestion_runs.id |
| name | VARCHAR(255) | No | Serverclass name |
| whitelist | JSONB | Yes | Whitelist patterns |
| blacklist | JSONB | Yes | Blacklist patterns |
| app_assignments | JSONB | Yes | App assignments |
| kv | JSONB | Yes | Additional key-value pairs |

**Foreign Keys:**
- `run_id` → `ingestion_runs.id` (CASCADE on delete)

**Indexes:**
- `ix_serverclasses_run_id` on `run_id` - for FK lookups
- `ix_serverclasses_whitelist_gin` on `whitelist` (GIN) - for JSONB search
- `ix_serverclasses_blacklist_gin` on `blacklist` (GIN) - for JSONB search
- `ix_serverclasses_app_assignments_gin` on `app_assignments` (GIN) - for JSONB search
- `ix_serverclasses_kv_gin` on `kv` (GIN) - for JSONB search

---

## Relationships

- One `ingestion_run` has many `files` (one-to-many)
- One `ingestion_run` has many `stanzas` (one-to-many)
- One `ingestion_run` has many typed configuration records: `inputs`, `props`, `transforms`, `indexes`, `outputs`, `serverclasses` (one-to-many for each)
- One `file` has many `stanzas` (one-to-many)
- Cascade delete: Deleting an ingestion run deletes all associated files, stanzas, and typed configurations
- Cascade delete: Deleting a file deletes all associated stanzas

## Design Decisions

### Primary Keys

Uses INTEGER auto-increment for simplicity. Could be migrated to UUID in the future for distributed systems.

### Timestamps

All timestamps use `TIMESTAMP WITH TIME ZONE` stored in UTC. Application code should use `datetime.utcnow()` for consistency.

### Enums

Stored as VARCHAR rather than native PostgreSQL enums for flexibility. SQLAlchemy Enum maps Python enums to string columns.

### Status Field

Extensible design allows adding new status values in future milestones without schema changes (within VARCHAR(50) limit).

### JSONB Columns

Milestone 2 introduces extensive use of JSONB for flexible schema:

- **raw_kv** in stanzas: Preserves original key-value pairs from .conf files
- **kv** in typed tables: Stores additional properties not extracted to typed columns
- **servers, whitelist, blacklist, app_assignments**: Complex nested structures

GIN (Generalized Inverted iNdex) indexes enable efficient JSONB queries:

```sql
-- Example: Find stanzas with specific key
SELECT * FROM stanzas WHERE raw_kv ? 'sourcetype';

-- Example: Find inputs with index=main
SELECT * FROM inputs WHERE kv @> '{"index": "main"}';
```

## Migration Management

### Applying Migrations

```bash
# From backend directory
alembic upgrade head

# Check current version
alembic current

# View history
alembic history
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

### Rolling Back

```bash
# Revert one migration
alembic downgrade -1

# Revert to specific version
alembic downgrade <revision_id>

# Revert all migrations
alembic downgrade base
```

## Testing Migrations

A test script verifies migration correctness:

```bash
# Start database with Docker Compose
docker compose up -d db

# Run migration test
cd backend
python scripts/test_migration.py
```

The test script checks:
- Database connectivity
- Table existence
- Column definitions
- Foreign key constraints
- Index creation

## Future Enhancements (Beyond Milestone 2)

Planned additions for future milestones:

1. **hosts table** - Resolved host inventory (M3)
2. **host_memberships** - Host-to-serverclass mappings (M3)
3. **host_apps** - App assignments per host (M3)
4. **host_effective_inputs** - Resolved input configurations (M4)
5. **host_data_paths** - Complete data flow paths (M4)

See `notes/Project description.md` for full schema evolution plan.

## Maintenance

### Backup Considerations

- Use `pg_dump` for logical backups
- Consider point-in-time recovery for production
- Back up before running destructive migrations

### Performance

- Indexes are created for common query patterns
- Monitor query performance as data grows
- Consider partitioning `ingestion_runs` by date if volume is high

### Monitoring

- Track migration timing in CI/CD
- Monitor table sizes and index usage
- Set up alerting for failed migrations

## References

- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Migration Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- Project Milestone Plans: `notes/milestone-1-plan.md`, `notes/milestone-2-plan.md`
- Gap Analysis: `notes/milestone-1-gap-analysis.md`, `notes/milestone-2-gap-analysis.md`
- Normalization Model: `docs/normalization-model.md`

# Database Schema Documentation

## Overview

The Splunk Auto Doc application uses PostgreSQL as its primary data store, with Alembic managing database migrations. This document describes the current database schema for Milestone 1.

## Schema Version

**Current Version**: 001 (Initial Schema)
**Migration File**: `backend/alembic/versions/001_initial_schema.py`

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

## Relationships

- One `ingestion_run` has many `files` (one-to-many)
- Cascade delete: Deleting an ingestion run deletes its associated files

## Design Decisions

### Primary Keys

Uses INTEGER auto-increment for simplicity. Could be migrated to UUID in the future for distributed systems.

### Timestamps

All timestamps use `TIMESTAMP WITH TIME ZONE` stored in UTC. Application code should use `datetime.utcnow()` for consistency.

### Enums

Stored as VARCHAR rather than native PostgreSQL enums for flexibility. SQLAlchemy Enum maps Python enums to string columns.

### Status Field

Extensible design allows adding new status values in future milestones without schema changes (within VARCHAR(50) limit).

### File Storage

The `stored_object_key` field references the blob storage location. Storage backend (local/MinIO/S3) is abstracted at the application level.

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

## Future Enhancements (Beyond Milestone 1)

Planned additions for future milestones:

1. **stanzas table** - Parsed configuration stanzas
2. **inputs/props/transforms tables** - Typed configuration views
3. **hosts table** - Resolved host inventory
4. **host_memberships** - Host-to-serverclass mappings
5. **host_apps** - App assignments per host
6. **host_effective_inputs** - Resolved input configurations
7. **host_data_paths** - Complete data flow paths

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
- Project Milestone Plan: `notes/milestone-1-plan.md`
- Gap Analysis: `notes/milestone-1-gap-analysis.md`

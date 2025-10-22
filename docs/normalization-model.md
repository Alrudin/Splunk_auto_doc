# Normalization Model Documentation

## Overview

This document describes the normalization model for Milestone 2 (Parser & Normalization), which transforms raw Splunk .conf files into structured, queryable database tables. The normalization process preserves complete provenance metadata and supports efficient querying of configuration relationships.

## Architecture

The normalization pipeline consists of two main layers:

1. **Generic Stanza Layer**: The `stanzas` table stores all parsed configuration stanzas with minimal interpretation, preserving raw key-value pairs in JSONB.

2. **Typed Configuration Layer**: Specialized tables (`inputs`, `props`, `transforms`, `indexes`, `outputs`, `serverclasses`) extract and normalize domain-specific fields from stanzas.

```
┌─────────────────┐
│  .conf files    │
│  (tar/zip)      │
└────────┬────────┘
         │
         ▼
  ┌──────────────┐
  │   Parser     │
  │   Core       │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐      Generic storage with
  │   stanzas    │◄──── full provenance &
  │   table      │      raw key-value pairs
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │    Typed     │      Domain-specific
  │  Projection  │◄──── field extraction &
  │   Mappers    │      normalization
  └──────┬───────┘
         │
         ├─────► inputs
         ├─────► props
         ├─────► transforms
         ├─────► indexes
         ├─────► outputs
         └─────► serverclasses
```

## Stanzas Table (Generic Layer)

The `stanzas` table is the foundation of the normalization model. It stores every parsed stanza from every .conf file with complete metadata.

### Key Design Principles

1. **Lossless Capture**: All key-value pairs are preserved in the `raw_kv` JSONB column
2. **Provenance Tracking**: Every stanza records its source (run, file, path, app, scope, layer)
3. **Order Preservation**: `order_in_file` maintains stanza sequence for precedence rules
4. **Type Classification**: `conf_type` enables efficient filtering and routing to typed tables

### Fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | INTEGER | Primary key |
| `run_id` | INTEGER | Links to ingestion run |
| `file_id` | INTEGER | Links to source file |
| `conf_type` | VARCHAR(50) | Configuration type (inputs, props, etc.) |
| `name` | VARCHAR(512) | Stanza header/name |
| `app` | VARCHAR(255) | App name from file path |
| `scope` | VARCHAR(50) | `default` or `local` |
| `layer` | VARCHAR(50) | `system` or `app` |
| `order_in_file` | INTEGER | Stanza sequence number |
| `source_path` | VARCHAR(1024) | Full path to .conf file |
| `raw_kv` | JSONB | All key-value pairs from stanza |

### Example Stanza Record

```json
{
  "id": 1,
  "run_id": 42,
  "file_id": 123,
  "conf_type": "inputs",
  "name": "monitor:///var/log/app.log",
  "app": "search",
  "scope": "local",
  "layer": "app",
  "order_in_file": 5,
  "source_path": "/opt/splunk/etc/apps/search/local/inputs.conf",
  "raw_kv": {
    "index": "main",
    "sourcetype": "app:log",
    "disabled": "0",
    "followTail": "1"
  }
}
```

## Typed Configuration Tables

Typed tables extract common fields from stanzas into typed columns for efficient querying and validation. Less common or dynamic properties remain in the `kv` JSONB column.

### inputs

**Purpose**: Normalizes Splunk input configurations (monitor, tcp, udp, scripts, etc.)

**Key Extraction Logic**:
- **Stanza Type Detection**: Extract input type from stanza name prefix using regex pattern `^([^:]+)://`
  - Supported types: `monitor://`, `tcp://`, `udp://`, `script://`, `WinEventLog://`, `splunktcp://`, `http://`, `fifo://`, and others
  - Type is normalized to lowercase (e.g., "WinEventLog" → "wineventlog")
  - Default and other stanzas without type prefix have `stanza_type = NULL`
- **Typed Column Extraction**:
  - `index`: Target index for events (if specified)
  - `sourcetype`: Event sourcetype (if specified)
  - `disabled`: Boolean field normalized from Splunk's string values
    - Accepts: "0"/"1", "true"/"false", "yes"/"no" (case-insensitive)
    - Whitespace is trimmed before conversion
- **Additional Properties**: All non-extracted fields stored in `kv` JSONB
  - Examples: `followTail`, `recursive`, `connection_host`, `interval`, `queueSize`, etc.
- **Provenance Preservation**:
  - `source_path`: Full path to source inputs.conf file
  - `app`: App name extracted from file path
  - `scope`: "default" or "local" from file path
  - `layer`: "system" or "app" from file path

**Projection Implementation**: `app/projections/inputs.py` - `InputProjector` class

**Use Cases**:
- List all inputs by type: `SELECT * FROM inputs WHERE stanza_type = 'monitor'`
- Find inputs writing to specific index: `SELECT * FROM inputs WHERE index = 'main'`
- Identify disabled inputs: `SELECT * FROM inputs WHERE disabled = true`
- Query inputs with specific properties: `SELECT * FROM inputs WHERE kv @> '{"followTail": "1"}'`

**Edge Cases Handled**:
- Stanzas without type prefix (e.g., `[default]`) have `stanza_type = NULL`
- Missing provenance metadata defaults to NULL or `<unknown>` for source_path
- Empty `kv` is stored as NULL rather than empty object
- Last-wins semantics preserved from parser for repeated keys

### props

**Purpose**: Normalizes sourcetype and source properties, especially transform chains

**Key Extraction Logic**:
- `target` stores the sourcetype or source pattern (stanza name)
- `transforms_list` collects all `TRANSFORMS-*` keys in order
- `sedcmds` collects all `SEDCMD-*` keys
- Remaining properties in `kv`

**Use Cases**:
- Trace transform chains for a sourcetype
- Find all props with SEDCMD operations
- Analyze parsing configuration

### transforms

**Purpose**: Normalizes field extraction and routing transforms

**Key Extraction Logic**:
- Extract `DEST_KEY`, `REGEX`, `FORMAT` to typed columns
- Set `writes_meta_index` = true if `DEST_KEY` = `_MetaData:Index`
- Set `writes_meta_sourcetype` = true if `DEST_KEY` = `_MetaData:Sourcetype`
- Remaining properties in `kv`

**Use Cases**:
- Find transforms that modify index/sourcetype
- Analyze field extraction patterns
- Validate REGEX correctness

### indexes

**Purpose**: Normalizes index definitions

**Key Extraction Logic**:
- `name` is the index name (stanza name)
- All index properties stored in `kv` (homePath, coldPath, maxDataSize, etc.)

**Use Cases**:
- List all indexes
- Query index retention settings
- Find index storage paths

### outputs

**Purpose**: Normalizes forwarding configurations

**Key Extraction Logic**:
- `group_name` is the output group (stanza name)
- `servers` JSONB contains server list and configurations
- Remaining properties in `kv`

**Use Cases**:
- List all forwarding destinations
- Find outputs by target server
- Analyze load balancing configuration

### serverclasses

**Purpose**: Normalizes deployment server configurations

**Key Extraction Logic**:
- `name` is the serverclass name
- `whitelist` JSONB contains host patterns
- `blacklist` JSONB contains exclusion patterns
- `app_assignments` JSONB contains app deployment rules
- Remaining properties in `kv`

**Use Cases**:
- List serverclasses for a host pattern
- Find all apps deployed via a serverclass
- Validate whitelist/blacklist rules

## Provenance and Precedence

### Provenance Metadata

Every record in typed tables includes:

- **run_id**: Which ingestion run produced this record
- **app**: Which app contained the configuration
- **scope**: Whether from `default/` or `local/` directory
- **layer**: Whether from `system/` or `apps/` hierarchy
- **source_path**: Full path to the source .conf file

This metadata enables:

1. **Audit Trail**: Track configuration changes across runs
2. **Precedence Resolution**: Apply Splunk's configuration layering rules
3. **Impact Analysis**: Identify which files affect specific configurations
4. **Troubleshooting**: Trace configuration to exact source file

### Splunk Precedence Rules

Splunk applies configurations in this precedence order (highest to lowest):

1. `$SPLUNK_HOME/etc/apps/<app>/local/`
2. `$SPLUNK_HOME/etc/apps/<app>/default/`
3. `$SPLUNK_HOME/etc/system/local/`
4. `$SPLUNK_HOME/etc/system/default/`

The normalization model preserves this metadata but does **not** automatically resolve precedence in Milestone 2. Precedence resolution is deferred to Milestone 4 (Routing Resolver).

### Order Preservation

For configurations where order matters (especially props and transforms), the `order_in_file` field in stanzas maintains sequence. Typed tables may include additional ordering fields as needed.

## JSONB Usage Patterns

### Why JSONB?

1. **Flexibility**: Splunk .conf files have hundreds of possible keys; storing all as typed columns is impractical
2. **Performance**: PostgreSQL GIN indexes enable efficient JSONB queries
3. **Evolution**: New Splunk configuration options don't require schema migrations

### Query Examples

```sql
-- Find all stanzas with a specific key
SELECT * FROM stanzas
WHERE raw_kv ? 'sourcetype';

-- Find inputs with index=main
SELECT * FROM inputs
WHERE kv @> '{"index": "main"}';

-- Find transforms using a specific REGEX
SELECT * FROM transforms
WHERE kv->>'REGEX' LIKE '%ERROR%';

-- Find serverclasses whitelisting a host
SELECT * FROM serverclasses
WHERE whitelist @> '["webserver*"]';
```

### Best Practices

1. **Extract Common Fields**: Frequently queried fields should be typed columns, not in JSONB
2. **Use GIN Indexes**: All JSONB columns have GIN indexes for efficient searches
3. **Validate Structure**: Application code should validate JSONB structure before insert
4. **Document Schema**: Comment JSONB structure in code and documentation

## Normalization Pipeline

The normalization process follows these steps:

### 1. Archive Extraction

- Unpack tar/zip to secure temporary directory
- Validate against zip bombs and path traversal
- Enforce size/file-count/depth limits

### 2. File Discovery

- Walk directory tree to find .conf files
- Filter by type: `inputs.conf`, `props.conf`, `transforms.conf`, `outputs.conf`, `indexes.conf`, `serverclass.conf`
- Extract metadata: app name, scope (default/local), layer (system/app)

### 3. Parsing

- Parse each .conf file into ordered stanzas
- Handle Splunk-specific syntax:
  - Comments (`#`)
  - Line continuations (`\`)
  - Repeated keys (last wins)
  - Multi-line values
- Preserve original order

### 4. Stanza Storage

- Insert all stanzas into `stanzas` table
- Bulk insert for performance
- Record provenance (run_id, file_id, source_path, app, scope, layer)

### 5. Typed Projection

- Apply type-specific mappers to stanzas
- Extract domain fields to typed columns
- Store remaining properties in `kv` JSONB
- Bulk insert typed records

### 6. Validation

- Count stanzas by type
- Validate foreign key relationships
- Log any parsing errors or warnings

## Performance Considerations

### Bulk Inserts

Use SQLAlchemy Core for bulk operations:

```python
# Example: Bulk insert stanzas
stanza_rows = [...]  # List of dicts
with engine.begin() as conn:
    conn.execute(stanzas_table.insert(), stanza_rows)
```

### Indexes

All critical query paths have indexes:

- B-tree indexes on foreign keys and common filters
- GIN indexes on JSONB columns
- Composite indexes on multi-column queries

### Query Optimization

- Use `EXPLAIN ANALYZE` to verify index usage
- Avoid `SELECT *` on JSONB-heavy tables
- Use covering indexes where possible

## Testing Strategy

### Unit Tests

- Parser correctness (comments, continuations, repeated keys)
- Typed mappers (field extraction logic)
- Edge cases (empty files, malformed stanzas)

### Integration Tests

- End-to-end: upload → parse → query
- Validate counts and provenance
- Test with golden fixtures (known good .conf sets)

### Property Tests

- Last-wins semantics for repeated keys
- Order preservation invariants
- Provenance completeness

## Future Enhancements

Planned for future milestones:

1. **M3 - Host Resolution**: Resolve serverclass membership to host inventory
2. **M4 - Routing Resolver**: Apply precedence rules to compute effective configurations
3. **M5 - Data Flow Paths**: Trace complete data paths from input to index

## Example Mappings

### inputs.conf Stanza Mapping

**Source (inputs.conf stanza):**
```ini
[monitor:///var/log/app.log]
disabled = false
index = main
sourcetype = app:log
followTail = 1
recursive = true
```

**Projection (inputs table record):**
```json
{
  "run_id": 42,
  "source_path": "/opt/splunk/etc/apps/search/local/inputs.conf",
  "stanza_type": "monitor",
  "index": "main",
  "sourcetype": "app:log",
  "disabled": false,
  "kv": {
    "followTail": "1",
    "recursive": "true"
  },
  "app": "search",
  "scope": "local",
  "layer": "app"
}
```

**Source (tcp input):**
```ini
[tcp://9997]
disabled = 0
connection_host = ip
sourcetype = splunk:tcp
```

**Projection:**
```json
{
  "stanza_type": "tcp",
  "index": null,
  "sourcetype": "splunk:tcp",
  "disabled": false,
  "kv": {
    "connection_host": "ip"
  }
}
```

**Source (default stanza):**
```ini
[default]
host = hf-01.example.com
index = default
```

**Projection:**
```json
{
  "stanza_type": null,
  "index": "default",
  "sourcetype": null,
  "disabled": null,
  "kv": {
    "host": "hf-01.example.com"
  }
}
```

## References

- Milestone 2 Plan: `notes/milestone-2-plan.md`
- Database Schema: `notes/database-schema.md`
- Splunk Configuration File Precedence: [Splunk Docs](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Wheretofindtheconfigurationfiles)
- PostgreSQL JSONB: [PostgreSQL Docs](https://www.postgresql.org/docs/current/datatype-json.html)
- Input Projector Implementation: `backend/app/projections/inputs.py`

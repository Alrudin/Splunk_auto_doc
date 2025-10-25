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
- **Target Identification**: Extract sourcetype or source pattern from stanza header
  - Sourcetype stanzas: `[app:log]`, `[json:api]`, `[custom:data]`
  - Source pattern stanzas: `[source::/var/log/special/*.log]`
  - Default stanza: `[default]` sets defaults for all sourcetypes
- **TRANSFORMS-* Keys**: Collected into `transforms_list` array in order
  - Keys like `TRANSFORMS-routing`, `TRANSFORMS-mask`, `TRANSFORMS-cleanup`
  - Values can be single transform name or comma-separated list: "transform1, transform2"
  - Order matters: transforms are applied sequentially
  - Last-wins semantics apply for repeated TRANSFORMS-* keys with same suffix
- **SEDCMD-* Keys**: Collected into `sedcmds` array in order
  - Keys like `SEDCMD-remove_sensitive`, `SEDCMD-normalize_dates`
  - Values are sed-like regex substitution patterns: `s/pattern/replacement/flags`
  - Order matters: sed commands are applied sequentially
- **Additional Properties**: All non-extracted fields stored in `kv` JSONB
  - Examples: `EXTRACT-*`, `REPORT-*`, `LINE_BREAKER`, `SHOULD_LINEMERGE`, `TIME_FORMAT`, `INDEXED_EXTRACTIONS`, `KV_MODE`, etc.

**Projection Implementation**: `app/projections/props.py` - `PropsProjector` class

**Use Cases**:
- Trace transform chains for a sourcetype: `SELECT * FROM props WHERE target = 'app:log'`
- Find all props with SEDCMD operations: `SELECT * FROM props WHERE sedcmds IS NOT NULL`
- Analyze parsing configuration: `SELECT * FROM props WHERE kv ? 'LINE_BREAKER'`
- List transform chains: `SELECT target, transforms_list FROM props WHERE transforms_list IS NOT NULL`
- Query field extraction rules: `SELECT * FROM props WHERE kv ? 'EXTRACT-fields'`

**Edge Cases Handled**:
- Default stanza (`[default]`) provides defaults for all sourcetypes
- TRANSFORMS-* keys with comma-separated values are split into individual transforms
- SEDCMD-* patterns preserved exactly as defined (no parsing of sed syntax)
- Empty `transforms_list` and `sedcmds` stored as NULL rather than empty array
- Empty `kv` is stored as NULL rather than empty object
- Case-insensitive matching for TRANSFORMS-* and SEDCMD-* keys
- Last-wins semantics preserved from parser for repeated keys
- Multi-line values with line continuations handled by parser before projection
- Order preservation critical for both TRANSFORMS and SEDCMD chains

### transforms

**Purpose**: Normalizes field extraction and routing transforms

**Key Extraction Logic**:
- **Typed Column Extraction**:
  - `name`: Transform name from stanza header
  - `dest_key`: DEST_KEY value (if specified) - normalized by trimming whitespace
  - `regex`: REGEX pattern (if specified) - preserved as-is for validation
  - `format`: FORMAT template (if specified) - used for output formatting
- **Metadata Write Detection**:
  - `writes_meta_index`: Set to `true` if DEST_KEY = `_MetaData:Index` (case-insensitive)
  - `writes_meta_sourcetype`: Set to `true` if DEST_KEY = `MetaData:Sourcetype` or `_MetaData:Sourcetype` (case-insensitive)
  - Both flags set to `false` if DEST_KEY is specified but not metadata-related
  - Both flags set to `null` if DEST_KEY is not specified
- **Additional Properties**: All non-extracted fields stored in `kv` JSONB
  - Examples: `PRIORITY`, `MV_ADD`, `WRITE_META`, `LOOKAHEAD`, `filename`, `max_matches`, etc.

**Projection Implementation**: `app/projections/transforms.py` - `TransformProjector` class

**Use Cases**:
- Find transforms that modify index/sourcetype: `SELECT * FROM transforms WHERE writes_meta_index = true`
- Analyze field extraction patterns: `SELECT name, regex, format FROM transforms WHERE regex IS NOT NULL`
- Validate REGEX correctness: `SELECT * FROM transforms WHERE regex LIKE '%ERROR%'`
- Find data masking transforms: `SELECT * FROM transforms WHERE dest_key = '_raw'`
- Query lookup-based transforms: `SELECT * FROM transforms WHERE kv ? 'filename'`

**Edge Cases Handled**:
- DEST_KEY case variations: `_MetaData:Index`, `_metadata:index`, `MetaData:Sourcetype`, `metadata:sourcetype`
- Missing fields: All extracted fields can be NULL if not specified
- Multi-line REGEX with continuations: Parser handles line continuations before projection
- Empty kv is stored as NULL rather than empty object
- Last-wins semantics preserved from parser for repeated stanza definitions

### indexes

**Purpose**: Normalizes index definitions from indexes.conf

**Key Extraction Logic**:
- **Index Name**: Extracted from stanza header
  - Preserved exactly as defined (e.g., "main", "app_index", "_internal")
  - Special stanza `[default]` sets default values for all indexes
  - Index names can include underscores, numbers, and hyphens
- **All Properties in JSONB**: Unlike inputs and transforms, indexes.conf has a vast array of possible settings that vary by index type and deployment configuration. All properties are stored in the `kv` JSONB column for maximum flexibility.

**Common Index Properties** (all in kv):
- **Storage Paths**:
  - `homePath`: Path to hot and warm buckets (e.g., `$SPLUNK_DB/$_index_name/db`)
  - `coldPath`: Path to cold buckets
  - `thawedPath`: Path to thawed buckets
  - `coldToFrozenDir`: Archive location for frozen data
- **Retention Settings**:
  - `frozenTimePeriodInSecs`: How long to keep data before archiving (e.g., "188697600" = 6 years)
  - `maxTotalDataSizeMB`: Maximum size of index in MB
  - `maxGlobalDataSizeMB`: Maximum size across cluster (cluster mode)
- **Performance Tuning**:
  - `maxHotBuckets`: Number of hot buckets (default varies)
  - `maxWarmDBCount`: Maximum number of warm buckets
  - `maxDataSize`: Maximum size of hot/warm buckets before rolling (e.g., "auto", "10000")
  - `maxHotSpanSecs`: Time span for hot buckets
- **Data Type**:
  - `datatype`: "event" (default) or "metric" for metrics store indexes
- **Compression & Optimization**:
  - `compressRawdata`: Whether to compress raw data (true/false)
  - `enableTsidxReduction`: Enable time-series index reduction (true/false)
  - `tsidxReductionCheckPeriodInSec`: Check period for TSIDX reduction
- **Replication** (cluster mode):
  - `repFactor`: Replication factor (number or "auto")
  - `maxGlobalRawDataSizeMB`: Maximum raw data size across cluster
- **Security**:
  - `coldToFrozenScript`: Script to run when archiving data
- And many more settings...

**Projection Implementation**: `app/projections/indexes.py` - `IndexProjector` class

**Use Cases**:
- List all indexes: `SELECT name FROM indexes WHERE run_id = ?`
- Find indexes with metrics data: `SELECT * FROM indexes WHERE kv @> '{"datatype": "metric"}'`
- Query retention settings: `SELECT name, kv->>'frozenTimePeriodInSecs' FROM indexes`
- Find indexes with custom paths: `SELECT * FROM indexes WHERE kv->>'homePath' LIKE '/custom/%'`
- Identify indexes with replication: `SELECT * FROM indexes WHERE kv ? 'repFactor'`
- Find indexes with compression: `SELECT * FROM indexes WHERE kv @> '{"compressRawdata": "true"}'`

**Edge Cases Handled**:
- Default stanza (`[default]`) provides defaults for all indexes
- All properties stored in JSONB (no typed extraction except name)
- Empty `kv` is stored as NULL rather than empty object
- Index names preserved exactly (case-sensitive)
- Supports Splunk variables: `$SPLUNK_DB`, `$_index_name`, etc.
- Handles both Windows (`C:\path\to\index`) and Unix (`/opt/splunk/index`) path styles
- Last-wins semantics preserved from parser for repeated keys within a stanza

**Splunk-Specific Nuances**:
- The `[default]` stanza sets defaults that apply to all indexes unless overridden
- Variable `$_index_name` is replaced with actual index name by Splunk at runtime
- Retention (`frozenTimePeriodInSecs`) is in seconds (common values: 188697600 = 6 years, 2592000 = 30 days)
- Size limits (`maxTotalDataSizeMB`) are in megabytes
- Hot buckets are actively being written to; warm buckets are searchable but not writable; cold buckets are on slower storage; frozen buckets are archived
- Metrics indexes (`datatype = metric`) use a different storage format optimized for time-series data
- In clustered environments, `repFactor` and global size limits control replication

See `test_index_projector.py` and `test_index_projector_integration.py` for comprehensive test coverage.

### outputs

**Purpose**: Normalizes forwarding configurations from outputs.conf

**Key Extraction Logic**:
- **Group Name**: Extracted from stanza header
  - Preserved exactly as defined (e.g., "tcpout", "tcpout:primary_indexers", "syslog:siem_output", "httpout:hec_output")
  - Default stanza `[tcpout]` sets default forwarding behavior
  - Named groups use colon syntax: `<type>:<name>`
- **Servers JSONB**: Contains server-related configuration
  - `server`: Comma-separated list of server:port pairs (for tcpout, syslog)
    - Example: "indexer1.example.com:9997, indexer2.example.com:9997, indexer3.example.com:9997"
  - `uri`: HTTP(S) URI for HEC outputs
    - Example: "https://hec.splunkcloud.com:8088/services/collector"
  - `target_group`: Reference to other output groups (for cloning/routing)
    - Example: "primary_indexers, backup_indexers"
  - Empty servers is stored as NULL (e.g., for `[tcpout]` default stanza)
- **Additional Properties**: All non-server fields stored in `kv` JSONB
  - Examples: `compressed`, `autoLBFrequency`, `maxQueueSize`, `defaultGroup`, `indexAndForward`, `token`, `sslVerifyServerCert`, etc.

**Projection Implementation**: `app/projections/outputs.py` - `OutputProjector` class

**Common Output Properties** (in kv):
- **Load Balancing & Performance**:
  - `autoLBFrequency`: Load balancing frequency in seconds (e.g., "30")
  - `maxQueueSize`: Maximum queue size (e.g., "10MB")
  - `compressed`: Whether to compress data (true/false)
- **Default Settings** (in `[tcpout]` stanza):
  - `defaultGroup`: Default output group to use
  - `indexAndForward`: Whether to index locally and forward (true/false)
  - `forwardedindex.filter.disable`: Disable index filtering (true/false)
- **HEC-Specific** (in `httpout:*` stanzas):
  - `token`: Authentication token
  - `sslVerifyServerCert`: SSL certificate verification (true/false)
- **Syslog-Specific** (in `syslog:*` stanzas):
  - `type`: Output type (tcp/udp)
  - `priority`: Syslog priority (e.g., "<134>")
- **Routing**:
  - `target_group`: Reference to other groups for cloning/routing
- And many more settings...

**Use Cases**:
- List all forwarding destinations: `SELECT * FROM outputs WHERE servers IS NOT NULL`
- Find outputs by target server: `SELECT * FROM outputs WHERE servers->>'server' LIKE '%indexer1%'`
- Analyze load balancing configuration: `SELECT group_name, kv->>'autoLBFrequency' FROM outputs`
- Find HEC outputs: `SELECT * FROM outputs WHERE group_name LIKE 'httpout:%'`
- Query clone groups: `SELECT * FROM outputs WHERE servers ? 'target_group'`
- Find compressed outputs: `SELECT * FROM outputs WHERE kv @> '{"compressed": "true"}'`

**Edge Cases Handled**:
- Default stanza (`[tcpout]`) has `servers = NULL` (no server-related fields)
- Multiple server values use last-wins semantics (e.g., repeated `server =` lines)
- Comma-separated server lists are preserved as single string value
- Empty `servers` and `kv` are stored as NULL rather than empty object
- Group names preserved exactly (case-sensitive)
- `target_group` allows routing to multiple destination groups

**Splunk-Specific Nuances**:
- The `[tcpout]` stanza sets global defaults for all tcpout groups
- Named groups (`tcpout:<name>`) define specific indexer destinations
- Load balancing (`autoLBFrequency`) distributes events across multiple servers in a group
- `indexAndForward` allows a forwarder to both index locally and forward to indexers
- `target_group` enables cloning data to multiple groups simultaneously
- HEC outputs (`httpout:*`) use token authentication and HTTPS
- Syslog outputs can use TCP or UDP and support standard syslog priorities
- Server lists support comma-separated values for multiple destinations
- Last-wins semantics apply when `server` is defined multiple times in same stanza

See `test_output_projector.py` and `test_output_projector_integration.py` for comprehensive test coverage.

### serverclasses

**Purpose**: Normalizes deployment server configurations from serverclass.conf

**Key Extraction Logic**:
- **Serverclass Name Detection**: Extract serverclass name from stanza header using regex pattern `^serverClass:([^:]+)$`
  - Supported formats: `serverClass:production`, `serverClass:universal_forwarders`, etc.
  - Serverclass names can contain letters, numbers, and underscores
  - App assignment stanzas (`serverClass:name:app:appname`) are identified but not currently projected
  - Global stanza (`[global]`) is skipped
- **Typed Column Extraction**:
  - `name`: Serverclass name extracted from stanza header
  - `whitelist`: JSONB dictionary of whitelist patterns from `whitelist.N` keys
    - Keys are numbered (e.g., `whitelist.0`, `whitelist.1`, `whitelist.2`)
    - Stored as dict mapping number to pattern: `{"0": "prod-*.example.com", "1": "uf-*.example.com"}`
    - Numbers may be non-sequential
    - Last-wins semantics apply for duplicate numbers
  - `blacklist`: JSONB dictionary of blacklist patterns from `blacklist.N` keys
    - Same structure as whitelist
    - Used to exclude hosts from serverclass membership
  - `app_assignments`: JSONB dictionary of app assignments (currently NULL, reserved for future)
  - `kv`: Additional properties (JSONB)
    - Examples: `restartSplunkd`, `restartSplunkWeb`, `stateOnClient`, `machineTypesFilter`, etc.
- **Provenance Preservation**:
  - `app`: App name extracted from file path
  - `scope`: "default" or "local" from file path
  - `layer`: "system" or "app" from file path

**Projection Implementation**: `app/projections/serverclasses.py` - `ServerclassProjector` class

**Use Cases**:
- List all serverclasses: `SELECT name FROM serverclasses`
- Find serverclasses whitelisting a host pattern: `SELECT * FROM serverclasses WHERE whitelist @> '{"0": "prod-*.example.com"}'`
- Find serverclasses with specific settings: `SELECT * FROM serverclasses WHERE kv @> '{"restartSplunkd": "true"}'`
- Validate whitelist/blacklist rules for deployment targeting

**Supported Stanza Types**:
- `[serverClass:name]` - Serverclass definition with targeting rules
- `[serverClass:name:app:appname]` - App assignment (identified but not projected in current implementation)
- `[global]` - Global settings (skipped by projector)

**Edge Cases Handled**:
- Global stanza is not projected (returns None)
- App assignment stanzas are not projected (returns None, reserved for future aggregation)
- Non-serverclass stanzas return None
- Empty whitelist/blacklist are stored as NULL
- Empty kv is stored as NULL
- Missing provenance metadata defaults to NULL
- Non-sequential whitelist/blacklist numbers are preserved
- Last-wins semantics for duplicate whitelist/blacklist numbers

**Example Projection**:

From this serverclass.conf stanza:
```ini
[serverClass:production]
whitelist.0 = prod-hf-*.example.com
whitelist.1 = prod-uf-*.example.com
blacklist.0 = *-test.example.com
restartSplunkd = true
restartSplunkWeb = false
```

Projected as:
```python
{
    "run_id": 1,
    "name": "production",
    "whitelist": {
        "0": "prod-hf-*.example.com",
        "1": "prod-uf-*.example.com"
    },
    "blacklist": {
        "0": "*-test.example.com"
    },
    "app_assignments": None,
    "kv": {
        "restartSplunkd": "true",
        "restartSplunkWeb": "false"
    },
    "app": "deployment",
    "scope": "local",
    "layer": "app"
}
```

See `test_serverclass_projector.py` and `test_serverclass_projector_integration.py` for comprehensive test coverage.

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

The normalization pipeline orchestrates the complete flow from archive upload through parsing, projection, and bulk insertion into the database. This is the core service bridging uploads with normalized data for downstream API/UI.

### Pipeline Architecture

```
┌─────────────────┐
│  Upload Archive │
│   (tar/zip)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Storage       │
│  (S3/Local)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Worker Task    │  ← Celery background task
│  (parse_run)    │     with retry & heartbeat
└────────┬────────┘
         │
         ├──► 1. Secure Extraction
         │         (zip bombs, path traversal, symlinks)
         │
         ├──► 2. Walk & Filter
         │         (find .conf files, extract provenance)
         │
         ├──► 3. Parse
         │         (ConfParser → ParsedStanza[])
         │
         ├──► 4. Bulk Insert Stanzas
         │         (SQLAlchemy Core)
         │
         ├──► 5. Typed Projection
         │         (6 projectors → typed rows)
         │
         └──► 6. Bulk Insert Projections
                  (SQLAlchemy Core)
```

The normalization process follows these steps:

### 1. Archive Extraction (Security-Hardened)

**Security Guardrails**:
- **Zip Bomb Protection**: Max 100MB per file, 1GB total uncompressed size
- **Path Traversal Prevention**: Validates all paths stay within extraction directory
- **Symlink Blocking**: Rejects archives containing symlinks or hardlinks (tar only)
- **File Count Limit**: Maximum 10,000 files per archive
- **Directory Depth Limit**: Maximum 20 levels deep

**Implementation**:
```python
# From app/worker/tasks.py::_extract_archive()
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB per file
MAX_TOTAL_SIZE = 1024 * 1024 * 1024  # 1 GB total
MAX_FILE_COUNT = 10000
MAX_DEPTH = 20
```

**Supported Formats**:
- `.tar.gz` / `.tgz` - Gzip-compressed tar archives
- `.tar` - Uncompressed tar archives
- `.zip` - ZIP archives

**Safety Mechanisms**:
- Pre-extraction validation of all members
- Path resolution and normalization
- Real-time size tracking during extraction
- Post-extraction symlink scan and removal
- Extraction to isolated temporary directory

### 2. File Discovery

- Walk directory tree to find .conf files
- Filter by type: `inputs.conf`, `props.conf`, `transforms.conf`, `outputs.conf`, `indexes.conf`, `serverclass.conf`
- Extract metadata: app name, scope (default/local), layer (system/app)
- Preserve file provenance for each configuration

### 3. Parsing

- Parse each .conf file into ordered stanzas using `ConfParser`
- Handle Splunk-specific syntax:
  - Comments (`#`)
  - Line continuations (`\`)
  - Repeated keys (last wins)
  - Multi-line values
- Preserve original order (critical for precedence)
- Extract provenance metadata (app, scope, layer, source_path)

### 4. Stanza Storage (Bulk Insert)

**Performance Optimization**:
- Accumulate all stanzas in memory during parsing
- Single bulk insert using SQLAlchemy Core `insert()` statement
- Idempotency check: skip if stanzas already exist for run
- Commit after successful bulk insert

**Benefits**:
- 10-100x faster than individual inserts
- Reduced database round-trips
- Atomic operation (all-or-nothing)

```python
# Bulk insert example
from sqlalchemy import insert
stmt = insert(Stanza).values(stanza_rows)
db.execute(stmt)
db.commit()
```

### 5. Typed Projection

**Projection Flow**:
```
Stanza (generic)  ─┬─► InputProjector      ─► Input (typed)
                   ├─► PropsProjector      ─► Props (typed)
                   ├─► TransformProjector  ─► Transform (typed)
                   ├─► IndexProjector      ─► Index (typed)
                   ├─► OutputProjector     ─► Output (typed)
                   └─► ServerclassProjector ─► Serverclass (typed)
```

**Process**:
1. Group parsed stanzas by conf_type (inputs, props, etc.)
2. Apply appropriate projector to each stanza
3. Extract common fields to typed columns
4. Store remaining fields in `kv` JSONB
5. Handle projection errors gracefully (log and continue)

**Projectors** (see individual sections above for details):
- `InputProjector`: Extracts stanza_type, index, sourcetype, disabled
- `PropsProjector`: Extracts target, transforms_list, sedcmds
- `TransformProjector`: Extracts dest_key, regex, format, metadata flags
- `IndexProjector`: Stores all properties in kv JSONB
- `OutputProjector`: Extracts group_name, servers (server/uri/target_group)
- `ServerclassProjector`: Extracts whitelist, blacklist patterns

### 6. Bulk Insert Typed Projections

**Performance Optimization**:
- Single bulk insert per conf_type using SQLAlchemy Core
- Non-fatal errors: If typed projection fails, stanzas are still persisted
- Logged metrics for each projection type

```python
# Bulk insert typed projections
if conf_type == "inputs":
    stmt = insert(Input).values(projected_rows)
    db.execute(stmt)
```

**Error Handling**:
- Projection errors are logged but don't fail the entire run
- Stanzas remain queryable even if typed projection fails
- Retry-safe: projections can be re-run if needed

### 7. Validation & Metrics

**Collected Metrics**:
```json
{
  "files_parsed": 15,
  "stanzas_created": 234,
  "typed_projections": {
    "inputs": 45,
    "props": 32,
    "transforms": 28,
    "indexes": 8,
    "outputs": 12,
    "serverclasses": 3
  },
  "duration_seconds": 12.5,
  "parse_errors": 2,
  "retry_count": 0
}
```

**Validation**:
- Count stanzas by type
- Count typed projections by type
- Validate foreign key relationships
- Log any parsing errors or warnings
- Track duration and performance

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

### props.conf Stanza Mapping

**Source (default settings):**
```ini
[default]
SHOULD_LINEMERGE = true
```

**Projection (props table record):**
```json
{
  "run_id": 42,
  "target": "default",
  "transforms_list": null,
  "sedcmds": null,
  "kv": {
    "SHOULD_LINEMERGE": "true"
  }
}
```

**Source (sourcetype with transforms):**
```ini
[app:log]
TRANSFORMS-routing = route_to_index
TRANSFORMS-mask = mask_sensitive_data
EXTRACT-fields = ^(?P<timestamp>\S+)\s+(?P<level>\w+)\s+(?P<message>.*)$
LINE_BREAKER = ([\r\n]+)\d{4}-\d{2}-\d{2}
SHOULD_LINEMERGE = false
TIME_PREFIX = ^
TIME_FORMAT = %Y-%m-%d %H:%M:%S
MAX_TIMESTAMP_LOOKAHEAD = 20
```

**Projection:**
```json
{
  "run_id": 42,
  "target": "app:log",
  "transforms_list": ["route_to_index", "mask_sensitive_data"],
  "sedcmds": null,
  "kv": {
    "EXTRACT-fields": "^(?P<timestamp>\\S+)\\s+(?P<level>\\w+)\\s+(?P<message>.*)$",
    "LINE_BREAKER": "([\\r\\n]+)\\d{4}-\\d{2}-\\d{2}",
    "SHOULD_LINEMERGE": "false",
    "TIME_PREFIX": "^",
    "TIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "MAX_TIMESTAMP_LOOKAHEAD": "20"
  }
}
```

**Source (source pattern):**
```ini
[source::/var/log/special/*.log]
sourcetype = special:log
TRANSFORMS-parse = extract_special_fields
```

**Projection:**
```json
{
  "run_id": 42,
  "target": "source::/var/log/special/*.log",
  "transforms_list": ["extract_special_fields"],
  "sedcmds": null,
  "kv": {
    "sourcetype": "special:log"
  }
}
```

**Source (props with SEDCMD operations):**
```ini
[custom:data]
SEDCMD-remove_sensitive = s/password=\S+/password=***MASKED***/g
SEDCMD-normalize_dates = s/(\d{2})\/(\d{2})\/(\d{4})/\3-\1-\2/g
TRANSFORMS-index = route_custom_data
```

**Projection:**
```json
{
  "run_id": 42,
  "target": "custom:data",
  "transforms_list": ["route_custom_data"],
  "sedcmds": [
    "s/password=\\S+/password=***MASKED***/g",
    "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g"
  ],
  "kv": null
}
```

**Source (complex transform chains):**
```ini
[json:api]
INDEXED_EXTRACTIONS = json
KV_MODE = json
TRANSFORMS-routing = route_by_severity, route_by_client
TRANSFORMS-cleanup = cleanup_fields, normalize_timestamps, add_metadata
```

**Projection:**
```json
{
  "run_id": 42,
  "target": "json:api",
  "transforms_list": [
    "route_by_severity",
    "route_by_client",
    "cleanup_fields",
    "normalize_timestamps",
    "add_metadata"
  ],
  "sedcmds": null,
  "kv": {
    "INDEXED_EXTRACTIONS": "json",
    "KV_MODE": "json"
  }
}
```

**Source (repeated TRANSFORMS keys with last-wins):**
```ini
[multi:transform]
TRANSFORMS-first = transform_a
TRANSFORMS-second = transform_b
TRANSFORMS-first = transform_a_override
```

**Projection:**
```json
{
  "run_id": 42,
  "target": "multi:transform",
  "transforms_list": ["transform_a_override", "transform_b"],
  "sedcmds": null,
  "kv": null
}
```

### transforms.conf Stanza Mapping

**Source (index routing transform):**
```ini
[route_to_index]
REGEX = level=ERROR
DEST_KEY = _MetaData:Index
FORMAT = error_index
```

**Projection (transforms table record):**
```json
{
  "run_id": 42,
  "name": "route_to_index",
  "dest_key": "_MetaData:Index",
  "regex": "level=ERROR",
  "format": "error_index",
  "writes_meta_index": true,
  "writes_meta_sourcetype": false,
  "kv": null
}
```

**Source (sourcetype override):**
```ini
[override_sourcetype]
REGEX = .
DEST_KEY = MetaData:Sourcetype
FORMAT = sourcetype::overridden:log
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "override_sourcetype",
  "dest_key": "MetaData:Sourcetype",
  "regex": ".",
  "format": "sourcetype::overridden:log",
  "writes_meta_index": false,
  "writes_meta_sourcetype": true,
  "kv": null
}
```

**Source (field extraction):**
```ini
[extract_special_fields]
REGEX = ^(?P<event_id>\d+)\s+(?P<severity>\w+)
FORMAT = event_id::$1 severity::$2
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "extract_special_fields",
  "dest_key": null,
  "regex": "^(?P<event_id>\\d+)\\s+(?P<severity>\\w+)",
  "format": "event_id::$1 severity::$2",
  "writes_meta_index": null,
  "writes_meta_sourcetype": null,
  "kv": null
}
```

**Source (data masking with additional properties):**
```ini
[mask_sensitive_data]
REGEX = (password|ssn|credit_card)=(\S+)
FORMAT = $1=***MASKED***
DEST_KEY = _raw
PRIORITY = 100
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "mask_sensitive_data",
  "dest_key": "_raw",
  "regex": "(password|ssn|credit_card)=(\\S+)",
  "format": "$1=***MASKED***",
  "writes_meta_index": false,
  "writes_meta_sourcetype": false,
  "kv": {
    "PRIORITY": "100"
  }
}
```

**Source (lookup transform):**
```ini
[lookup_transform]
filename = lookup.csv
max_matches = 1
min_matches = 1
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "lookup_transform",
  "dest_key": null,
  "regex": null,
  "format": null,
  "writes_meta_index": null,
  "writes_meta_sourcetype": null,
  "kv": {
    "filename": "lookup.csv",
    "max_matches": "1",
    "min_matches": "1"
  }
}
```

### indexes.conf Stanza Mapping

**Source (default index settings):**
```ini
[default]
frozenTimePeriodInSecs = 188697600
# 6 years
maxTotalDataSizeMB = 500000
homePath = $SPLUNK_DB/$_index_name/db
coldPath = $SPLUNK_DB/$_index_name/colddb
thawedPath = $SPLUNK_DB/$_index_name/thaweddb
```

**Projection (indexes table record):**
```json
{
  "run_id": 42,
  "name": "default",
  "kv": {
    "frozenTimePeriodInSecs": "188697600",
    "maxTotalDataSizeMB": "500000",
    "homePath": "$SPLUNK_DB/$_index_name/db",
    "coldPath": "$SPLUNK_DB/$_index_name/colddb",
    "thawedPath": "$SPLUNK_DB/$_index_name/thaweddb"
  }
}
```

**Source (main index):**
```ini
[main]
homePath = $SPLUNK_DB/defaultdb/db
coldPath = $SPLUNK_DB/defaultdb/colddb
thawedPath = $SPLUNK_DB/defaultdb/thaweddb
maxTotalDataSizeMB = 1000000
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "main",
  "kv": {
    "homePath": "$SPLUNK_DB/defaultdb/db",
    "coldPath": "$SPLUNK_DB/defaultdb/colddb",
    "thawedPath": "$SPLUNK_DB/defaultdb/thaweddb",
    "maxTotalDataSizeMB": "1000000"
  }
}
```

**Source (metrics index):**
```ini
[metrics]
datatype = metric
frozenTimePeriodInSecs = 7776000
# 90 days
maxTotalDataSizeMB = 50000
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "metrics",
  "kv": {
    "datatype": "metric",
    "frozenTimePeriodInSecs": "7776000",
    "maxTotalDataSizeMB": "50000"
  }
}
```

**Source (custom app index with advanced settings):**
```ini
[app_index]
homePath = /fast-storage/splunk/app_index/db
coldPath = /archive-storage/splunk/app_index/colddb
thawedPath = /archive-storage/splunk/app_index/thaweddb
frozenTimePeriodInSecs = 31536000
# 1 year
maxTotalDataSizeMB = 250000
maxHotBuckets = 10
maxWarmDBCount = 300
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "app_index",
  "kv": {
    "homePath": "/fast-storage/splunk/app_index/db",
    "coldPath": "/archive-storage/splunk/app_index/colddb",
    "thawedPath": "/archive-storage/splunk/app_index/thaweddb",
    "frozenTimePeriodInSecs": "31536000",
    "maxTotalDataSizeMB": "250000",
    "maxHotBuckets": "10",
    "maxWarmDBCount": "300"
  }
}
```

**Source (audit index with frozen archive):**
```ini
[audit]
homePath = $SPLUNK_DB/audit/db
coldPath = $SPLUNK_DB/audit/colddb
frozenTimePeriodInSecs = 315360000
# 10 years
coldToFrozenDir = /compliance-archive/audit
```

**Projection:**
```json
{
  "run_id": 42,
  "name": "audit",
  "kv": {
    "homePath": "$SPLUNK_DB/audit/db",
    "coldPath": "$SPLUNK_DB/audit/colddb",
    "frozenTimePeriodInSecs": "315360000",
    "coldToFrozenDir": "/compliance-archive/audit"
  }
}
```

### outputs.conf Stanza Mapping

**Source (default tcpout settings):**
```ini
[tcpout]
defaultGroup = primary_indexers
forwardedindex.filter.disable = true
indexAndForward = false
```

**Projection (outputs table record):**
```json
{
  "run_id": 42,
  "group_name": "tcpout",
  "servers": null,
  "kv": {
    "defaultGroup": "primary_indexers",
    "forwardedindex.filter.disable": "true",
    "indexAndForward": "false"
  }
}
```

**Source (TCP output group with load balancing):**
```ini
[tcpout:primary_indexers]
server = indexer1.example.com:9997, indexer2.example.com:9997, indexer3.example.com:9997
autoLBFrequency = 30
maxQueueSize = 10MB
compressed = true
```

**Projection:**
```json
{
  "run_id": 42,
  "group_name": "tcpout:primary_indexers",
  "servers": {
    "server": "indexer1.example.com:9997, indexer2.example.com:9997, indexer3.example.com:9997"
  },
  "kv": {
    "autoLBFrequency": "30",
    "maxQueueSize": "10MB",
    "compressed": "true"
  }
}
```

**Source (syslog output):**
```ini
[syslog:siem_output]
server = siem.example.com:514
type = tcp
priority = <134>
```

**Projection:**
```json
{
  "run_id": 42,
  "group_name": "syslog:siem_output",
  "servers": {
    "server": "siem.example.com:514"
  },
  "kv": {
    "type": "tcp",
    "priority": "<134>"
  }
}
```

**Source (HTTP Event Collector output):**
```ini
[httpout:hec_output]
uri = https://hec.splunkcloud.com:8088/services/collector
token = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
sslVerifyServerCert = true
```

**Projection:**
```json
{
  "run_id": 42,
  "group_name": "httpout:hec_output",
  "servers": {
    "uri": "https://hec.splunkcloud.com:8088/services/collector"
  },
  "kv": {
    "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "sslVerifyServerCert": "true"
  }
}
```

**Source (clone group with target_group):**
```ini
[tcpout:clone_group]
target_group = primary_indexers, backup_indexers
```

**Projection:**
```json
{
  "run_id": 42,
  "group_name": "tcpout:clone_group",
  "servers": {
    "target_group": "primary_indexers, backup_indexers"
  },
  "kv": null
}
```

**Source (last-wins semantics with repeated server):**
```ini
[tcpout:dynamic_group]
server = old1.example.com:9997
server = old2.example.com:9997
server = new1.example.com:9997, new2.example.com:9997
```

**Projection:**
```json
{
  "run_id": 42,
  "group_name": "tcpout:dynamic_group",
  "servers": {
    "server": "new1.example.com:9997, new2.example.com:9997"
  },
  "kv": null
}
```

## References

- Milestone 2 Plan: `notes/milestone-2-plan.md`
- Database Schema: `notes/database-schema.md`
- Splunk Configuration File Precedence: [Splunk Docs](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Wheretofindtheconfigurationfiles)
- PostgreSQL JSONB: [PostgreSQL Docs](https://www.postgresql.org/docs/current/datatype-json.html)
- Input Projector Implementation: `backend/app/projections/inputs.py`
- Transform Projector Implementation: `backend/app/projections/transforms.py`
- Index Projector Implementation: `backend/app/projections/indexes.py`

## Processing Model and Error Handling

### Ingestion Run Lifecycle

The `ingestion_runs` table tracks the complete lifecycle of configuration uploads from initial creation through parsing completion or failure.

#### Status Flow

The ingestion run transitions through the following states:

```
                    ┌─────────┐
                    │ PENDING │  Run created, file upload in progress
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ STORED  │  File stored successfully, parsing queued
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ PARSING │  Parsing job in progress, extracting stanzas
                    └────┬────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ NORMALIZED   │  Stanzas parsed, typed projections created
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  COMPLETE    │  Fully processed and validated
                  └──────────────┘

Note: At any stage from STORED through NORMALIZED, the run can transition to FAILED
if an error occurs (shown below):

                  STORED / PARSING / NORMALIZED
                         │
                         ├──────► FAILED  (on error)
```

**Status Descriptions**:

- **PENDING**: Run created, file upload in progress
- **STORED**: File stored successfully in storage backend, parsing job queued
- **PARSING**: Worker is extracting and parsing .conf files into stanzas
- **NORMALIZED**: Stanzas have been parsed and typed projections created
- **COMPLETE**: All processing complete, metrics stored, ready for queries
- **FAILED**: Upload, storage, parsing, or normalization failed (see error_message)

#### API Endpoints for Status

The following endpoints enable monitoring and management of run status:

**GET /v1/runs/{run_id}/status** - Get current status and summary
```bash
curl http://localhost:8000/v1/runs/42/status
```

Response:
```json
{
  "run_id": 42,
  "status": "complete",
  "error_message": null,
  "summary": {
    "files_parsed": 15,
    "stanzas_created": 234,
    "typed_projections": {
      "inputs": 45,
      "props": 32,
      "transforms": 28,
      "indexes": 8,
      "outputs": 12,
      "serverclasses": 3
    },
    "parse_errors": 0,
    "duration_seconds": 12.5
  }
}
```

**PATCH /v1/runs/{run_id}/status** - Update status (admin/debug only)
```bash
curl -X PATCH http://localhost:8000/v1/runs/42/status \
  -H "Content-Type: application/json" \
  -d '{"status": "failed", "error_message": "Manual intervention required"}'
```

Response:
```json
{
  "run_id": 42,
  "status": "failed",
  "error_message": "Manual intervention required",
  "summary": null
}
```

**Note**: The PATCH endpoint is intended for administrative and debugging purposes only.
Normal status transitions occur automatically through the worker pipeline.

#### Enhanced Tracking Fields

The ingestion run model includes comprehensive tracking for retry and error handling:

| Field | Type | Purpose |
|-------|------|---------|
| `task_id` | VARCHAR(255) | Celery task ID for async processing |
| `retry_count` | INTEGER | Number of retry attempts (0-3) |
| `error_message` | TEXT | High-level error description |
| `error_traceback` | TEXT | Full Python stack trace for debugging |
| `last_heartbeat` | TIMESTAMP | Last activity timestamp for timeout detection |
| `started_at` | TIMESTAMP | Task execution start time |
| `completed_at` | TIMESTAMP | Task completion time (success or failure) |
| `metrics` | JSONB | Execution metrics (duration, counts, error type) |

#### Error Classification

Parsing errors are classified into two categories:

**Permanent Errors** (no retry):
- Malformed or corrupted archives
- Unsupported archive formats (not .tar.gz, .tar, or .zip)
- Missing required data (no files in run)
- Invalid configuration structure

**Transient Errors** (retry with exponential backoff):
- Network connectivity issues
- Database connection timeouts
- Storage backend temporary failures
- Resource unavailability

#### Retry Behavior

- **Max Retries**: 3 attempts
- **Backoff Schedule**: 60s, 180s, 600s (exponential)
- **Idempotency**: Tasks can be safely retried without creating duplicate stanzas
- **Heartbeat**: Long-running tasks update `last_heartbeat` every 30 seconds

#### Metrics Collection

The `metrics` JSONB field stores execution data:

```json
{
  "files_parsed": 15,
  "stanzas_created": 234,
  "typed_projections": {
    "inputs": 45,
    "props": 32,
    "transforms": 28,
    "indexes": 8,
    "outputs": 12,
    "serverclasses": 3
  },
  "duration_seconds": 45.5,
  "parse_errors": 2,
  "retry_count": 1,
  "error_type": "transient"
}
```

These metrics are exposed via the `/v1/runs/{run_id}/status` endpoint for monitoring
and debugging purposes.

### Idempotency Guarantees

The parsing process is designed to be idempotent:

1. **Completed Run Check**: Tasks skip processing if run status is already `COMPLETE`
2. **Duplicate Detection**: Stanzas are checked for existence before insertion
3. **Atomic Operations**: Database commits occur only after successful parsing
4. **Retry Safety**: Failed tasks can be retried without side effects

### Error Recovery

**For Failed Runs**:
1. Review error details via `/v1/worker/runs/{run_id}/status`
2. Check `error_message` for high-level description
3. Examine `error_traceback` for detailed debugging
4. If permanent error: fix input data and re-upload
5. If transient error exhausted: verify infrastructure and retry

**Monitoring Failed Jobs**:
```bash
# Get recent failures
curl http://localhost:8000/v1/worker/metrics

# Check specific run
curl http://localhost:8000/v1/worker/runs/{run_id}/status
```

### Performance Considerations

- **Heartbeat Overhead**: Minimal - updates only every 30s
- **Metrics Storage**: JSONB indexed for efficient queries
- **Retry Impact**: Exponential backoff prevents thundering herd
- **Idempotency Cost**: Duplicate check uses indexed fields (run_id, file_id, name, source_path)

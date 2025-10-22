# Typed Projections

This module contains projectors that transform generic parsed stanzas from the parser into typed database records.

## Overview

The typed projection layer sits between the parser and the database, extracting domain-specific fields from generic stanzas into typed columns while preserving additional properties in JSONB.

```
┌──────────────┐
│   Parser     │
│   Core       │
└──────┬───────┘
       │ ParsedStanza[]
       ▼
┌──────────────┐
│  Projector   │ ──► Extract common fields
│   Layer      │ ──► Normalize values  
└──────┬───────┘ ──► Preserve metadata
       │ dict[]
       ▼
┌──────────────┐
│   Database   │
│   Models     │
└──────────────┘
```

## Implemented Projectors

### InputProjector

Projects `inputs.conf` stanzas to the `inputs` table.

**Extracted Fields:**
- `stanza_type`: Input type from stanza name (monitor, tcp, udp, script, WinEventLog, etc.)
- `index`: Target index for events
- `sourcetype`: Event sourcetype
- `disabled`: Boolean flag (normalized from string values)
- `kv`: Additional properties (JSONB)
- Provenance: `app`, `scope`, `layer`, `source_path`

**Example:**

```python
from app.parser import ConfParser
from app.projections import InputProjector

# Parse inputs.conf
parser = ConfParser()
stanzas = parser.parse_file("path/to/inputs.conf")

# Project to Input records
projector = InputProjector()
for stanza in stanzas:
    input_data = projector.project(stanza, run_id=1)
    # input_data is ready for Input model instantiation
```

**Supported Input Types:**
- `monitor://` - File/directory monitoring
- `tcp://` - TCP network inputs
- `udp://` - UDP network inputs
- `script://` - Script-based inputs
- `WinEventLog://` - Windows Event Log
- `splunktcp://` - Splunk-to-Splunk forwarding
- `http://` - HTTP Event Collector
- `fifo://` - Named pipe inputs
- And others

**Edge Cases:**
- Default stanza (`[default]`) has `stanza_type = NULL`
- Missing provenance defaults to NULL or `<unknown>`
- Empty kv is stored as NULL
- Disabled field accepts: "0"/"1", "true"/"false", "yes"/"no" (case-insensitive)

See `test_input_projector.py` for comprehensive test coverage.

### TransformProjector

Projects `transforms.conf` stanzas to the `transforms` table.

**Extracted Fields:**
- `name`: Transform name from stanza header
- `dest_key`: DEST_KEY value (if specified)
- `regex`: REGEX pattern (if specified)
- `format`: FORMAT template (if specified)
- `writes_meta_index`: Boolean - true if DEST_KEY = `_MetaData:Index` (case-insensitive)
- `writes_meta_sourcetype`: Boolean - true if DEST_KEY = `MetaData:Sourcetype` or `_MetaData:Sourcetype` (case-insensitive)
- `kv`: Additional properties (JSONB)

**Example:**

```python
from app.parser import ConfParser
from app.projections import TransformProjector

# Parse transforms.conf
parser = ConfParser()
stanzas = parser.parse_file("path/to/transforms.conf")

# Project to Transform records
projector = TransformProjector()
for stanza in stanzas:
    transform_data = projector.project(stanza, run_id=1)
    # transform_data is ready for Transform model instantiation
```

**Supported Transform Types:**
- Index routing (`_MetaData:Index`)
- Sourcetype routing (`MetaData:Sourcetype`, `_MetaData:Sourcetype`)
- Field extractions (REGEX + FORMAT)
- Data masking/rewriting (`_raw`)
- Queue routing (`queue`)
- Lookup-based transforms

**Edge Cases:**
- DEST_KEY is case-insensitive for metadata detection
- Missing fields result in NULL values
- Empty kv is stored as NULL
- All non-extracted fields go to kv JSONB
- Parser handles multi-line REGEX with continuations

See `test_transform_projector.py` for comprehensive test coverage.

### IndexProjector

Projects `indexes.conf` stanzas to the `indexes` table.

**Extracted Fields:**
- `name`: Index name from stanza header (e.g., "main", "app_index", "metrics")
- `kv`: All index configuration properties (JSONB)

**Example:**

```python
from app.parser import ConfParser
from app.projections import IndexProjector

# Parse indexes.conf
parser = ConfParser()
stanzas = parser.parse_file("path/to/indexes.conf")

# Project to Index records
projector = IndexProjector()
for stanza in stanzas:
    index_data = projector.project(stanza, run_id=1)
    # index_data is ready for Index model instantiation
```

**Supported Index Types:**
- Event indexes (default datatype)
- Metrics indexes (`datatype = metric`)
- Custom indexes with various retention and storage settings

**Common Index Properties in kv:**
- `homePath`: Path to hot/warm buckets
- `coldPath`: Path to cold buckets
- `thawedPath`: Path to thawed buckets
- `frozenTimePeriodInSecs`: Retention period in seconds
- `maxTotalDataSizeMB`: Maximum index size in MB
- `maxHotBuckets`: Number of hot buckets
- `maxWarmDBCount`: Maximum warm buckets
- `datatype`: "event" (default) or "metric"
- `coldToFrozenDir`: Archive path for frozen data
- `compressRawdata`: Whether to compress raw data
- `repFactor`: Replication factor (cluster mode)
- And many more...

**Edge Cases:**
- Default stanza (`[default]`) sets defaults for all indexes
- Empty kv is stored as NULL
- Index names preserved exactly (including underscores, numbers)
- All properties stored in JSONB for maximum flexibility
- Supports Splunk variables like `$SPLUNK_DB` and `$_index_name`
- Handles Windows and Unix path styles

**Projection Implementation**: `app/projections/indexes.py` - `IndexProjector` class

See `test_index_projector.py` and `test_index_projector_integration.py` for comprehensive test coverage.

### OutputProjector

Projects `outputs.conf` stanzas to the `outputs` table.

**Extracted Fields:**
- `group_name`: Output group name from stanza header
- `servers`: Server configurations (JSONB) - includes `server`, `uri`, `target_group`
- `kv`: Additional properties (JSONB)

**Example:**

```python
from app.parser import ConfParser
from app.projections.outputs import OutputProjector

# Parse outputs.conf
parser = ConfParser()
stanzas = parser.parse_file("path/to/outputs.conf")

# Project to Output records
projector = OutputProjector()
for stanza in stanzas:
    output_data = projector.project(stanza, run_id=1)
    # output_data is ready for Output model instantiation
```

**Supported Output Types:**
- `tcpout` - TCP forwarding to indexers
- `tcpout:<group>` - Named TCP output groups
- `syslog:<name>` - Syslog forwarding
- `httpout:<name>` - HTTP Event Collector (HEC) forwarding
- And others

**Servers JSONB Structure:**
- `server`: Comma-separated list of server:port pairs (for tcpout, syslog)
- `uri`: HTTP(S) URI for HEC outputs
- `target_group`: Reference to other output groups (for cloning/routing)

**Common Properties in kv:**
- `compressed`: Whether to compress data
- `autoLBFrequency`: Load balancing frequency in seconds
- `maxQueueSize`: Maximum queue size
- `defaultGroup`: Default output group (in `[tcpout]` stanza)
- `indexAndForward`: Whether to index locally and forward
- `token`: Authentication token (for HEC)
- `sslVerifyServerCert`: SSL certificate verification
- `type`: Output type (tcp/udp for syslog)
- `priority`: Syslog priority
- And many more...

**Edge Cases:**
- Default stanza (`[tcpout]`) has `servers = NULL` (no server field)
- Empty servers is stored as NULL
- Empty kv is stored as NULL
- Multiple server values use last-wins semantics
- Comma-separated server lists are preserved as single string
- `target_group` refers to other output groups for cloning

**Projection Implementation**: `app/projections/outputs.py` - `OutputProjector` class

See `test_output_projector.py` and `test_output_projector_integration.py` for comprehensive test coverage.

## Future Projectors

The following projectors are planned:

- **PropsProjector**: Projects `props.conf` stanzas
- **ServerclassProjector**: Projects `serverclass.conf` stanzas

## Design Principles

1. **Lossless Projection**: No data is lost; everything not in typed columns goes to kv JSONB
2. **Provenance Preservation**: All source metadata is maintained
3. **Type Safety**: Values are normalized to appropriate Python types
4. **Testability**: Each projector has comprehensive unit and integration tests
5. **Performance**: Projections are fast, single-pass operations

## Testing

Each projector should have:

1. **Unit Tests**: Test individual methods (extraction, normalization, etc.)
2. **Integration Tests**: Test with real fixture files
3. **Property Tests**: Verify invariants (provenance preservation, run_id consistency, etc.)
4. **Edge Case Tests**: Empty stanzas, missing fields, special characters, etc.

Run tests:

```bash
# Unit tests
python backend/tests/projections/test_input_projector.py

# Integration tests
python backend/tests/projections/test_input_projector_integration.py

# Or use pytest
pytest backend/tests/projections/
```

## Documentation

For detailed mapping logic and examples, see:
- [Normalization Model](../../../docs/normalization-model.md)
- [Milestone 2 Gap Analysis](../../../notes/milestone-2-gap-analysis.md)

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

### ServerclassProjector

Projects `serverclass.conf` stanzas to the `serverclasses` table.

**Extracted Fields:**
- `name`: Serverclass name from stanza header (e.g., "production", "universal_forwarders")
- `whitelist`: JSONB dictionary of whitelist patterns (from `whitelist.N` keys)
- `blacklist`: JSONB dictionary of blacklist patterns (from `blacklist.N` keys)
- `app_assignments`: JSONB dictionary of app assignments (reserved for future, currently NULL)
- `kv`: Additional properties (JSONB)

**Example:**

```python
from app.parser import ConfParser
from app.projections import ServerclassProjector

# Parse serverclass.conf
parser = ConfParser()
stanzas = parser.parse_file("path/to/serverclass.conf")

# Project to Serverclass records
projector = ServerclassProjector()
for stanza in stanzas:
    serverclass_data = projector.project(stanza, run_id=1)
    # serverclass_data is ready for Serverclass model instantiation
```

**Supported Stanza Types:**
- `serverClass:name` - Serverclass definitions with targeting rules
- `serverClass:name:app:appname` - App assignments (identified but not projected)
- `global` - Global settings (skipped)

**Common Properties in kv:**
- `restartSplunkd`: Whether to restart Splunkd on deployment
- `restartSplunkWeb`: Whether to restart SplunkWeb on deployment
- `stateOnClient`: Deployment state (enabled/disabled/noop)
- `machineTypesFilter`: OS/architecture filter (e.g., "linux-x86_64")
- `repositoryLocation`: Custom app repository path
- `targetRepositoryLocation`: Target location on client
- `continueMatching`: Whether to continue matching other serverclasses
- And many more...

**Edge Cases:**
- Global stanza (`[global]`) is not projected (returns None)
- App assignment stanzas are not projected (returns None, reserved for future)
- Whitelist/blacklist patterns are extracted from numbered keys (`whitelist.0`, `whitelist.1`, etc.)
- Non-sequential numbers are preserved in the JSONB dictionary
- Last-wins semantics apply for duplicate numbers
- Empty whitelist/blacklist stored as NULL
- Empty kv stored as NULL

**Projection Implementation**: `app/projections/serverclasses.py` - `ServerclassProjector` class

See `test_serverclass_projector.py` and `test_serverclass_projector_integration.py` for comprehensive test coverage.

## Future Projectors

The following projectors are planned:

- **PropsProjector**: Projects `props.conf` stanzas
- **OutputProjector**: Projects `outputs.conf` stanzas

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

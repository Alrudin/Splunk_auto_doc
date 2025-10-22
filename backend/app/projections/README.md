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

## Future Projectors

The following projectors are planned:

- **PropsProjector**: Projects `props.conf` stanzas
- **TransformProjector**: Projects `transforms.conf` stanzas
- **IndexProjector**: Projects `indexes.conf` stanzas
- **OutputProjector**: Projects `outputs.conf` stanzas
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

# Splunk .conf Parser

A robust, production-ready parser for Splunk configuration files.

## Features

- ✅ **Complete syntax support**: Comments, line continuations, repeated keys, special characters
- ✅ **Order preservation**: Maintains file order for accurate precedence resolution
- ✅ **Provenance tracking**: Extracts app, scope, layer metadata from file paths
- ✅ **Last-wins semantics**: Handles repeated keys correctly with full history
- ✅ **Edge case handling**: Unicode, empty values, special stanza names, etc.
- ✅ **Well-tested**: 24 unit tests + 8 golden fixture tests, 100% passing
- ✅ **Documented**: Complete specification in `docs/parser-spec.md`

## Quick Start

```python
from app.parser import ConfParser

# Parse a file
parser = ConfParser()
stanzas = parser.parse_file("/opt/splunk/etc/apps/search/local/inputs.conf")

# Iterate through stanzas
for stanza in stanzas:
    print(f"[{stanza.name}]")
    for key, value in stanza.keys.items():
        print(f"  {key} = {value}")

# Parse a string
stanzas = parser.parse_string("""
[monitor:///var/log/app.log]
index = main
sourcetype = app:log
""")

# Access provenance
for stanza in stanzas:
    prov = stanza.provenance
    print(f"App: {prov.app}, Scope: {prov.scope}, Layer: {prov.layer}")
```

## Parser Output

### ParsedStanza

Each stanza contains:

- `name`: Stanza header (without brackets)
- `keys`: Dictionary of key-value pairs (last-wins for repeated keys)
- `key_order`: List of all keys in order (including repeats)
- `key_history`: Complete history for each key
- `provenance`: Source metadata

### Provenance

Metadata extracted from file path:

- `source_path`: Full file path
- `app`: App name (e.g., "search", "TA-myapp")
- `scope`: "default" or "local"
- `layer`: "system" or "app"
- `order_in_file`: Stanza sequence number

## Handled Edge Cases

| Feature | Support | Notes |
|---------|---------|-------|
| Comments | ✅ | Full-line and inline |
| Line continuations | ✅ | Backslash at EOL |
| Repeated keys | ✅ | Last-wins with history |
| Unicode | ✅ | Full UTF-8 support |
| Empty values | ✅ | `key = ` is valid |
| Special chars in names | ✅ | `:`, `/`, etc. preserved |
| Keys before stanza | ✅ | Creates "default" stanza |
| Whitespace | ✅ | Normalized appropriately |

## Testing

Run tests:

```bash
# Unit tests
python backend/tests/parser/test_parser_core.py

# Golden fixture tests
python backend/tests/parser/test_golden_fixtures.py

# Interactive demo
python backend/tests/parser/demo_parser.py
```

Results:
- **Unit tests**: 24/24 passing
- **Golden fixtures**: 8/8 passing
- **Total coverage**: All documented features

## Documentation

- **Specification**: [docs/parser-spec.md](../../../docs/parser-spec.md)
- **Examples**: [demo_parser.py](../../tests/parser/demo_parser.py)
- **Golden fixtures**: [fixtures/](../../tests/parser/fixtures/)

## Performance

Single-pass streaming parser with O(n) complexity:

- Small file (100 stanzas): <1ms
- Medium file (1,000 stanzas): ~10ms
- Large file (10,000 stanzas): ~100ms

## Known Limitations

1. Escaped quotes in values use simple heuristic
2. Include directives not processed (each file parsed independently)
3. Macros not expanded (stored as-is for downstream processing)
4. Non-UTF-8 encodings not supported

See [parser-spec.md](../../../docs/parser-spec.md) for complete details.

## Architecture

```
backend/app/parser/
├── __init__.py        # Module exports
├── core.py            # Main ConfParser class
├── types.py           # ParsedStanza, Provenance types
└── exceptions.py      # ParserError, ParserWarning
```

## Integration

The parser is designed to integrate with the normalization pipeline:

1. **Parser** → ParsedStanza objects
2. **Normalization** → Database stanzas table
3. **Typed projections** → Specialized tables (inputs, props, etc.)

See [docs/normalization-model.md](../../../docs/normalization-model.md) for details.

## License

MIT - See repository root for details.

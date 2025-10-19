# Parser Specification

**Document Version:** 1.0  
**Status:** Active  
**Last Updated:** 2025-10-19

## Overview

This document specifies the behavior of the Splunk .conf file parser implemented for Milestone 2. The parser is designed to handle all nuances of Splunk configuration syntax while preserving complete provenance metadata and maintaining deterministic, reproducible results.

## Goals

1. **Correctness**: Parse all valid Splunk .conf files accurately
2. **Provenance**: Track source location and context for every configuration item
3. **Order Preservation**: Maintain stanza and key ordering for precedence resolution
4. **Evidence**: Record complete history of repeated keys for debugging
5. **Error Recovery**: Handle malformed input gracefully when possible

## Splunk .conf File Format

### Basic Structure

Splunk .conf files follow an INI-like format with these elements:

```
# Comments start with hash
[stanza_header]
key1 = value1
key2 = value2

[another_stanza]
key3 = value3
```

### Grammar (Informal EBNF)

```ebnf
conf_file     ::= line*
line          ::= comment | stanza_header | key_value | blank_line
comment       ::= '#' any_text
stanza_header ::= '[' stanza_name ']'
key_value     ::= key '=' value
key           ::= non_equals_chars
value         ::= any_text
blank_line    ::= whitespace*
```

## Parser Features

### 1. Comments

**Syntax**: Lines starting with `#` (with optional leading whitespace)

**Behavior**:
- Full-line comments are ignored completely
- Inline comments (# after a value) are removed from the value
- Hash symbols within quotes are preserved (simple heuristic)

**Examples**:
```ini
# This is a full-line comment
key1 = value1  # inline comment removed
key2 = "value with # preserved"
```

**Edge Cases**:
- The inline comment heuristic uses quote detection
- Nested or escaped quotes may not be handled perfectly
- When in doubt, the parser preserves the value

### 2. Line Continuation

**Syntax**: Backslash `\` at end of line

**Behavior**:
- Trailing backslash causes next line to be merged
- Backslash is removed, lines are concatenated
- Multiple continuations are supported
- Whitespace from continuation lines is preserved

**Examples**:
```ini
key = value1 \
continued \
more continuation
# Result: key = value1 continued more continuation

path = /very/long/path/\
to/some/file
# Result: path = /very/long/path/to/some/file
```

**Edge Cases**:
- Backslash in quoted strings: Not specially handled (limitation)
- Continuation from within comments: Comment continues

### 3. Stanza Headers

**Syntax**: `[stanza_name]` on its own line

**Behavior**:
- Starts a new stanza, finalizing any previous stanza
- Stanza name is trimmed of leading/trailing whitespace
- Special characters in stanza names are preserved
- Empty stanzas (no keys) are valid

**Examples**:
```ini
[simple]
[monitor:///var/log/app.log]
[tcp://9997]
[ stanza with spaces ]
# Result: stanza name is "stanza with spaces"
```

**Edge Cases**:
- Brackets in stanza names: Not supported (would break parsing)
- Multiple stanzas with same name: Both preserved (distinct objects)

### 4. Key-Value Pairs

**Syntax**: `key = value`

**Behavior**:
- First `=` separates key from value
- Key is trimmed of leading/trailing whitespace
- Value is trimmed of leading/trailing whitespace
- Additional `=` in value are preserved
- Empty values are valid

**Examples**:
```ini
key1 = value1
  key2  =  value2  
# Both result in trimmed key/value

key3 = value=with=equals
# Result: key3 = value=with=equals

empty_key = 
# Result: empty_key = ""
```

**Edge Cases**:
- Keys before any stanza header: Placed in a "default" stanza
- Malformed lines (no `=`): Silently ignored

### 5. Repeated Keys

**Syntax**: Same key appearing multiple times in one stanza

**Behavior**:
- **Last-wins**: Final value is the last occurrence
- **History preserved**: All values recorded in `key_history`
- **Order tracked**: `key_order` lists all keys including repeats

**Examples**:
```ini
[stanza]
key1 = first
key2 = value2
key1 = second
key1 = third
# Result: 
#   keys["key1"] = "third" (last-wins)
#   key_history["key1"] = ["first", "second", "third"]
#   key_order = ["key1", "key2", "key1", "key1"]
```

**Rationale**:
- Splunk uses last-wins for effective configuration
- History enables evidence collection and debugging
- Order enables accurate precedence calculation

### 6. Provenance Tracking

**Metadata Extracted**:

| Field | Source | Example |
|-------|--------|---------|
| `source_path` | File path | `/opt/splunk/etc/apps/search/local/inputs.conf` |
| `app` | Path pattern | `search` |
| `scope` | Path pattern | `local` or `default` |
| `layer` | Path pattern | `app` or `system` |
| `order_in_file` | Parse sequence | `0`, `1`, `2`, ... |

**Path Patterns**:

```
# App configuration
/opt/splunk/etc/apps/{app}/{scope}/{conf}.conf
  -> app="{app}", scope="{scope}", layer="app"

# System configuration  
/opt/splunk/etc/system/{scope}/{conf}.conf
  -> app=None, scope="{scope}", layer="system"
```

**Example**:
```python
provenance = Provenance(
    source_path="/opt/splunk/etc/apps/TA-myapp/local/inputs.conf",
    app="TA-myapp",
    scope="local",
    layer="app",
    order_in_file=5
)
```

### 7. Whitespace Handling

**Rules**:
- Leading/trailing whitespace on keys: trimmed
- Leading/trailing whitespace on values: trimmed
- Whitespace within values: preserved
- Blank lines: ignored
- Whitespace-only lines: ignored

**Examples**:
```ini
   key1   =   value1   
# Result: key1 = value1

key2 = value with   spaces
# Result: key2 = value with   spaces
```

### 8. Character Encoding

**Supported**: UTF-8

**Behavior**:
- Unicode characters in keys and values are fully supported
- Files are opened with UTF-8 encoding
- Non-UTF-8 files will raise an error

**Examples**:
```ini
[日本語]
キー = 値
emoji = 🎉
```

## Parser Output

### ParsedStanza Object

```python
@dataclass
class ParsedStanza:
    name: str                          # Stanza header
    keys: dict[str, Any]               # Last-wins values
    key_order: list[str]               # All keys in order
    key_history: dict[str, list[Any]]  # Complete value history
    provenance: Provenance | None      # Source metadata
```

### Provenance Object

```python
@dataclass
class Provenance:
    source_path: str       # Full file path
    app: str | None        # App name
    scope: str | None      # default|local
    layer: str | None      # system|app
    order_in_file: int     # Stanza sequence number
```

## Known Splunk Quirks

### 1. Macros and Variables

**Splunk supports**: `$variable$`, `$(macro)`, `$ENV_VAR`

**Parser behavior**: Stored as-is, not expanded

**Rationale**: Macro expansion requires runtime context; stored for downstream processing

### 2. Disabled Stanzas

**Splunk supports**: `disabled = true` or `disabled = 1`

**Parser behavior**: Parses normally, downstream logic handles disabled state

### 3. Include Directives

**Splunk supports**: Some .conf files support `source = other.conf`

**Parser behavior**: Not implemented; each file parsed independently

### 4. Conf-specific Syntax

**Example**: `props.conf` TRANSFORMS-* keys, `serverclass.conf` whitelist.N patterns

**Parser behavior**: Generic parsing; typed interpretation in normalization layer

## Edge Cases and Limitations

### Handled Edge Cases

1. ✅ Empty files
2. ✅ Files with only comments
3. ✅ Stanzas with no keys
4. ✅ Keys before first stanza (creates "default" stanza)
5. ✅ Special characters in stanza names (`:`, `/`, etc.)
6. ✅ Equals signs in values
7. ✅ Empty values
8. ✅ Unicode/emoji in keys and values
9. ✅ Multiple stanzas with same name (both preserved)
10. ✅ Whitespace variations

### Known Limitations

1. ❌ Escaped quotes in values (limited heuristic)
2. ❌ Backslash in quoted strings (not special-cased)
3. ❌ Include directives not processed
4. ❌ Macro expansion not performed
5. ❌ Non-UTF-8 encodings not supported
6. ❌ Binary .conf files (if any exist)

### Error Handling

**Parser Philosophy**: Be lenient, preserve intent

**Strategies**:
- Malformed lines without `=`: Silently ignored
- Missing stanza before keys: Create "default" stanza
- Parse errors: Raise `ParserError` with context
- Invalid UTF-8: Raise encoding error (not recoverable)

## Performance Characteristics

**Algorithm**: Single-pass streaming parser

**Complexity**:
- Time: O(n) where n = file size in bytes
- Space: O(s + k) where s = number of stanzas, k = total keys

**Benchmarks** (estimated):
- Small file (100 stanzas, 1KB): <1ms
- Medium file (1,000 stanzas, 100KB): ~10ms
- Large file (10,000 stanzas, 1MB): ~100ms

**Optimizations**:
- Regex compilation happens once at class initialization
- String operations use built-in methods
- No backtracking or lookahead

## Testing Strategy

### Unit Tests

**Coverage**:
- Basic parsing (stanzas, keys, values)
- Comments (full-line, inline, in quotes)
- Line continuation (simple, multiple, with whitespace)
- Repeated keys (last-wins, history, order)
- Provenance extraction
- Edge cases (unicode, empty values, special chars)
- Property invariants (order preservation, last-wins semantic)

**Location**: `backend/tests/parser/test_parser_core.py`

### Golden Fixture Tests

**Purpose**: Validate against real-world configurations

**Fixtures**:
- `hf_inputs.conf`: Heavy Forwarder inputs
- `props.conf`: Props with transforms and SEDCMD
- `transforms.conf`: Index-time transformations
- `outputs.conf`: Forwarder outputs and groups
- `serverclass.conf`: Deployment Server configuration
- `indexes.conf`: Index definitions

**Location**: `backend/tests/parser/fixtures/`, `backend/tests/parser/test_golden_fixtures.py`

### Property Tests

**Invariants Tested**:
1. Stanza order = input order (not alphabetical)
2. Last-wins: repeated keys use final value
3. History: all values present in key_history
4. Order: key_order matches input sequence
5. Idempotency: parse(serialize(parse(x))) = parse(x)

**Location**: Integrated in `test_parser_core.py` (`TestPropertyInvariants`)

## Usage Examples

### Basic Parsing

```python
from app.parser import ConfParser

parser = ConfParser()
stanzas = parser.parse_file("/path/to/inputs.conf")

for stanza in stanzas:
    print(f"[{stanza.name}]")
    for key, value in stanza.keys.items():
        print(f"  {key} = {value}")
```

### Checking Provenance

```python
stanzas = parser.parse_file("/opt/splunk/etc/apps/search/local/inputs.conf")

for stanza in stanzas:
    prov = stanza.provenance
    print(f"{stanza.name}: app={prov.app}, scope={prov.scope}, order={prov.order_in_file}")
```

### Examining Repeated Keys

```python
stanzas = parser.parse_string("""
[test]
key1 = first
key1 = second
key1 = third
""")

stanza = stanzas[0]
print(f"Current value: {stanza.keys['key1']}")  # "third"
print(f"History: {stanza.key_history['key1']}")  # ["first", "second", "third"]
print(f"Order: {stanza.key_order}")  # ["key1", "key1", "key1"]
```

## Future Enhancements

**Potential Additions** (not in scope for M2):
1. Strict mode: fail on malformed lines instead of ignoring
2. Warning collection: report non-fatal issues (ambiguous syntax, deprecated patterns)
3. Include directive support: recursively parse referenced files
4. Macro expansion: resolve $variables$ with context
5. Schema validation: validate against known .conf types
6. Diff/merge utilities: compare parsed results, merge configurations
7. Serialization: convert ParsedStanza back to .conf format
8. Performance profiling: detailed metrics for large files

## References

- [Splunk Configuration Files Documentation](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Aboutconfigurationfiles)
- [Milestone 2 Plan](../notes/milestone-2-plan.md)
- [Normalization Model](normalization-model.md)
- [Project Description](../notes/Project%20description.md)

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-19 | 1.0 | Initial specification for M2 parser core |

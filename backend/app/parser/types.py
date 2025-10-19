"""Type definitions for the parser module."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Provenance:
    """Provenance metadata for a parsed stanza.
    
    Tracks the source location and context of a configuration stanza,
    enabling accurate precedence resolution and debugging.
    """

    source_path: str
    """Full path to the source .conf file"""

    app: str | None = None
    """App name extracted from path (e.g., 'search', 'TA-myapp')"""

    scope: str | None = None
    """Scope: 'default' or 'local'"""

    layer: str | None = None
    """Layer: 'system' or 'app'"""

    order_in_file: int = 0
    """Zero-based stanza sequence number within the file"""


@dataclass
class ParsedStanza:
    """Represents a single parsed stanza from a .conf file.
    
    A stanza consists of a header (in square brackets) followed by
    key-value pairs. This class preserves order and handles repeated keys.
    """

    name: str
    """Stanza header/name (without brackets)"""

    keys: dict[str, Any] = field(default_factory=dict)
    """Key-value pairs (last-wins for repeated keys)"""

    key_order: list[str] = field(default_factory=list)
    """Ordered list of all keys as they appeared (including repeats)"""

    key_history: dict[str, list[Any]] = field(default_factory=dict)
    """Complete history of values for each key (for evidence/debugging)"""

    provenance: Provenance | None = None
    """Source metadata"""

    def add_key(self, key: str, value: Any) -> None:
        """Add a key-value pair, handling repeats with last-wins semantics.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        # Record in order
        self.key_order.append(key)

        # Track history
        if key not in self.key_history:
            self.key_history[key] = []
        self.key_history[key].append(value)

        # Last-wins: update current value
        self.keys[key] = value

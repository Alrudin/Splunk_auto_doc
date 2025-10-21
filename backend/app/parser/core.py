"""Core parser implementation for Splunk .conf files.

This module implements the main parsing logic for Splunk configuration files,
handling all nuances including comments, line continuations, repeated keys,
whitespace handling, and provenance tracking.
"""

import re
from pathlib import Path
from typing import TextIO

from app.parser.exceptions import ParserError
from app.parser.types import ParsedStanza, Provenance


class ConfParser:
    """Parser for Splunk .conf configuration files.

    Handles:
    - Comments (lines starting with #)
    - Line continuations (trailing backslash)
    - Repeated keys (last-wins with full history)
    - Stanza ordering
    - Provenance metadata extraction
    - Whitespace normalization

    Example:
        parser = ConfParser()
        stanzas = parser.parse_file("/path/to/inputs.conf")
        for stanza in stanzas:
            print(f"Stanza: {stanza.name}")
            for key, value in stanza.keys.items():
                print(f"  {key} = {value}")
    """

    # Regex patterns
    STANZA_HEADER_PATTERN = re.compile(r"^\[([^\]]+)\]\s*$")
    KEY_VALUE_PATTERN = re.compile(r"^([^=]+?)\s*=\s*(.*)$")
    COMMENT_PATTERN = re.compile(r"^\s*#")
    CONTINUATION_PATTERN = re.compile(r"\\$")

    # Path patterns for provenance extraction
    PATH_PATTERN = re.compile(
        r"/(?:apps|system)/(?:(?P<app>[^/]+)/)?(?P<scope>default|local)/"
    )

    def __init__(self) -> None:
        """Initialize the parser."""
        self._current_stanza: ParsedStanza | None = None
        self._stanzas: list[ParsedStanza] = []
        self._stanza_counter = 0

    def parse_file(self, file_path: str | Path) -> list[ParsedStanza]:
        """Parse a Splunk .conf file and return ordered stanzas.

        Args:
            file_path: Path to the .conf file

        Returns:
            List of parsed stanzas in file order

        Raises:
            ParserError: If the file cannot be parsed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ParserError(f"File not found: {file_path}")

        provenance = self._extract_provenance(str(file_path))

        with open(file_path, encoding="utf-8") as f:
            return self._parse_stream(f, provenance)

    def parse_string(
        self, content: str, source_path: str = "<string>"
    ) -> list[ParsedStanza]:
        """Parse .conf content from a string.

        Args:
            content: Configuration file content
            source_path: Optional path for provenance (default: "<string>")

        Returns:
            List of parsed stanzas in order
        """
        provenance = self._extract_provenance(source_path)
        # lines = content.splitlines(keepends=True)

        # Create a file-like object from the lines
        from io import StringIO

        stream = StringIO(content)
        return self._parse_stream(stream, provenance)

    def _parse_stream(
        self, stream: TextIO, provenance: Provenance
    ) -> list[ParsedStanza]:
        """Parse a text stream into stanzas.

        Args:
            stream: Text stream to parse
            provenance: Source metadata

        Returns:
            List of parsed stanzas
        """
        self._current_stanza = None
        self._stanzas = []
        self._stanza_counter = 0

        line_buffer = ""
        line_num = 0

        for raw_line in stream:
            line_num += 1
            line = raw_line.rstrip("\n\r")

            # Handle line continuation
            if self.CONTINUATION_PATTERN.search(line):
                # Remove trailing backslash and accumulate
                line_buffer += line[:-1]
                continue

            # Append accumulated buffer
            line = line_buffer + line
            line_buffer = ""

            # Process the complete line
            self._process_line(line, provenance)

        # Finalize the last stanza
        if self._current_stanza:
            self._stanzas.append(self._current_stanza)

        return self._stanzas

    def _process_line(self, line: str, provenance: Provenance) -> None:
        """Process a single logical line (after continuation handling).

        Args:
            line: The line to process
            provenance: Source metadata
        """
        # Skip empty lines and comments
        if not line.strip() or self.COMMENT_PATTERN.match(line):
            return

        # Check for stanza header
        stanza_match = self.STANZA_HEADER_PATTERN.match(line)
        if stanza_match:
            # Finalize previous stanza
            if self._current_stanza:
                self._stanzas.append(self._current_stanza)

            # Start new stanza
            stanza_name = stanza_match.group(1).strip()
            self._current_stanza = ParsedStanza(
                name=stanza_name,
                provenance=Provenance(
                    source_path=provenance.source_path,
                    app=provenance.app,
                    scope=provenance.scope,
                    layer=provenance.layer,
                    order_in_file=self._stanza_counter,
                ),
            )
            self._stanza_counter += 1
            return

        # Check for key-value pair
        kv_match = self.KEY_VALUE_PATTERN.match(line)
        if kv_match:
            if self._current_stanza is None:
                # Key-value before any stanza header - create a default stanza
                self._current_stanza = ParsedStanza(
                    name="default",
                    provenance=Provenance(
                        source_path=provenance.source_path,
                        app=provenance.app,
                        scope=provenance.scope,
                        layer=provenance.layer,
                        order_in_file=self._stanza_counter,
                    ),
                )
                self._stanza_counter += 1

            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()

            # Remove inline comments (but preserve # in quoted values)
            value = self._remove_inline_comment(value)

            self._current_stanza.add_key(key, value)
            return

        # If we get here, it's a malformed line - ignore it
        # (Splunk is somewhat lenient with malformed lines)

    def _remove_inline_comment(self, value: str) -> str:
        """Remove inline comments from a value, preserving # in quotes.

        Args:
            value: The value to process

        Returns:
            Value with inline comment removed
        """
        # Simple heuristic: only remove # if not in quotes
        # This is a simplified version - Splunk's actual behavior is complex
        in_quotes = False
        for i, char in enumerate(value):
            if char in ('"', "'"):
                in_quotes = not in_quotes
            elif char == "#" and not in_quotes:
                # Found inline comment
                return value[:i].rstrip()
        return value

    def _extract_provenance(self, file_path: str) -> Provenance:
        """Extract provenance metadata from file path.

        Splunk config paths follow conventions like:
        - /opt/splunk/etc/apps/<app>/(default|local)/<conf>.conf
        - /opt/splunk/etc/system/(default|local)/<conf>.conf

        Args:
            file_path: Full path to the config file

        Returns:
            Provenance object with extracted metadata
        """
        provenance = Provenance(source_path=file_path)

        match = self.PATH_PATTERN.search(file_path)
        if match:
            provenance.app = match.group("app")
            provenance.scope = match.group("scope")

            # Determine layer
            if "/system/" in file_path:
                provenance.layer = "system"
            elif "/apps/" in file_path:
                provenance.layer = "app"

        return provenance

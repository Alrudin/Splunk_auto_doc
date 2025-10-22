"""Input projector for normalizing inputs.conf stanzas.

This module implements typed projection for Splunk inputs.conf stanzas,
extracting common fields into typed columns and preserving additional
properties in JSONB.
"""

import re
from typing import Any

from app.parser.types import ParsedStanza


class InputProjector:
    """Projects parsed inputs.conf stanzas to typed Input records.

    Handles various Splunk input types:
    - monitor:// - File/directory monitoring
    - tcp:// - TCP network inputs
    - udp:// - UDP network inputs
    - script:// - Script-based inputs
    - WinEventLog:// - Windows Event Log inputs
    - splunktcp:// - Splunk-to-Splunk forwarding
    - http:// - HTTP Event Collector
    - fifo:// - Named pipe inputs
    - And others

    Example:
        projector = InputProjector()
        input_data = projector.project(parsed_stanza, run_id=1)
        # Returns dict ready for Input model instantiation
    """

    # Regex pattern to extract stanza type from stanza name
    STANZA_TYPE_PATTERN = re.compile(r"^([^:]+)://")

    # Common extracted fields - these go into typed columns
    EXTRACTED_FIELDS = {"index", "sourcetype", "disabled"}

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any]:
        """Project a parsed stanza to an Input record dictionary.

        Args:
            stanza: Parsed stanza from inputs.conf
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for Input model:
            - run_id: Ingestion run ID
            - source_path: Path to source inputs.conf
            - stanza_type: Type of input (monitor, tcp, udp, etc.)
            - index: Target index (if specified)
            - sourcetype: Sourcetype (if specified)
            - disabled: Whether input is disabled
            - kv: Additional key-value pairs
            - app: App name from provenance
            - scope: Scope (default/local) from provenance
            - layer: Layer (system/app) from provenance
        """
        # Extract stanza type from stanza name
        stanza_type = self._extract_stanza_type(stanza.name)

        # Extract common fields
        index = stanza.keys.get("index")
        sourcetype = stanza.keys.get("sourcetype")
        disabled = self._normalize_disabled(stanza.keys.get("disabled"))

        # Build kv dict with remaining properties
        kv = self._build_kv(stanza.keys)

        # Build the projection
        projection: dict[str, Any] = {
            "run_id": run_id,
            "source_path": (
                stanza.provenance.source_path if stanza.provenance else "<unknown>"
            ),
            "stanza_type": stanza_type,
            "index": index,
            "sourcetype": sourcetype,
            "disabled": disabled,
            "kv": kv if kv else None,
            "app": stanza.provenance.app if stanza.provenance else None,
            "scope": stanza.provenance.scope if stanza.provenance else None,
            "layer": stanza.provenance.layer if stanza.provenance else None,
        }

        return projection

    def _extract_stanza_type(self, stanza_name: str) -> str | None:
        """Extract input type from stanza name.

        Args:
            stanza_name: Stanza header (e.g., "monitor:///var/log/app.log")

        Returns:
            Input type (e.g., "monitor", "tcp", "udp") or None if no type prefix

        Examples:
            >>> projector = InputProjector()
            >>> projector._extract_stanza_type("monitor:///var/log/app.log")
            'monitor'
            >>> projector._extract_stanza_type("tcp://9997")
            'tcp'
            >>> projector._extract_stanza_type("default")
            None
        """
        match = self.STANZA_TYPE_PATTERN.match(stanza_name)
        if match:
            return match.group(1).lower()
        return None

    def _normalize_disabled(self, value: Any) -> bool | None:
        """Normalize disabled field to boolean.

        Splunk uses string values "0", "1", "true", "false" (case-insensitive).

        Args:
            value: Raw disabled value from config

        Returns:
            Boolean representation or None if not specified

        Examples:
            >>> projector = InputProjector()
            >>> projector._normalize_disabled("0")
            False
            >>> projector._normalize_disabled("1")
            True
            >>> projector._normalize_disabled("false")
            False
            >>> projector._normalize_disabled("TRUE")
            True
            >>> projector._normalize_disabled(None)
            None
        """
        if value is None:
            return None

        # Convert to string and normalize
        str_value = str(value).lower().strip()

        # Handle boolean strings
        if str_value in ("true", "1", "yes"):
            return True
        if str_value in ("false", "0", "no"):
            return False

        # If we can't parse it, return None
        return None

    def _build_kv(self, keys: dict[str, Any]) -> dict[str, Any]:
        """Build kv dict with non-extracted fields.

        Args:
            keys: All key-value pairs from stanza

        Returns:
            Dictionary with fields not extracted to typed columns
        """
        kv = {}
        for key, value in keys.items():
            if key not in self.EXTRACTED_FIELDS:
                kv[key] = value
        return kv

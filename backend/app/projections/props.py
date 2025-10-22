"""Props projector for normalizing props.conf stanzas.

This module implements typed projection for Splunk props.conf stanzas,
extracting TRANSFORMS-* and SEDCMD-* keys into arrays and preserving
additional properties in JSONB.
"""

import re
from typing import Any

from app.parser.types import ParsedStanza


class PropsProjector:
    """Projects parsed props.conf stanzas to typed Props records.

    Handles various Splunk props configurations:
    - TRANSFORMS-* keys - Transform chains in order
    - SEDCMD-* keys - Sed command operations
    - Field extractions (EXTRACT-*, REPORT-*)
    - Line breaking rules
    - Timestamp extraction
    - And others

    Example:
        projector = PropsProjector()
        props_data = projector.project(parsed_stanza, run_id=1)
        # Returns dict ready for Props model instantiation
    """

    # Regex patterns to identify special key types
    TRANSFORMS_PATTERN = re.compile(r"^TRANSFORMS-(.+)$", re.IGNORECASE)
    SEDCMD_PATTERN = re.compile(r"^SEDCMD-(.+)$", re.IGNORECASE)

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any]:
        """Project a parsed stanza to a Props record dictionary.

        Args:
            stanza: Parsed stanza from props.conf
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for Props model:
            - run_id: Ingestion run ID
            - target: Sourcetype or source pattern (stanza name)
            - transforms_list: List of transform names from TRANSFORMS-* keys (in order)
            - sedcmds: List of sed command patterns from SEDCMD-* keys
            - kv: Additional key-value pairs
        """
        # Target is the stanza name (sourcetype or source pattern)
        target = stanza.name

        # Extract TRANSFORMS-* and SEDCMD-* keys in order
        transforms_list = self._extract_transforms(stanza)
        sedcmds = self._extract_sedcmds(stanza)

        # Build kv dict with remaining properties
        kv = self._build_kv(stanza.keys)

        # Build the projection
        projection: dict[str, Any] = {
            "run_id": run_id,
            "target": target,
            "transforms_list": transforms_list if transforms_list else None,
            "sedcmds": sedcmds if sedcmds else None,
            "kv": kv if kv else None,
        }

        return projection

    def _extract_transforms(self, stanza: ParsedStanza) -> list[str]:
        """Extract TRANSFORMS-* keys in order from stanza.

        Splunk TRANSFORMS-* keys can have values that are:
        - Single transform name: "transform1"
        - Comma-separated list: "transform1, transform2"
        - Multi-line with continuation: "transform1, \\\ntransform2"

        We preserve the order of keys as they appear in the file,
        and split comma-separated values into individual transforms.

        Args:
            stanza: Parsed stanza

        Returns:
            List of transform names in order

        Examples:
            >>> stanza = ParsedStanza(name="app:log", keys={
            ...     "TRANSFORMS-routing": "route_to_index",
            ...     "TRANSFORMS-mask": "mask_sensitive_data"
            ... }, key_order=["TRANSFORMS-routing", "TRANSFORMS-mask"])
            >>> projector = PropsProjector()
            >>> projector._extract_transforms(stanza)
            ['route_to_index', 'mask_sensitive_data']
        """
        transforms = []

        # Process keys in order they appeared in file
        for key in stanza.key_order:
            match = self.TRANSFORMS_PATTERN.match(key)
            if match:
                value = stanza.keys.get(key)
                if value:
                    # Split by comma and strip whitespace
                    # Handle both single and comma-separated transform names
                    transform_names = [
                        name.strip() for name in str(value).split(",") if name.strip()
                    ]
                    transforms.extend(transform_names)

        return transforms

    def _extract_sedcmds(self, stanza: ParsedStanza) -> list[str]:
        """Extract SEDCMD-* keys in order from stanza.

        SEDCMD-* keys contain sed-like regex substitution patterns.
        We collect them in order as they appear in the configuration.

        Args:
            stanza: Parsed stanza

        Returns:
            List of sed command patterns in order

        Examples:
            >>> stanza = ParsedStanza(name="custom:data", keys={
            ...     "SEDCMD-remove": "s/password=\\S+/password=***MASKED***/g",
            ...     "SEDCMD-normalize": "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g"
            ... }, key_order=["SEDCMD-remove", "SEDCMD-normalize"])
            >>> projector = PropsProjector()
            >>> projector._extract_sedcmds(stanza)
            ['s/password=\\\\S+/password=***MASKED***/g', 's/(\\\\d{2})\\\\/(\\\\d{2})\\\\/(\\\\d{4})/\\\\3-\\\\1-\\\\2/g']
        """
        sedcmds = []

        # Process keys in order they appeared in file
        for key in stanza.key_order:
            match = self.SEDCMD_PATTERN.match(key)
            if match:
                value = stanza.keys.get(key)
                if value:
                    # Store the sed command pattern as-is
                    sedcmds.append(str(value))

        return sedcmds

    def _build_kv(self, keys: dict[str, Any]) -> dict[str, Any]:
        """Build kv dict with non-extracted fields.

        Filters out TRANSFORMS-* and SEDCMD-* keys since those are
        extracted into dedicated arrays.

        Args:
            keys: All key-value pairs from stanza

        Returns:
            Dictionary with fields not extracted to typed columns
        """
        kv = {}
        for key, value in keys.items():
            # Skip TRANSFORMS-* and SEDCMD-* keys (already extracted)
            if not (
                self.TRANSFORMS_PATTERN.match(key) or self.SEDCMD_PATTERN.match(key)
            ):
                kv[key] = value
        return kv

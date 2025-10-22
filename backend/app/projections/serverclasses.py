"""Serverclass projector for normalizing serverclass.conf stanzas.

This module implements typed projection for Splunk serverclass.conf stanzas,
extracting whitelist, blacklist, and app assignments into typed columns
and preserving additional properties in JSONB.
"""

import re
from typing import Any

from app.parser.types import ParsedStanza


class ServerclassProjector:
    """Projects parsed serverclass.conf stanzas to typed Serverclass records.

    Handles Splunk deployment server configurations:
    - Serverclass definitions with whitelist/blacklist patterns
    - App assignments to serverclasses
    - Global settings

    Example:
        projector = ServerclassProjector()
        serverclass_data = projector.project(parsed_stanza, run_id=1)
        # Returns dict ready for Serverclass model instantiation
    """

    # Regex pattern to extract serverclass name and app from stanza name
    SERVERCLASS_PATTERN = re.compile(r"^serverClass:([^:]+)$")
    SERVERCLASS_APP_PATTERN = re.compile(r"^serverClass:([^:]+):app:([^:]+)$")

    # Patterns for whitelist/blacklist numbered keys
    WHITELIST_PATTERN = re.compile(r"^whitelist\.(\d+)$")
    BLACKLIST_PATTERN = re.compile(r"^blacklist\.(\d+)$")

    # Fields that go into typed columns or are handled specially
    SPECIAL_FIELDS = set()

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any]:
        """Project a parsed stanza to a Serverclass record dictionary.

        Args:
            stanza: Parsed stanza from serverclass.conf
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for Serverclass model:
            - run_id: Ingestion run ID
            - name: Serverclass name
            - whitelist: Whitelist patterns (JSONB)
            - blacklist: Blacklist patterns (JSONB)
            - app_assignments: App assignments (JSONB)
            - kv: Additional key-value pairs
            - app: App name from provenance
            - scope: Scope (default/local) from provenance
            - layer: Layer (system/app) from provenance
        """
        # Extract serverclass name and type
        serverclass_name = self._extract_serverclass_name(stanza.name)

        # Skip global and non-serverclass stanzas
        if serverclass_name is None:
            return None

        # Check if this is an app assignment stanza
        app_match = self.SERVERCLASS_APP_PATTERN.match(stanza.name)
        if app_match:
            # This is an app assignment - return minimal record
            # App assignments are aggregated into the parent serverclass
            return None

        # Extract whitelist and blacklist
        whitelist = self._extract_numbered_patterns(stanza.keys, "whitelist")
        blacklist = self._extract_numbered_patterns(stanza.keys, "blacklist")

        # Build kv dict with remaining properties
        kv = self._build_kv(stanza.keys)

        # Build the projection
        projection: dict[str, Any] = {
            "run_id": run_id,
            "name": serverclass_name,
            "whitelist": whitelist if whitelist else None,
            "blacklist": blacklist if blacklist else None,
            "app_assignments": None,  # TODO: aggregate from child stanzas
            "kv": kv if kv else None,
            "app": stanza.provenance.app if stanza.provenance else None,
            "scope": stanza.provenance.scope if stanza.provenance else None,
            "layer": stanza.provenance.layer if stanza.provenance else None,
        }

        return projection

    def _extract_serverclass_name(self, stanza_name: str) -> str | None:
        """Extract serverclass name from stanza name.

        Args:
            stanza_name: Stanza header (e.g., "serverClass:production")

        Returns:
            Serverclass name (e.g., "production") or None if not a serverclass stanza

        Examples:
            >>> projector = ServerclassProjector()
            >>> projector._extract_serverclass_name("serverClass:production")
            'production'
            >>> projector._extract_serverclass_name("serverClass:indexers")
            'indexers'
            >>> projector._extract_serverclass_name("serverClass:production:app:Splunk_TA_nix")
            'production'
            >>> projector._extract_serverclass_name("global")
            None
        """
        # Try app assignment pattern first
        app_match = self.SERVERCLASS_APP_PATTERN.match(stanza_name)
        if app_match:
            return app_match.group(1)

        # Try serverclass pattern
        sc_match = self.SERVERCLASS_PATTERN.match(stanza_name)
        if sc_match:
            return sc_match.group(1)

        return None

    def _extract_numbered_patterns(
        self, keys: dict[str, Any], prefix: str
    ) -> dict[str, str]:
        """Extract numbered patterns (whitelist.0, blacklist.0, etc.) from keys.

        Splunk uses numbered keys for lists: whitelist.0, whitelist.1, etc.
        These are extracted into a dictionary keyed by the number.

        Args:
            keys: All key-value pairs from stanza
            prefix: Pattern prefix ("whitelist" or "blacklist")

        Returns:
            Dictionary mapping number to pattern value

        Examples:
            >>> projector = ServerclassProjector()
            >>> keys = {"whitelist.0": "prod-*.example.com", "whitelist.1": "uf-*.example.com"}
            >>> projector._extract_numbered_patterns(keys, "whitelist")
            {'0': 'prod-*.example.com', '1': 'uf-*.example.com'}
        """
        pattern = re.compile(rf"^{prefix}\.(\d+)$")
        result = {}

        for key, value in keys.items():
            match = pattern.match(key)
            if match:
                number = match.group(1)
                result[number] = value

        return result

    def _build_kv(self, keys: dict[str, Any]) -> dict[str, Any]:
        """Build kv dict with non-extracted fields.

        Excludes whitelist.*, blacklist.* patterns as these are in typed columns.

        Args:
            keys: All key-value pairs from stanza

        Returns:
            Dictionary with fields not extracted to typed columns
        """
        kv = {}
        for key, value in keys.items():
            # Skip whitelist and blacklist patterns
            if self.WHITELIST_PATTERN.match(key) or self.BLACKLIST_PATTERN.match(key):
                continue
            kv[key] = value
        return kv

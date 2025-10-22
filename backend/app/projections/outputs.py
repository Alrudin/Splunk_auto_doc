"""Output projector for normalizing outputs.conf stanzas.

This module implements typed projection for Splunk outputs.conf stanzas,
extracting common fields into typed columns and preserving additional
properties in JSONB.
"""

from typing import Any

from app.parser.types import ParsedStanza


class OutputProjector:
    """Projects parsed outputs.conf stanzas to typed Output records.

    Handles various Splunk output types:
    - tcpout:// - TCP forwarding to indexers
    - syslog:// - Syslog forwarding
    - httpout:// - HTTP Event Collector (HEC) forwarding
    - And others

    Example:
        projector = OutputProjector()
        output_data = projector.project(parsed_stanza, run_id=1)
        # Returns dict ready for Output model instantiation
    """

    # Common extracted fields that will go into servers JSONB
    SERVER_FIELDS = {"server", "uri"}

    # Fields that will go into servers or kv depending on context
    # target_group is similar to server but references other groups
    TARGET_FIELDS = {"target_group"}

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any]:
        """Project a parsed stanza to an Output record dictionary.

        Args:
            stanza: Parsed stanza from outputs.conf
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for Output model:
            - run_id: Ingestion run ID
            - group_name: Output group name (stanza header)
            - servers: Server list and configurations (JSONB)
            - kv: Additional key-value pairs (JSONB)

        Notes:
            - The stanza name is the output group name (e.g., "tcpout:primary_indexers")
            - Server information (server, uri, target_group) goes into servers JSONB
            - All other properties go into kv JSONB
            - Empty servers/kv becomes None for consistency
        """
        # Extract group name from stanza header
        group_name = stanza.name

        # Build servers dict with server-related fields
        servers = self._build_servers(stanza.keys)

        # Build kv dict with remaining properties
        kv = self._build_kv(stanza.keys)

        # Build the projection
        projection: dict[str, Any] = {
            "run_id": run_id,
            "group_name": group_name,
            "servers": servers if servers else None,
            "kv": kv if kv else None,
        }

        return projection

    def _build_servers(self, keys: dict[str, Any]) -> dict[str, Any]:
        """Build servers dict with server-related fields.

        Extracts server configuration fields into a structured JSONB object.

        Args:
            keys: All key-value pairs from stanza

        Returns:
            Dictionary with server-related configuration

        Examples:
            >>> projector = OutputProjector()
            >>> keys = {
            ...     "server": "indexer1.example.com:9997, indexer2.example.com:9997",
            ...     "autoLBFrequency": "30"
            ... }
            >>> servers = projector._build_servers(keys)
            >>> servers["server"]
            'indexer1.example.com:9997, indexer2.example.com:9997'
        """
        servers = {}
        for key, value in keys.items():
            if key in self.SERVER_FIELDS or key in self.TARGET_FIELDS:
                servers[key] = value
        return servers

    def _build_kv(self, keys: dict[str, Any]) -> dict[str, Any]:
        """Build kv dict with non-server fields.

        Args:
            keys: All key-value pairs from stanza

        Returns:
            Dictionary with fields not extracted to servers

        Examples:
            >>> projector = OutputProjector()
            >>> keys = {
            ...     "server": "indexer1.example.com:9997",
            ...     "compressed": "true",
            ...     "maxQueueSize": "10MB"
            ... }
            >>> kv = projector._build_kv(keys)
            >>> "server" in kv
            False
            >>> kv["compressed"]
            'true'
        """
        kv = {}
        for key, value in keys.items():
            if key not in self.SERVER_FIELDS and key not in self.TARGET_FIELDS:
                kv[key] = value
        return kv

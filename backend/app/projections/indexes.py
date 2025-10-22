"""Index projector for normalizing indexes.conf stanzas.

This module implements typed projection for Splunk indexes.conf stanzas,
extracting the index name and preserving all configuration properties in JSONB.
"""

from typing import Any

from app.parser.types import ParsedStanza


class IndexProjector:
    """Projects parsed indexes.conf stanzas to typed Index records.

    Handles all index types in Splunk:
    - Event indexes (default datatype)
    - Metrics indexes (datatype = metric)
    - Custom indexes with various settings

    Example:
        projector = IndexProjector()
        index_data = projector.project(parsed_stanza, run_id=1)
        # Returns dict ready for Index model instantiation
    """

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any]:
        """Project a parsed stanza to an Index record dictionary.

        Args:
            stanza: Parsed stanza from indexes.conf
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for Index model:
            - run_id: Ingestion run ID
            - name: Index name (stanza header)
            - kv: All key-value pairs from the stanza

        Notes:
            - The stanza name is the index name (e.g., "main", "app_index")
            - All properties are stored in kv JSONB for flexibility
            - Special stanza [default] sets defaults for all indexes
            - Empty kv becomes None for consistency
        """
        # Extract index name from stanza header
        name = stanza.name

        # Build kv dict with all properties
        kv = self._build_kv(stanza.keys)

        # Build the projection
        projection: dict[str, Any] = {
            "run_id": run_id,
            "name": name,
            "kv": kv if kv else None,
        }

        return projection

    def _build_kv(self, keys: dict[str, Any]) -> dict[str, Any]:
        """Build kv dict with all configuration fields.

        For indexes.conf, all properties are stored in JSONB as there are
        many possible settings and they vary by index type.

        Args:
            keys: All key-value pairs from stanza

        Returns:
            Dictionary with all configuration properties

        Examples:
            >>> projector = IndexProjector()
            >>> keys = {
            ...     "homePath": "$SPLUNK_DB/main/db",
            ...     "coldPath": "$SPLUNK_DB/main/colddb",
            ...     "maxTotalDataSizeMB": "500000"
            ... }
            >>> kv = projector._build_kv(keys)
            >>> kv["homePath"]
            '$SPLUNK_DB/main/db'
        """
        # For indexes, we store all properties in kv
        # No fields are extracted to typed columns
        return dict(keys)

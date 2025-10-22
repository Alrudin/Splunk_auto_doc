"""Transform projector for normalizing transforms.conf stanzas.

This module implements typed projection for Splunk transforms.conf stanzas,
extracting common fields into typed columns and preserving additional
properties in JSONB.
"""

from typing import Any

from app.parser.types import ParsedStanza


class TransformProjector:
    """Projects parsed transforms.conf stanzas to typed Transform records.

    Handles various Splunk transform types:
    - Field extractions (REGEX + FORMAT)
    - Index routing (_MetaData:Index)
    - Sourcetype routing (_MetaData:Sourcetype)
    - Data masking/rewriting
    - And others

    Example:
        projector = TransformProjector()
        transform_data = projector.project(parsed_stanza, run_id=1)
        # Returns dict ready for Transform model instantiation
    """

    # Common extracted fields - these go into typed columns
    EXTRACTED_FIELDS = {"DEST_KEY", "REGEX", "FORMAT"}

    def project(self, stanza: ParsedStanza, run_id: int) -> dict[str, Any]:
        """Project a parsed stanza to a Transform record dictionary.

        Args:
            stanza: Parsed stanza from transforms.conf
            run_id: ID of the ingestion run

        Returns:
            Dictionary with fields for Transform model:
            - run_id: Ingestion run ID
            - name: Transform name (stanza header)
            - dest_key: DEST_KEY value (if specified)
            - regex: REGEX pattern (if specified)
            - format: FORMAT template (if specified)
            - writes_meta_index: Whether transform writes to _MetaData:Index
            - writes_meta_sourcetype: Whether transform writes to _MetaData:Sourcetype
            - kv: Additional key-value pairs
        """
        # Extract common fields
        dest_key = self._extract_dest_key(stanza.keys.get("DEST_KEY"))
        regex = stanza.keys.get("REGEX")
        format_value = stanza.keys.get("FORMAT")

        # Detect metadata writes
        writes_meta_index = self._detect_writes_meta_index(dest_key)
        writes_meta_sourcetype = self._detect_writes_meta_sourcetype(dest_key)

        # Build kv dict with remaining properties
        kv = self._build_kv(stanza.keys)

        # Build the projection
        projection: dict[str, Any] = {
            "run_id": run_id,
            "name": stanza.name,
            "dest_key": dest_key,
            "regex": regex,
            "format": format_value,
            "writes_meta_index": writes_meta_index,
            "writes_meta_sourcetype": writes_meta_sourcetype,
            "kv": kv if kv else None,
        }

        return projection

    def _extract_dest_key(self, value: Any) -> str | None:
        """Extract and normalize DEST_KEY value.

        DEST_KEY in Splunk can have various formats:
        - _MetaData:Index (with various capitalizations)
        - MetaData:Sourcetype (without underscore prefix)
        - _raw
        - queue
        - And others

        Args:
            value: Raw DEST_KEY value from config

        Returns:
            Normalized DEST_KEY string or None if not specified

        Examples:
            >>> projector = TransformProjector()
            >>> projector._extract_dest_key("_MetaData:Index")
            '_MetaData:Index'
            >>> projector._extract_dest_key("_raw")
            '_raw'
            >>> projector._extract_dest_key(None)
            None
        """
        if value is None:
            return None

        # Convert to string and strip whitespace
        return str(value).strip()

    def _detect_writes_meta_index(self, dest_key: str | None) -> bool | None:
        """Detect if transform writes to _MetaData:Index.

        This is a critical routing operation that changes which index events go to.

        Args:
            dest_key: Normalized DEST_KEY value

        Returns:
            True if writes to index metadata, False if explicitly doesn't, None if N/A

        Examples:
            >>> projector = TransformProjector()
            >>> projector._detect_writes_meta_index("_MetaData:Index")
            True
            >>> projector._detect_writes_meta_index("_metadata:index")
            True
            >>> projector._detect_writes_meta_index("_raw")
            False
            >>> projector._detect_writes_meta_index(None)
            None
        """
        if dest_key is None:
            return None

        # Case-insensitive comparison for metadata index
        dest_key_lower = dest_key.lower()
        if dest_key_lower == "_metadata:index":
            return True

        # If DEST_KEY is specified but not metadata:index, explicitly False
        return False

    def _detect_writes_meta_sourcetype(self, dest_key: str | None) -> bool | None:
        """Detect if transform writes to _MetaData:Sourcetype or MetaData:Sourcetype.

        This is a critical routing operation that changes the sourcetype of events.

        Args:
            dest_key: Normalized DEST_KEY value

        Returns:
            True if writes to sourcetype metadata, False if explicitly doesn't, None if N/A

        Examples:
            >>> projector = TransformProjector()
            >>> projector._detect_writes_meta_sourcetype("MetaData:Sourcetype")
            True
            >>> projector._detect_writes_meta_sourcetype("_MetaData:Sourcetype")
            True
            >>> projector._detect_writes_meta_sourcetype("metadata:sourcetype")
            True
            >>> projector._detect_writes_meta_sourcetype("_raw")
            False
            >>> projector._detect_writes_meta_sourcetype(None)
            None
        """
        if dest_key is None:
            return None

        # Case-insensitive comparison for metadata sourcetype
        # Both MetaData:Sourcetype and _MetaData:Sourcetype are valid
        dest_key_lower = dest_key.lower()
        if dest_key_lower in ("_metadata:sourcetype", "metadata:sourcetype"):
            return True

        # If DEST_KEY is specified but not metadata:sourcetype, explicitly False
        return False

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

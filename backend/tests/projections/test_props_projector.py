"""Unit tests for PropsProjector - props.conf typed projection."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.types import ParsedStanza
from app.projections.props import PropsProjector


class TestTransformsExtraction:
    """Test TRANSFORMS-* key extraction."""

    def test_single_transform(self):
        """Test extraction of single TRANSFORMS key."""
        stanza = ParsedStanza(
            name="app:log",
            keys={"TRANSFORMS-routing": "route_to_index"},
            key_order=["TRANSFORMS-routing"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == ["route_to_index"]

    def test_multiple_transforms_keys(self):
        """Test extraction of multiple TRANSFORMS-* keys."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "TRANSFORMS-routing": "route_to_index",
                "TRANSFORMS-mask": "mask_sensitive_data",
            },
            key_order=["TRANSFORMS-routing", "TRANSFORMS-mask"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == ["route_to_index", "mask_sensitive_data"]

    def test_comma_separated_transforms(self):
        """Test extraction of comma-separated transform list."""
        stanza = ParsedStanza(
            name="json:api",
            keys={"TRANSFORMS-routing": "route_by_severity, route_by_client"},
            key_order=["TRANSFORMS-routing"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == ["route_by_severity", "route_by_client"]

    def test_multi_line_transforms(self):
        """Test extraction of multi-line transform list."""
        stanza = ParsedStanza(
            name="json:api",
            keys={
                "TRANSFORMS-cleanup": "cleanup_fields, normalize_timestamps, add_metadata"
            },
            key_order=["TRANSFORMS-cleanup"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == [
            "cleanup_fields",
            "normalize_timestamps",
            "add_metadata",
        ]

    def test_transforms_order_preserved(self):
        """Test that transform order is preserved."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "TRANSFORMS-first": "transform_a",
                "TRANSFORMS-second": "transform_b",
                "TRANSFORMS-third": "transform_c",
            },
            key_order=["TRANSFORMS-first", "TRANSFORMS-second", "TRANSFORMS-third"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == ["transform_a", "transform_b", "transform_c"]

    def test_transforms_last_wins(self):
        """Test that repeated TRANSFORMS keys use last-wins."""
        stanza = ParsedStanza(
            name="multi:transform",
            keys={
                "TRANSFORMS-first": "transform_a_override",
                "TRANSFORMS-second": "transform_b",
            },
            key_order=[
                "TRANSFORMS-first",
                "TRANSFORMS-second",
                "TRANSFORMS-first",
            ],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        # First appears twice in key_order, last value wins in keys
        # Order reflects appearance in key_order
        assert "transform_a_override" in transforms
        assert "transform_b" in transforms

    def test_no_transforms(self):
        """Test stanza with no TRANSFORMS keys."""
        stanza = ParsedStanza(
            name="default",
            keys={"SHOULD_LINEMERGE": "true"},
            key_order=["SHOULD_LINEMERGE"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == []

    def test_transforms_case_insensitive(self):
        """Test that TRANSFORMS key matching is case-insensitive."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "TRANSFORMS-routing": "route1",
                "transforms-mask": "mask1",
                "Transforms-extract": "extract1",
            },
            key_order=["TRANSFORMS-routing", "transforms-mask", "Transforms-extract"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == ["route1", "mask1", "extract1"]

    def test_transforms_with_whitespace(self):
        """Test transform extraction handles whitespace."""
        stanza = ParsedStanza(
            name="app:log",
            keys={"TRANSFORMS-routing": "  transform1  ,  transform2  "},
            key_order=["TRANSFORMS-routing"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == ["transform1", "transform2"]

    def test_empty_transforms_value(self):
        """Test that empty transform values are skipped."""
        stanza = ParsedStanza(
            name="app:log",
            keys={"TRANSFORMS-routing": ""},
            key_order=["TRANSFORMS-routing"],
        )
        projector = PropsProjector()
        transforms = projector._extract_transforms(stanza)
        assert transforms == []


class TestSedcmdExtraction:
    """Test SEDCMD-* key extraction."""

    def test_single_sedcmd(self):
        """Test extraction of single SEDCMD key."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={"SEDCMD-remove": "s/password=\\S+/password=***MASKED***/g"},
            key_order=["SEDCMD-remove"],
        )
        projector = PropsProjector()
        sedcmds = projector._extract_sedcmds(stanza)
        assert sedcmds == ["s/password=\\S+/password=***MASKED***/g"]

    def test_multiple_sedcmds(self):
        """Test extraction of multiple SEDCMD keys."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={
                "SEDCMD-remove_sensitive": "s/password=\\S+/password=***MASKED***/g",
                "SEDCMD-normalize_dates": "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g",
            },
            key_order=["SEDCMD-remove_sensitive", "SEDCMD-normalize_dates"],
        )
        projector = PropsProjector()
        sedcmds = projector._extract_sedcmds(stanza)
        assert sedcmds == [
            "s/password=\\S+/password=***MASKED***/g",
            "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g",
        ]

    def test_sedcmd_order_preserved(self):
        """Test that SEDCMD order is preserved."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={
                "SEDCMD-first": "s/a/b/g",
                "SEDCMD-second": "s/c/d/g",
                "SEDCMD-third": "s/e/f/g",
            },
            key_order=["SEDCMD-first", "SEDCMD-second", "SEDCMD-third"],
        )
        projector = PropsProjector()
        sedcmds = projector._extract_sedcmds(stanza)
        assert sedcmds == ["s/a/b/g", "s/c/d/g", "s/e/f/g"]

    def test_no_sedcmds(self):
        """Test stanza with no SEDCMD keys."""
        stanza = ParsedStanza(
            name="app:log",
            keys={"TRANSFORMS-routing": "route_to_index"},
            key_order=["TRANSFORMS-routing"],
        )
        projector = PropsProjector()
        sedcmds = projector._extract_sedcmds(stanza)
        assert sedcmds == []

    def test_sedcmd_case_insensitive(self):
        """Test that SEDCMD key matching is case-insensitive."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={
                "SEDCMD-first": "s/a/b/g",
                "sedcmd-second": "s/c/d/g",
                "Sedcmd-third": "s/e/f/g",
            },
            key_order=["SEDCMD-first", "sedcmd-second", "Sedcmd-third"],
        )
        projector = PropsProjector()
        sedcmds = projector._extract_sedcmds(stanza)
        assert sedcmds == ["s/a/b/g", "s/c/d/g", "s/e/f/g"]

    def test_empty_sedcmd_value(self):
        """Test that empty SEDCMD values are skipped."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={"SEDCMD-empty": ""},
            key_order=["SEDCMD-empty"],
        )
        projector = PropsProjector()
        sedcmds = projector._extract_sedcmds(stanza)
        assert sedcmds == []


class TestKvBuilding:
    """Test kv dict building."""

    def test_kv_excludes_transforms(self):
        """Test that TRANSFORMS-* keys are excluded from kv."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "TRANSFORMS-routing": "route_to_index",
                "SHOULD_LINEMERGE": "false",
                "TIME_FORMAT": "%Y-%m-%d %H:%M:%S",
            },
            key_order=["TRANSFORMS-routing", "SHOULD_LINEMERGE", "TIME_FORMAT"],
        )
        projector = PropsProjector()
        kv = projector._build_kv(stanza.keys)
        assert "TRANSFORMS-routing" not in kv
        assert kv["SHOULD_LINEMERGE"] == "false"
        assert kv["TIME_FORMAT"] == "%Y-%m-%d %H:%M:%S"

    def test_kv_excludes_sedcmds(self):
        """Test that SEDCMD-* keys are excluded from kv."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={
                "SEDCMD-remove": "s/password=\\S+/password=***MASKED***/g",
                "LINE_BREAKER": "([\\r\\n]+)\\d{4}-\\d{2}-\\d{2}",
            },
            key_order=["SEDCMD-remove", "LINE_BREAKER"],
        )
        projector = PropsProjector()
        kv = projector._build_kv(stanza.keys)
        assert "SEDCMD-remove" not in kv
        assert kv["LINE_BREAKER"] == "([\\r\\n]+)\\d{4}-\\d{2}-\\d{2}"

    def test_kv_includes_other_keys(self):
        """Test that other keys are included in kv."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "EXTRACT-fields": "^(?P<timestamp>\\S+)\\s+(?P<level>\\w+)",
                "INDEXED_EXTRACTIONS": "json",
                "KV_MODE": "json",
                "MAX_TIMESTAMP_LOOKAHEAD": "20",
            },
            key_order=[
                "EXTRACT-fields",
                "INDEXED_EXTRACTIONS",
                "KV_MODE",
                "MAX_TIMESTAMP_LOOKAHEAD",
            ],
        )
        projector = PropsProjector()
        kv = projector._build_kv(stanza.keys)
        assert len(kv) == 4
        assert kv["EXTRACT-fields"] == "^(?P<timestamp>\\S+)\\s+(?P<level>\\w+)"
        assert kv["INDEXED_EXTRACTIONS"] == "json"
        assert kv["KV_MODE"] == "json"
        assert kv["MAX_TIMESTAMP_LOOKAHEAD"] == "20"

    def test_empty_kv(self):
        """Test that kv is empty when only TRANSFORMS/SEDCMD keys present."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "TRANSFORMS-routing": "route_to_index",
                "SEDCMD-mask": "s/ssn=\\d+/ssn=***MASKED***/g",
            },
            key_order=["TRANSFORMS-routing", "SEDCMD-mask"],
        )
        projector = PropsProjector()
        kv = projector._build_kv(stanza.keys)
        assert kv == {}


class TestProjection:
    """Test full projection logic."""

    def test_simple_sourcetype_projection(self):
        """Test projection of simple sourcetype with transforms."""
        stanza = ParsedStanza(
            name="app:log",
            keys={
                "TRANSFORMS-routing": "route_to_index",
                "TRANSFORMS-mask": "mask_sensitive_data",
                "EXTRACT-fields": "^(?P<timestamp>\\S+)\\s+(?P<level>\\w+)",
            },
            key_order=["TRANSFORMS-routing", "TRANSFORMS-mask", "EXTRACT-fields"],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["run_id"] == 42
        assert result["target"] == "app:log"
        assert result["transforms_list"] == ["route_to_index", "mask_sensitive_data"]
        assert result["sedcmds"] is None
        assert (
            result["kv"]["EXTRACT-fields"] == "^(?P<timestamp>\\S+)\\s+(?P<level>\\w+)"
        )

    def test_source_pattern_projection(self):
        """Test projection of source pattern."""
        stanza = ParsedStanza(
            name="source::/var/log/special/*.log",
            keys={
                "sourcetype": "special:log",
                "TRANSFORMS-parse": "extract_special_fields",
            },
            key_order=["sourcetype", "TRANSFORMS-parse"],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["target"] == "source::/var/log/special/*.log"
        assert result["transforms_list"] == ["extract_special_fields"]
        assert result["kv"]["sourcetype"] == "special:log"

    def test_projection_with_sedcmds(self):
        """Test projection with SEDCMD operations."""
        stanza = ParsedStanza(
            name="custom:data",
            keys={
                "SEDCMD-remove_sensitive": "s/password=\\S+/password=***MASKED***/g",
                "SEDCMD-normalize_dates": "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g",
                "TRANSFORMS-index": "route_custom_data",
            },
            key_order=[
                "SEDCMD-remove_sensitive",
                "SEDCMD-normalize_dates",
                "TRANSFORMS-index",
            ],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["target"] == "custom:data"
        assert result["transforms_list"] == ["route_custom_data"]
        assert result["sedcmds"] == [
            "s/password=\\S+/password=***MASKED***/g",
            "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g",
        ]

    def test_default_stanza_projection(self):
        """Test projection of [default] stanza."""
        stanza = ParsedStanza(
            name="default",
            keys={"SHOULD_LINEMERGE": "true"},
            key_order=["SHOULD_LINEMERGE"],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["target"] == "default"
        assert result["transforms_list"] is None
        assert result["sedcmds"] is None
        assert result["kv"]["SHOULD_LINEMERGE"] == "true"

    def test_complex_projection(self):
        """Test projection with multiple transform chains."""
        stanza = ParsedStanza(
            name="json:api",
            keys={
                "INDEXED_EXTRACTIONS": "json",
                "KV_MODE": "json",
                "TRANSFORMS-routing": "route_by_severity, route_by_client",
                "TRANSFORMS-cleanup": "cleanup_fields, normalize_timestamps, add_metadata",
            },
            key_order=[
                "INDEXED_EXTRACTIONS",
                "KV_MODE",
                "TRANSFORMS-routing",
                "TRANSFORMS-cleanup",
            ],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["target"] == "json:api"
        assert result["transforms_list"] == [
            "route_by_severity",
            "route_by_client",
            "cleanup_fields",
            "normalize_timestamps",
            "add_metadata",
        ]
        assert result["kv"]["INDEXED_EXTRACTIONS"] == "json"
        assert result["kv"]["KV_MODE"] == "json"

    def test_null_values_for_empty_fields(self):
        """Test that empty fields are set to None."""
        stanza = ParsedStanza(
            name="simple:log",
            keys={"TIME_FORMAT": "%Y-%m-%d %H:%M:%S"},
            key_order=["TIME_FORMAT"],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["transforms_list"] is None
        assert result["sedcmds"] is None
        assert result["kv"]["TIME_FORMAT"] == "%Y-%m-%d %H:%M:%S"

    def test_projection_with_repeated_keys(self):
        """Test projection handles repeated keys with last-wins."""
        stanza = ParsedStanza(
            name="multi:transform",
            keys={
                "TRANSFORMS-first": "transform_a_override",
                "TRANSFORMS-second": "transform_b",
            },
            key_order=[
                "TRANSFORMS-first",
                "TRANSFORMS-second",
                "TRANSFORMS-first",
            ],
        )
        projector = PropsProjector()
        result = projector.project(stanza, run_id=42)

        assert result["target"] == "multi:transform"
        # Should contain both transforms with last-wins applied
        assert "transform_a_override" in result["transforms_list"]
        assert "transform_b" in result["transforms_list"]


if __name__ == "__main__":
    # Run tests directly
    import pytest

    pytest.main([__file__, "-v"])

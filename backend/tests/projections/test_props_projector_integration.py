"""Integration tests for PropsProjector with golden fixtures.

Tests the complete flow: parse props.conf → project to Props records.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser
from app.projections.props import PropsProjector

# Path to golden fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "parser" / "fixtures"


class TestGoldenFixtures:
    """Test projection with golden fixture files."""

    def test_props_conf(self):
        """Test projection of props.conf fixture."""
        fixture_path = FIXTURES_DIR / "props.conf"

        # Parse the file
        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Project all stanzas
        projector = PropsProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Should have multiple stanzas
        assert len(projections) > 0

        # Verify default stanza
        default_projection = next(
            (p for p in projections if p["target"] == "default"), None
        )
        assert default_projection is not None
        assert default_projection["transforms_list"] is None
        assert default_projection["sedcmds"] is None
        assert "SHOULD_LINEMERGE" in default_projection["kv"]
        assert default_projection["kv"]["SHOULD_LINEMERGE"] == "true"

        # Verify app:log sourcetype with transforms
        app_log = next((p for p in projections if p["target"] == "app:log"), None)
        assert app_log is not None
        assert app_log["transforms_list"] == ["route_to_index", "mask_sensitive_data"]
        assert app_log["sedcmds"] is None
        assert "EXTRACT-fields" in app_log["kv"]
        assert "LINE_BREAKER" in app_log["kv"]
        assert "SHOULD_LINEMERGE" in app_log["kv"]
        assert app_log["kv"]["SHOULD_LINEMERGE"] == "false"

        # Verify source pattern
        source_pattern = next(
            (
                p
                for p in projections
                if p["target"] == "source::/var/log/special/*.log"
            ),
            None,
        )
        assert source_pattern is not None
        assert source_pattern["transforms_list"] == ["extract_special_fields"]
        assert "sourcetype" in source_pattern["kv"]
        assert source_pattern["kv"]["sourcetype"] == "special:log"

        # Verify custom:data with SEDCMD operations
        custom_data = next(
            (p for p in projections if p["target"] == "custom:data"), None
        )
        assert custom_data is not None
        assert custom_data["sedcmds"] is not None
        assert len(custom_data["sedcmds"]) == 2
        assert "s/password=\\S+/password=***MASKED***/g" in custom_data["sedcmds"]
        assert (
            "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g" in custom_data["sedcmds"]
        )
        assert custom_data["transforms_list"] == ["route_custom_data"]

        # Verify json:api with multiple transform chains
        json_api = next((p for p in projections if p["target"] == "json:api"), None)
        assert json_api is not None
        assert json_api["transforms_list"] is not None
        assert len(json_api["transforms_list"]) == 5
        assert "route_by_severity" in json_api["transforms_list"]
        assert "route_by_client" in json_api["transforms_list"]
        assert "cleanup_fields" in json_api["transforms_list"]
        assert "normalize_timestamps" in json_api["transforms_list"]
        assert "add_metadata" in json_api["transforms_list"]
        assert "INDEXED_EXTRACTIONS" in json_api["kv"]
        assert json_api["kv"]["INDEXED_EXTRACTIONS"] == "json"

        # Verify multi:transform with repeated keys
        multi_transform = next(
            (p for p in projections if p["target"] == "multi:transform"), None
        )
        assert multi_transform is not None
        # Last-wins should apply: transform_a_override wins over transform_a
        assert "transform_a_override" in multi_transform["transforms_list"]
        assert "transform_b" in multi_transform["transforms_list"]

    def test_transforms_order_preservation(self):
        """Test that transform order is preserved through parsing and projection."""
        fixture_path = FIXTURES_DIR / "props.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find json:api stanza
        json_api_stanza = next((s for s in stanzas if s.name == "json:api"), None)
        assert json_api_stanza is not None

        # Verify order in parsed stanza
        transforms_keys = [
            k for k in json_api_stanza.key_order if k.startswith("TRANSFORMS-")
        ]
        assert len(transforms_keys) > 0

        # Project and verify order preserved
        projector = PropsProjector()
        projection = projector.project(json_api_stanza, run_id=1)

        # Transforms should appear in the order they were defined
        # (accounting for comma-separated values)
        assert projection["transforms_list"] is not None
        transforms = projection["transforms_list"]
        # First TRANSFORMS-routing key has two values
        assert transforms.index("route_by_severity") < transforms.index(
            "route_by_client"
        )
        # Second TRANSFORMS-cleanup key has three values
        assert transforms.index("cleanup_fields") < transforms.index(
            "normalize_timestamps"
        )
        assert transforms.index("normalize_timestamps") < transforms.index(
            "add_metadata"
        )

    def test_sedcmd_order_preservation(self):
        """Test that SEDCMD order is preserved through parsing and projection."""
        fixture_path = FIXTURES_DIR / "props.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find custom:data stanza
        custom_data_stanza = next((s for s in stanzas if s.name == "custom:data"), None)
        assert custom_data_stanza is not None

        # Verify order in parsed stanza
        sedcmd_keys = [k for k in custom_data_stanza.key_order if k.startswith("SEDCMD-")]
        assert len(sedcmd_keys) == 2

        # Project and verify order preserved
        projector = PropsProjector()
        projection = projector.project(custom_data_stanza, run_id=1)

        # SEDCMDs should appear in the order they were defined
        assert projection["sedcmds"] is not None
        assert len(projection["sedcmds"]) == 2
        # First SEDCMD-remove_sensitive, then SEDCMD-normalize_dates
        assert (
            projection["sedcmds"][0] == "s/password=\\S+/password=***MASKED***/g"
        )
        assert (
            projection["sedcmds"][1]
            == "s/(\\d{2})\\/(\\d{2})\\/(\\d{4})/\\3-\\1-\\2/g"
        )

    def test_last_wins_semantics(self):
        """Test that last-wins semantics are preserved through projection."""
        fixture_path = FIXTURES_DIR / "props.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find the stanza with repeated TRANSFORMS keys
        multi_stanza = next((s for s in stanzas if s.name == "multi:transform"), None)
        assert multi_stanza is not None

        # Verify parser captured repeated keys in history
        # TRANSFORMS-first appears twice, second value should win
        assert "TRANSFORMS-first" in multi_stanza.keys
        # The last value for TRANSFORMS-first is transform_a_override
        assert multi_stanza.keys["TRANSFORMS-first"] == "transform_a_override"

        # Project and verify last-wins applied
        projector = PropsProjector()
        projection = projector.project(multi_stanza, run_id=1)

        # Should contain the override value, not the original
        assert "transform_a_override" in projection["transforms_list"]
        assert "transform_b" in projection["transforms_list"]


class TestEdgeCases:
    """Test edge cases in props projection."""

    def test_empty_props_conf(self):
        """Test projection of empty props.conf."""
        # Create empty file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("# Empty props.conf\n")
            temp_path = f.name

        try:
            parser = ConfParser()
            stanzas = parser.parse_file(temp_path)
            assert len(stanzas) == 0

            projector = PropsProjector()
            projections = [projector.project(stanza, run_id=1) for stanza in stanzas]
            assert len(projections) == 0
        finally:
            import os

            os.unlink(temp_path)

    def test_props_with_only_comments(self):
        """Test projection of props.conf with only comments."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("# Comment 1\n")
            f.write("# Comment 2\n")
            f.write("# Comment 3\n")
            temp_path = f.name

        try:
            parser = ConfParser()
            stanzas = parser.parse_file(temp_path)
            assert len(stanzas) == 0

            projector = PropsProjector()
            projections = [projector.project(stanza, run_id=1) for stanza in stanzas]
            assert len(projections) == 0
        finally:
            import os

            os.unlink(temp_path)


if __name__ == "__main__":
    # Run tests directly
    import pytest

    pytest.main([__file__, "-v"])

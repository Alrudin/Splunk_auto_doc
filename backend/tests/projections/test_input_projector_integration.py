"""Integration tests for InputProjector with golden fixtures.

Tests the complete flow: parse inputs.conf → project to Input records.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser
from app.projections.inputs import InputProjector

# Path to golden fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "parser" / "fixtures"


class TestGoldenFixtures:
    """Test projection with golden fixture files."""

    def test_hf_inputs_conf(self):
        """Test projection of Heavy Forwarder inputs.conf fixture."""
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"

        # Parse the file
        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Project all stanzas
        projector = InputProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Should have multiple stanzas
        assert len(projections) > 0

        # Find and verify specific stanzas
        projection_map = {p["stanza_type"]: p for p in projections if p["stanza_type"]}

        # Verify default stanza
        default_projection = next(
            (p for p in projections if p["stanza_type"] is None), None
        )
        assert default_projection is not None
        assert "host" in default_projection["kv"]

        # Verify monitor inputs
        monitor_projections = [
            p for p in projections if p["stanza_type"] == "monitor"
        ]
        assert len(monitor_projections) >= 3  # Multiple monitor inputs in fixture

        # Check specific monitor input
        app_log = next(
            (
                p
                for p in monitor_projections
                if p["sourcetype"] == "app:log"
            ),
            None,
        )
        assert app_log is not None
        assert app_log["index"] == "main"
        assert app_log["disabled"] is False
        assert "followTail" in app_log["kv"]

        # Verify TCP input
        tcp_projection = next(
            (p for p in projections if p["stanza_type"] == "tcp"), None
        )
        assert tcp_projection is not None
        assert tcp_projection["sourcetype"] == "splunk:tcp"
        assert tcp_projection["disabled"] is False

        # Verify UDP input
        udp_projection = next(
            (p for p in projections if p["stanza_type"] == "udp"), None
        )
        assert udp_projection is not None
        assert udp_projection["sourcetype"] == "syslog"
        assert "no_priority_stripping" in udp_projection["kv"]

        # Verify script input
        script_projection = next(
            (p for p in projections if p["stanza_type"] == "script"), None
        )
        assert script_projection is not None
        assert script_projection["sourcetype"] == "custom:script"
        assert script_projection["kv"]["interval"] == "300"

    def test_last_wins_semantics(self):
        """Test that last-wins semantics are preserved through projection."""
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find the stanza with repeated index key
        repeated_stanza = next(
            (s for s in stanzas if "debug.log" in s.name), None
        )
        assert repeated_stanza is not None

        # Verify parser captured both values in history
        assert len(repeated_stanza.key_history.get("index", [])) == 2
        assert repeated_stanza.key_history["index"][0] == "dev"
        assert repeated_stanza.key_history["index"][1] == "debug"

        # Verify projection uses last value
        projector = InputProjector()
        projection = projector.project(repeated_stanza, run_id=1)
        assert projection["index"] == "debug"

    def test_provenance_preservation(self):
        """Test that provenance metadata is preserved through projection."""
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = InputProjector()

        for idx, stanza in enumerate(stanzas):
            projection = projector.project(stanza, run_id=99)

            # All projections should have source_path
            assert projection["source_path"] is not None
            assert str(fixture_path) in projection["source_path"]

            # Provenance should be consistent
            if stanza.provenance:
                assert projection["app"] == stanza.provenance.app
                assert projection["scope"] == stanza.provenance.scope
                assert projection["layer"] == stanza.provenance.layer

    def test_all_stanza_types_projected(self):
        """Test that all stanzas are successfully projected."""
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = InputProjector()

        # Project all stanzas
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Every stanza should produce a valid projection
        assert len(projections) == len(stanzas)

        # All projections should have required fields
        for projection in projections:
            assert "run_id" in projection
            assert projection["run_id"] == 1
            assert "source_path" in projection
            assert "stanza_type" in projection
            # kv can be None or dict
            assert projection["kv"] is None or isinstance(projection["kv"], dict)

    def test_disabled_field_variations(self):
        """Test various disabled field representations in fixtures."""
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = InputProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Find projections with disabled field
        disabled_projections = [p for p in projections if p["disabled"] is not None]

        # Should have multiple disabled fields
        assert len(disabled_projections) > 0

        # All should be boolean
        for p in disabled_projections:
            assert isinstance(p["disabled"], bool)

    def test_special_characters_in_paths(self):
        """Test handling of special characters in stanza names."""
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find stanza with special characters
        special_stanza = next(
            (s for s in stanzas if "$TODAY" in s.name), None
        )
        assert special_stanza is not None

        # Project it
        projector = InputProjector()
        projection = projector.project(special_stanza, run_id=1)

        # Should project successfully
        assert projection["stanza_type"] == "monitor"
        assert projection["index"] == "main"


class TestEdgeCases:
    """Test edge cases in projection."""

    def test_empty_stanza(self):
        """Test projection of stanza with no keys."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/inputs.conf")
        stanza = ParsedStanza(name="monitor:///empty", keys={}, provenance=provenance)

        projector = InputProjector()
        projection = projector.project(stanza, run_id=1)

        assert projection["run_id"] == 1
        assert projection["stanza_type"] == "monitor"
        assert projection["index"] is None
        assert projection["sourcetype"] is None
        assert projection["disabled"] is None
        assert projection["kv"] is None

    def test_stanza_with_only_kv_fields(self):
        """Test stanza with only non-extracted fields."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/inputs.conf")
        stanza = ParsedStanza(
            name="tcp://9997",
            keys={"connection_host": "ip", "queueSize": "10MB"},
            provenance=provenance,
        )

        projector = InputProjector()
        projection = projector.project(stanza, run_id=1)

        assert projection["index"] is None
        assert projection["sourcetype"] is None
        assert projection["disabled"] is None
        assert projection["kv"]["connection_host"] == "ip"
        assert projection["kv"]["queueSize"] == "10MB"


if __name__ == "__main__":
    # Run tests with simple test runner
    import traceback

    test_classes = [TestGoldenFixtures, TestEdgeCases]

    total = 0
    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in methods:
            total += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  ✗ {method_name}")
                print(f"    {e}")
                failed += 1
            except Exception as e:
                print(f"  ✗ {method_name} (error)")
                traceback.print_exc()
                failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    if failed > 0:
        exit(1)

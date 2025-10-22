"""Integration tests for TransformProjector with golden fixtures.

Tests the complete flow: parse transforms.conf → project to Transform records.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser
from app.projections.transforms import TransformProjector

# Path to golden fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "parser" / "fixtures"


class TestGoldenFixtures:
    """Test projection with golden fixture files."""

    def test_transforms_conf(self):
        """Test projection of transforms.conf fixture."""
        fixture_path = FIXTURES_DIR / "transforms.conf"

        # Parse the file
        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Project all stanzas
        projector = TransformProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Should have multiple stanzas
        assert len(projections) > 0

        # Find and verify specific transforms
        projection_map = {p["name"]: p for p in projections}

        # Verify index routing transform (last-wins for repeated definition)
        assert "route_to_index" in projection_map
        route_transform = projection_map["route_to_index"]
        # Last definition should have this regex (overwrites first)
        assert route_transform["regex"] == "level=(ERROR|CRITICAL)"
        assert route_transform["dest_key"] == "_MetaData:Index"
        assert route_transform["format"] == "critical_index"
        assert route_transform["writes_meta_index"] is True
        assert route_transform["writes_meta_sourcetype"] is False

        # Verify data masking transform
        assert "mask_sensitive_data" in projection_map
        mask_transform = projection_map["mask_sensitive_data"]
        assert mask_transform["regex"] == r"(password|ssn|credit_card)=(\S+)"
        assert mask_transform["format"] == "$1=***MASKED***"
        assert mask_transform["dest_key"] == "_raw"
        assert mask_transform["writes_meta_index"] is False

        # Verify sourcetype override transform
        assert "override_sourcetype" in projection_map
        sourcetype_transform = projection_map["override_sourcetype"]
        assert sourcetype_transform["regex"] == "."
        assert sourcetype_transform["dest_key"] == "MetaData:Sourcetype"
        assert sourcetype_transform["format"] == "sourcetype::overridden:log"
        assert sourcetype_transform["writes_meta_sourcetype"] is True
        assert sourcetype_transform["writes_meta_index"] is False

        # Verify field extraction transform
        assert "extract_special_fields" in projection_map
        extract_transform = projection_map["extract_special_fields"]
        assert extract_transform["regex"] == r"^(?P<event_id>\d+)\s+(?P<severity>\w+)"
        assert extract_transform["format"] == "event_id::$1 severity::$2"
        assert extract_transform["dest_key"] is None
        assert extract_transform["writes_meta_index"] is None
        assert extract_transform["writes_meta_sourcetype"] is None

        # Verify routing by severity
        assert "route_by_severity" in projection_map
        severity_transform = projection_map["route_by_severity"]
        assert severity_transform["regex"] == "severity=(?P<sev>CRITICAL|HIGH)"
        assert severity_transform["dest_key"] == "_MetaData:Index"
        assert severity_transform["format"] == "critical_index"
        assert severity_transform["writes_meta_index"] is True

    def test_last_wins_semantics(self):
        """Test that last-wins semantics are preserved through projection."""
        fixture_path = FIXTURES_DIR / "transforms.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find the repeated route_to_index stanza
        # Parser should have captured the last definition
        route_stanzas = [s for s in stanzas if s.name == "route_to_index"]

        # Should have the stanza (parser handles last-wins)
        assert len(route_stanzas) >= 1

        # The stanza should have the last value
        last_stanza = route_stanzas[-1]

        # Verify projection uses last value
        projector = TransformProjector()
        projection = projector.project(last_stanza, run_id=1)

        # Last definition has this regex
        assert projection["regex"] == "level=(ERROR|CRITICAL)"
        assert projection["format"] == "critical_index"

    def test_provenance_preservation(self):
        """Test that provenance metadata is preserved through projection."""
        fixture_path = FIXTURES_DIR / "transforms.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = TransformProjector()

        for stanza in stanzas:
            projection = projector.project(stanza, run_id=99)

            # All projections should have name from stanza
            assert projection["name"] == stanza.name
            assert projection["run_id"] == 99

    def test_all_stanza_types_projected(self):
        """Test that all stanzas are successfully projected."""
        fixture_path = FIXTURES_DIR / "transforms.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = TransformProjector()

        # Project all stanzas
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Every stanza should produce a valid projection
        assert len(projections) == len(stanzas)

        # All projections should have required fields
        for projection in projections:
            assert "run_id" in projection
            assert projection["run_id"] == 1
            assert "name" in projection
            assert "dest_key" in projection
            assert "regex" in projection
            assert "format" in projection
            assert "writes_meta_index" in projection
            assert "writes_meta_sourcetype" in projection
            # kv can be None or dict
            assert projection["kv"] is None or isinstance(projection["kv"], dict)

    def test_metadata_variations(self):
        """Test various DEST_KEY metadata variations."""
        fixture_path = FIXTURES_DIR / "transforms.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = TransformProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Find transforms with metadata writes
        index_writes = [p for p in projections if p["writes_meta_index"] is True]
        sourcetype_writes = [
            p for p in projections if p["writes_meta_sourcetype"] is True
        ]

        # Should have multiple index routing transforms
        assert len(index_writes) >= 2

        # Should have at least one sourcetype override
        assert len(sourcetype_writes) >= 1

        # All should have proper DEST_KEY
        for p in index_writes:
            assert p["dest_key"] is not None
            assert "index" in p["dest_key"].lower()

        for p in sourcetype_writes:
            assert p["dest_key"] is not None
            assert "sourcetype" in p["dest_key"].lower()

    def test_multiline_regex(self):
        """Test handling of multi-line regex with continuations."""
        fixture_path = FIXTURES_DIR / "transforms.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find the complex extraction transform
        complex_stanza = next(
            (s for s in stanzas if s.name == "complex_extraction"), None
        )
        assert complex_stanza is not None

        # Project it
        projector = TransformProjector()
        projection = projector.project(complex_stanza, run_id=1)

        # Should have captured the regex (parser handles line continuations)
        assert projection["regex"] is not None
        assert "transaction_id" in projection["regex"]
        assert projection["format"] is not None


class TestEdgeCases:
    """Test edge cases in projection."""

    def test_empty_stanza(self):
        """Test projection of stanza with no keys."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/transforms.conf")
        stanza = ParsedStanza(
            name="empty_transform", keys={}, provenance=provenance
        )

        projector = TransformProjector()
        projection = projector.project(stanza, run_id=1)

        assert projection["run_id"] == 1
        assert projection["name"] == "empty_transform"
        assert projection["dest_key"] is None
        assert projection["regex"] is None
        assert projection["format"] is None
        assert projection["writes_meta_index"] is None
        assert projection["writes_meta_sourcetype"] is None
        assert projection["kv"] is None

    def test_stanza_with_only_kv_fields(self):
        """Test stanza with only non-extracted fields."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/transforms.conf")
        stanza = ParsedStanza(
            name="kv_only_transform",
            keys={
                "PRIORITY": "100",
                "MV_ADD": "true",
                "WRITE_META": "true",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        projection = projector.project(stanza, run_id=1)

        assert projection["dest_key"] is None
        assert projection["regex"] is None
        assert projection["format"] is None
        assert projection["kv"]["PRIORITY"] == "100"
        assert projection["kv"]["MV_ADD"] == "true"
        assert projection["kv"]["WRITE_META"] == "true"

    def test_regex_only_transform(self):
        """Test transform with only REGEX field."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/transforms.conf")
        stanza = ParsedStanza(
            name="regex_only",
            keys={"REGEX": "test_pattern"},
            provenance=provenance,
        )

        projector = TransformProjector()
        projection = projector.project(stanza, run_id=1)

        assert projection["regex"] == "test_pattern"
        assert projection["format"] is None
        assert projection["dest_key"] is None
        assert projection["kv"] is None


class TestSpecialCases:
    """Test special Splunk transform scenarios."""

    def test_queue_dest_key(self):
        """Test transform with queue DEST_KEY."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/transforms.conf")
        stanza = ParsedStanza(
            name="route_to_queue",
            keys={
                "REGEX": "severity=high",
                "DEST_KEY": "queue",
                "FORMAT": "indexQueue",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        projection = projector.project(stanza, run_id=1)

        assert projection["dest_key"] == "queue"
        assert projection["writes_meta_index"] is False
        assert projection["writes_meta_sourcetype"] is False

    def test_lookup_transform(self):
        """Test lookup-based transform."""
        from app.parser.types import ParsedStanza, Provenance

        provenance = Provenance(source_path="/test/transforms.conf")
        stanza = ParsedStanza(
            name="lookup_transform",
            keys={
                "filename": "lookup.csv",
                "max_matches": "1",
                "min_matches": "1",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        projection = projector.project(stanza, run_id=1)

        # Lookup fields should be in kv
        assert projection["kv"]["filename"] == "lookup.csv"
        assert projection["kv"]["max_matches"] == "1"
        assert projection["kv"]["min_matches"] == "1"


if __name__ == "__main__":
    # Run tests with simple test runner
    import traceback

    test_classes = [TestGoldenFixtures, TestEdgeCases, TestSpecialCases]

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
            except Exception:
                print(f"  ✗ {method_name} (error)")
                traceback.print_exc()
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 60}")

    if failed > 0:
        exit(1)

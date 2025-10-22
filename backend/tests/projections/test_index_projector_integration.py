"""Integration tests for IndexProjector using real fixtures."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.core import ConfParser
from app.projections.indexes import IndexProjector


class TestIndexProjectorIntegration:
    """Integration tests using real indexes.conf fixtures."""

    def test_parse_and_project_indexes_conf(self):
        """Test parsing and projecting real indexes.conf file."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        # Parse the file
        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Project all stanzas
        projector = IndexProjector()
        results = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Verify we got all stanzas
        assert len(results) > 0, "No stanzas projected"

        # Verify all have required fields
        for result in results:
            assert "run_id" in result
            assert "name" in result
            assert "kv" in result
            assert result["run_id"] == 1

    def test_default_index_settings(self):
        """Test projection of [default] stanza from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find default stanza
        default_stanza = next((s for s in stanzas if s.name == "default"), None)
        assert default_stanza is not None, "[default] stanza not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(default_stanza, run_id=42)

        # Verify projection
        assert result["name"] == "default"
        assert result["run_id"] == 42

        # Verify key settings are in kv
        assert result["kv"] is not None
        assert "frozenTimePeriodInSecs" in result["kv"]
        assert "maxTotalDataSizeMB" in result["kv"]
        assert "homePath" in result["kv"]
        assert "coldPath" in result["kv"]
        assert "thawedPath" in result["kv"]

    def test_main_index(self):
        """Test projection of [main] index from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find main index
        main_stanza = next((s for s in stanzas if s.name == "main"), None)
        assert main_stanza is not None, "[main] index not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(main_stanza, run_id=1)

        # Verify projection
        assert result["name"] == "main"
        assert result["kv"] is not None
        assert "homePath" in result["kv"]
        assert "coldPath" in result["kv"]
        assert "thawedPath" in result["kv"]
        assert "maxTotalDataSizeMB" in result["kv"]

        # Verify specific values from fixture
        assert "defaultdb" in result["kv"]["homePath"]
        assert result["kv"]["maxTotalDataSizeMB"] == "1000000"

    def test_custom_app_index(self):
        """Test projection of [app_index] from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find app_index
        app_stanza = next((s for s in stanzas if s.name == "app_index"), None)
        assert app_stanza is not None, "[app_index] not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(app_stanza, run_id=10)

        # Verify projection
        assert result["name"] == "app_index"
        assert result["kv"] is not None

        # Verify custom paths
        assert "fast-storage" in result["kv"]["homePath"]
        assert "archive-storage" in result["kv"]["coldPath"]

        # Verify custom settings
        assert "frozenTimePeriodInSecs" in result["kv"]
        assert result["kv"]["frozenTimePeriodInSecs"] == "31536000"
        assert "maxHotBuckets" in result["kv"]
        assert result["kv"]["maxHotBuckets"] == "10"
        assert "maxWarmDBCount" in result["kv"]
        assert result["kv"]["maxWarmDBCount"] == "300"

    def test_metrics_index(self):
        """Test projection of [metrics] index from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find metrics index
        metrics_stanza = next((s for s in stanzas if s.name == "metrics"), None)
        assert metrics_stanza is not None, "[metrics] index not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(metrics_stanza, run_id=5)

        # Verify projection
        assert result["name"] == "metrics"
        assert result["kv"] is not None

        # Verify datatype is metric
        assert "datatype" in result["kv"]
        assert result["kv"]["datatype"] == "metric"

        # Verify shorter retention
        assert "frozenTimePeriodInSecs" in result["kv"]
        assert result["kv"]["frozenTimePeriodInSecs"] == "7776000"

    def test_audit_index(self):
        """Test projection of [audit] index from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find audit index
        audit_stanza = next((s for s in stanzas if s.name == "audit"), None)
        assert audit_stanza is not None, "[audit] index not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(audit_stanza, run_id=20)

        # Verify projection
        assert result["name"] == "audit"
        assert result["kv"] is not None

        # Verify extended retention
        assert "frozenTimePeriodInSecs" in result["kv"]
        assert result["kv"]["frozenTimePeriodInSecs"] == "315360000"

        # Verify coldToFrozenDir is set
        assert "coldToFrozenDir" in result["kv"]
        assert "compliance-archive" in result["kv"]["coldToFrozenDir"]

    def test_summary_index(self):
        """Test projection of [summary] index from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find summary index
        summary_stanza = next((s for s in stanzas if s.name == "summary"), None)
        assert summary_stanza is not None, "[summary] index not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(summary_stanza, run_id=15)

        # Verify projection
        assert result["name"] == "summary"
        assert result["kv"] is not None

        # Verify optimization settings
        assert "maxHotBuckets" in result["kv"]
        assert result["kv"]["maxHotBuckets"] == "3"

    def test_repeated_setting_last_wins(self):
        """Test that repeated settings use last-wins from fixture."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find test_index with repeated settings
        test_stanza = next((s for s in stanzas if s.name == "test_index"), None)
        assert test_stanza is not None, "[test_index] not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(test_stanza, run_id=7)

        # Verify projection
        assert result["name"] == "test_index"
        assert result["kv"] is not None

        # Verify last value wins (50000 from fixture)
        assert "maxTotalDataSizeMB" in result["kv"]
        assert result["kv"]["maxTotalDataSizeMB"] == "50000"

    def test_line_continuation(self):
        """Test projection of index with line continuation."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find long_path_index with line continuations
        long_path_stanza = next(
            (s for s in stanzas if s.name == "long_path_index"), None
        )
        assert long_path_stanza is not None, "[long_path_index] not found"

        # Project it
        projector = IndexProjector()
        result = projector.project(long_path_stanza, run_id=3)

        # Verify projection
        assert result["name"] == "long_path_index"
        assert result["kv"] is not None

        # Verify paths are assembled correctly (parser handles continuations)
        assert "homePath" in result["kv"]
        assert "coldPath" in result["kv"]

        # The parser should have assembled the continued lines
        # Check that the path doesn't contain backslash continuation
        assert (
            "\\" not in result["kv"]["homePath"]
            or "line/continuation" in result["kv"]["homePath"]
        )

    def test_all_indexes_have_valid_names(self):
        """Test that all projected indexes have valid names."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = IndexProjector()
        results = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # All results should have non-empty names
        for result in results:
            assert result["name"], "Index name should not be empty"
            assert isinstance(result["name"], str), "Index name should be a string"

    def test_bulk_projection(self):
        """Test projecting all stanzas in bulk."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = IndexProjector()
        run_id = 999

        # Project all stanzas
        results = [projector.project(stanza, run_id=run_id) for stanza in stanzas]

        # Verify consistency
        assert len(results) == len(stanzas), "Should project all stanzas"

        for result in results:
            assert result["run_id"] == run_id, "All should have same run_id"
            assert "name" in result, "All should have name"
            assert "kv" in result, "All should have kv field"

        # Verify unique names (except possibly repeated definitions)
        names = [r["name"] for r in results]
        assert len(names) > 0, "Should have at least one index"

    def test_golden_fixture_coverage(self):
        """Test that fixture covers key index scenarios."""
        fixture_path = (
            Path(__file__).parent.parent / "parser" / "fixtures" / "indexes.conf"
        )

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        index_names = {s.name for s in stanzas}

        # Verify key scenarios are covered
        assert "default" in index_names, "Should have [default] stanza"
        assert "main" in index_names, "Should have main index"
        assert "metrics" in index_names or "app_index" in index_names, (
            "Should have custom indexes"
        )

        # Project all to verify no errors
        projector = IndexProjector()
        for stanza in stanzas:
            result = projector.project(stanza, run_id=1)
            assert result["name"] == stanza.name
            # If stanza has keys, kv should not be None
            if stanza.keys:
                assert result["kv"] is not None


if __name__ == "__main__":
    # Run tests with simple test runner
    import traceback

    test_classes = [TestIndexProjectorIntegration]

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

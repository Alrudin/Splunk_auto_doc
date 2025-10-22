"""Integration tests for ServerclassProjector with real serverclass.conf fixtures."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.core import ConfParser
from app.projections.serverclasses import ServerclassProjector


class TestServerclassFixture:
    """Test ServerclassProjector with real serverclass.conf fixture."""

    def test_parse_and_project_serverclass_fixture(self):
        """Test parsing and projecting the serverclass.conf fixture."""
        # Parse the fixture file
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        # Project all stanzas
        projector = ServerclassProjector()
        projections = []
        for stanza in stanzas:
            result = projector.project(stanza, run_id=1)
            if result is not None:
                projections.append(result)

        # Should have serverclass definitions (not global or app assignments)
        # From fixture: production, indexers, universal_forwarders, test, deprecated
        assert len(projections) == 5

        # Verify projection structure
        for proj in projections:
            assert "run_id" in proj
            assert "name" in proj
            assert "whitelist" in proj
            assert "blacklist" in proj
            assert "app_assignments" in proj
            assert "kv" in proj
            assert proj["run_id"] == 1

    def test_production_serverclass(self):
        """Test projection of production serverclass from fixture."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        production_stanza = None
        for stanza in stanzas:
            if stanza.name == "serverClass:production":
                production_stanza = stanza
                break

        assert production_stanza is not None
        result = projector.project(production_stanza, run_id=1)

        assert result is not None
        assert result["name"] == "production"
        assert result["whitelist"] == {
            "0": "prod-hf-*.example.com",
            "1": "prod-uf-*.example.com",
        }
        assert result["blacklist"] == {
            "0": "*-test.example.com",
        }
        assert result["kv"] == {
            "restartSplunkd": "true",
            "restartSplunkWeb": "false",
        }

    def test_indexers_serverclass(self):
        """Test projection of indexers serverclass from fixture."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        indexers_stanza = None
        for stanza in stanzas:
            if stanza.name == "serverClass:indexers":
                indexers_stanza = stanza
                break

        assert indexers_stanza is not None
        result = projector.project(indexers_stanza, run_id=1)

        assert result is not None
        assert result["name"] == "indexers"
        assert result["whitelist"] == {
            "0": "idx-*.example.com",
        }
        assert result["blacklist"] is None
        assert result["kv"] == {
            "machineTypesFilter": "linux-x86_64, linux-aarch64",
        }

    def test_universal_forwarders_serverclass(self):
        """Test projection of universal_forwarders serverclass from fixture."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        uf_stanza = None
        for stanza in stanzas:
            if stanza.name == "serverClass:universal_forwarders":
                uf_stanza = stanza
                break

        assert uf_stanza is not None
        result = projector.project(uf_stanza, run_id=1)

        assert result is not None
        assert result["name"] == "universal_forwarders"
        assert result["whitelist"] == {
            "0": "uf-*.example.com",
        }
        assert result["blacklist"] == {
            "0": "hf-*.example.com",
        }

    def test_test_serverclass_with_overridden_whitelist(self):
        """Test projection of test serverclass with overridden whitelist.0."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        test_stanza = None
        for stanza in stanzas:
            if stanza.name == "serverClass:test":
                test_stanza = stanza
                break

        assert test_stanza is not None
        result = projector.project(test_stanza, run_id=1)

        assert result is not None
        assert result["name"] == "test"
        # whitelist.0 appears twice, last-wins should apply
        # In the fixture: whitelist.0 first = test1.example.com, then = test-new.example.com
        assert result["whitelist"]["0"] == "test-new.example.com"
        assert result["whitelist"]["1"] == "test2.example.com"

    def test_deprecated_serverclass(self):
        """Test projection of deprecated serverclass from fixture."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        deprecated_stanza = None
        for stanza in stanzas:
            if stanza.name == "serverClass:deprecated":
                deprecated_stanza = stanza
                break

        assert deprecated_stanza is not None
        result = projector.project(deprecated_stanza, run_id=1)

        assert result is not None
        assert result["name"] == "deprecated"
        assert result["whitelist"] == {
            "0": "*",
        }
        assert result["kv"] == {
            "stateOnClient": "disabled",
        }

    def test_global_stanza_not_projected(self):
        """Test that global stanza is not projected."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        global_stanza = None
        for stanza in stanzas:
            if stanza.name == "global":
                global_stanza = stanza
                break

        assert global_stanza is not None
        result = projector.project(global_stanza, run_id=1)

        # Global stanzas should not be projected
        assert result is None

    def test_app_assignment_stanzas_not_projected(self):
        """Test that app assignment stanzas are not projected."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        app_stanzas = []
        for stanza in stanzas:
            if ":app:" in stanza.name:
                app_stanzas.append(stanza)

        assert len(app_stanzas) > 0  # Fixture should have app assignment stanzas

        # None of the app assignment stanzas should be projected
        for stanza in app_stanzas:
            result = projector.project(stanza, run_id=1)
            assert result is None


class TestEdgeCases:
    """Test edge cases in serverclass projection."""

    def test_serverclass_with_continuation_line(self):
        """Test that continuation lines are handled by parser."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        # Find the production:app:TA-custom-app stanza with continuation
        app_stanza = None
        for stanza in stanzas:
            if stanza.name == "serverClass:production:app:TA-custom-app":
                app_stanza = stanza
                break

        assert app_stanza is not None
        # Verify continuation line was handled
        assert "repositoryLocation" in app_stanza.keys
        # The value should have the continuation merged
        assert "TA-custom-app" in app_stanza.keys["repositoryLocation"]


class TestProvenance:
    """Test provenance preservation in projections."""

    def test_provenance_preserved(self):
        """Test that provenance metadata is preserved in projections."""
        parser = ConfParser()
        fixture_path = Path(__file__).parent.parent / "parser" / "fixtures" / "serverclass.conf"
        stanzas = parser.parse_file(str(fixture_path))

        projector = ServerclassProjector()
        for stanza in stanzas:
            result = projector.project(stanza, run_id=1)
            if result is not None:
                # All projections should preserve provenance (even if None)
                assert "app" in result
                assert "scope" in result
                assert "layer" in result


def run_tests():
    """Run all test classes."""
    import inspect

    # Get all test classes in this module
    current_module = sys.modules[__name__]
    test_classes = [
        obj
        for name, obj in inspect.getmembers(current_module)
        if inspect.isclass(obj) and name.startswith("Test")
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        print(f"{test_class.__name__}:")
        test_instance = test_class()
        test_methods = [
            method
            for method in dir(test_instance)
            if method.startswith("test_") and callable(getattr(test_instance, method))
        ]

        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")

        print()

    print(f"Tests passed: {passed_tests}/{total_tests}")
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

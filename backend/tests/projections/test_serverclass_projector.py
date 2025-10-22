"""Unit tests for ServerclassProjector - serverclass.conf typed projection."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.types import ParsedStanza, Provenance
from app.projections.serverclasses import ServerclassProjector


class TestServerclassNameExtraction:
    """Test serverclass name extraction from stanza names."""

    def test_simple_serverclass(self):
        """Test extraction of simple serverclass name."""
        projector = ServerclassProjector()
        assert projector._extract_serverclass_name("serverClass:production") == "production"

    def test_serverclass_with_underscores(self):
        """Test serverclass with underscores in name."""
        projector = ServerclassProjector()
        assert projector._extract_serverclass_name("serverClass:universal_forwarders") == "universal_forwarders"

    def test_serverclass_with_numbers(self):
        """Test serverclass with numbers in name."""
        projector = ServerclassProjector()
        assert projector._extract_serverclass_name("serverClass:prod123") == "prod123"

    def test_serverclass_app_assignment(self):
        """Test extraction from app assignment stanza."""
        projector = ServerclassProjector()
        assert projector._extract_serverclass_name("serverClass:production:app:Splunk_TA_nix") == "production"

    def test_global_stanza(self):
        """Test that global stanza has no serverclass name."""
        projector = ServerclassProjector()
        assert projector._extract_serverclass_name("global") is None

    def test_non_serverclass_stanza(self):
        """Test that non-serverclass stanzas return None."""
        projector = ServerclassProjector()
        assert projector._extract_serverclass_name("default") is None
        assert projector._extract_serverclass_name("someOtherStanza") is None


class TestNumberedPatternsExtraction:
    """Test whitelist/blacklist numbered patterns extraction."""

    def test_whitelist_single_pattern(self):
        """Test extraction of single whitelist pattern."""
        projector = ServerclassProjector()
        keys = {"whitelist.0": "prod-*.example.com"}
        result = projector._extract_numbered_patterns(keys, "whitelist")
        assert result == {"0": "prod-*.example.com"}

    def test_whitelist_multiple_patterns(self):
        """Test extraction of multiple whitelist patterns."""
        projector = ServerclassProjector()
        keys = {
            "whitelist.0": "prod-hf-*.example.com",
            "whitelist.1": "prod-uf-*.example.com",
            "whitelist.2": "prod-idx-*.example.com",
        }
        result = projector._extract_numbered_patterns(keys, "whitelist")
        assert result == {
            "0": "prod-hf-*.example.com",
            "1": "prod-uf-*.example.com",
            "2": "prod-idx-*.example.com",
        }

    def test_blacklist_single_pattern(self):
        """Test extraction of single blacklist pattern."""
        projector = ServerclassProjector()
        keys = {"blacklist.0": "*-test.example.com"}
        result = projector._extract_numbered_patterns(keys, "blacklist")
        assert result == {"0": "*-test.example.com"}

    def test_blacklist_multiple_patterns(self):
        """Test extraction of multiple blacklist patterns."""
        projector = ServerclassProjector()
        keys = {
            "blacklist.0": "*-test.example.com",
            "blacklist.1": "*-dev.example.com",
        }
        result = projector._extract_numbered_patterns(keys, "blacklist")
        assert result == {
            "0": "*-test.example.com",
            "1": "*-dev.example.com",
        }

    def test_empty_patterns(self):
        """Test extraction with no patterns."""
        projector = ServerclassProjector()
        keys = {"restartSplunkd": "true"}
        result = projector._extract_numbered_patterns(keys, "whitelist")
        assert result == {}

    def test_mixed_keys(self):
        """Test extraction ignores non-pattern keys."""
        projector = ServerclassProjector()
        keys = {
            "whitelist.0": "*.example.com",
            "whitelist.1": "*.test.com",
            "restartSplunkd": "true",
            "stateOnClient": "enabled",
        }
        result = projector._extract_numbered_patterns(keys, "whitelist")
        assert result == {
            "0": "*.example.com",
            "1": "*.test.com",
        }

    def test_non_sequential_numbers(self):
        """Test extraction with non-sequential numbers."""
        projector = ServerclassProjector()
        keys = {
            "whitelist.0": "pattern0",
            "whitelist.5": "pattern5",
            "whitelist.10": "pattern10",
        }
        result = projector._extract_numbered_patterns(keys, "whitelist")
        assert result == {
            "0": "pattern0",
            "5": "pattern5",
            "10": "pattern10",
        }


class TestKVBuilding:
    """Test kv dictionary building."""

    def test_empty_keys(self):
        """Test kv building with empty keys."""
        projector = ServerclassProjector()
        kv = projector._build_kv({})
        assert kv == {}

    def test_only_whitelist_blacklist(self):
        """Test kv excludes whitelist and blacklist patterns."""
        projector = ServerclassProjector()
        keys = {
            "whitelist.0": "*.example.com",
            "blacklist.0": "*-test.example.com",
        }
        kv = projector._build_kv(keys)
        assert kv == {}

    def test_mixed_keys(self):
        """Test kv includes non-pattern keys."""
        projector = ServerclassProjector()
        keys = {
            "whitelist.0": "*.example.com",
            "blacklist.0": "*-test.example.com",
            "restartSplunkd": "true",
            "restartSplunkWeb": "false",
            "stateOnClient": "enabled",
        }
        kv = projector._build_kv(keys)
        assert kv == {
            "restartSplunkd": "true",
            "restartSplunkWeb": "false",
            "stateOnClient": "enabled",
        }

    def test_only_non_pattern_keys(self):
        """Test kv with only non-pattern keys."""
        projector = ServerclassProjector()
        keys = {
            "restartSplunkd": "true",
            "machineTypesFilter": "linux-x86_64",
        }
        kv = projector._build_kv(keys)
        assert kv == {
            "restartSplunkd": "true",
            "machineTypesFilter": "linux-x86_64",
        }


class TestProjection:
    """Test full projection of serverclass stanzas."""

    def test_simple_serverclass_projection(self):
        """Test projection of a simple serverclass with whitelist."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:production",
            keys={
                "whitelist.0": "prod-*.example.com",
                "restartSplunkd": "true",
            },
            provenance=Provenance(
                source_path="/opt/splunk/etc/system/local/serverclass.conf",
                app="system",
                scope="local",
                layer="system",
            ),
        )

        result = projector.project(stanza, run_id=42)

        assert result is not None
        assert result["run_id"] == 42
        assert result["name"] == "production"
        assert result["whitelist"] == {"0": "prod-*.example.com"}
        assert result["blacklist"] is None
        assert result["app_assignments"] is None
        assert result["kv"] == {"restartSplunkd": "true"}
        assert result["app"] == "system"
        assert result["scope"] == "local"
        assert result["layer"] == "system"

    def test_serverclass_with_whitelist_and_blacklist(self):
        """Test projection with both whitelist and blacklist."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:production",
            keys={
                "whitelist.0": "prod-hf-*.example.com",
                "whitelist.1": "prod-uf-*.example.com",
                "blacklist.0": "*-test.example.com",
                "restartSplunkd": "true",
                "restartSplunkWeb": "false",
            },
            provenance=Provenance(
                source_path="/opt/splunk/etc/apps/deployment/local/serverclass.conf",
                app="deployment",
                scope="local",
                layer="app",
            ),
        )

        result = projector.project(stanza, run_id=1)

        assert result is not None
        assert result["name"] == "production"
        assert result["whitelist"] == {
            "0": "prod-hf-*.example.com",
            "1": "prod-uf-*.example.com",
        }
        assert result["blacklist"] == {"0": "*-test.example.com"}
        assert result["kv"] == {
            "restartSplunkd": "true",
            "restartSplunkWeb": "false",
        }

    def test_serverclass_no_patterns(self):
        """Test serverclass with no whitelist or blacklist."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:indexers",
            keys={
                "machineTypesFilter": "linux-x86_64",
                "restartSplunkd": "true",
            },
            provenance=Provenance(
                source_path="/opt/splunk/etc/system/local/serverclass.conf",
            ),
        )

        result = projector.project(stanza, run_id=1)

        assert result is not None
        assert result["name"] == "indexers"
        assert result["whitelist"] is None
        assert result["blacklist"] is None
        assert result["kv"] == {
            "machineTypesFilter": "linux-x86_64",
            "restartSplunkd": "true",
        }

    def test_app_assignment_stanza_skipped(self):
        """Test that app assignment stanzas are skipped."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:production:app:Splunk_TA_nix",
            keys={
                "stateOnClient": "enabled",
                "restartSplunkd": "true",
            },
            provenance=Provenance(
                source_path="/opt/splunk/etc/system/local/serverclass.conf",
            ),
        )

        result = projector.project(stanza, run_id=1)

        # App assignment stanzas should return None for now
        assert result is None

    def test_global_stanza_skipped(self):
        """Test that global stanza is skipped."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="global",
            keys={
                "restartSplunkWeb": "false",
                "restartSplunkd": "true",
            },
            provenance=Provenance(
                source_path="/opt/splunk/etc/system/local/serverclass.conf",
            ),
        )

        result = projector.project(stanza, run_id=1)

        assert result is None

    def test_no_provenance(self):
        """Test projection with no provenance metadata."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:test",
            keys={
                "whitelist.0": "test-*.example.com",
            },
        )

        result = projector.project(stanza, run_id=1)

        assert result is not None
        assert result["name"] == "test"
        assert result["app"] is None
        assert result["scope"] is None
        assert result["layer"] is None

    def test_empty_kv_stored_as_none(self):
        """Test that empty kv is stored as None."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:minimal",
            keys={
                "whitelist.0": "*.example.com",
            },
        )

        result = projector.project(stanza, run_id=1)

        assert result is not None
        assert result["kv"] is None

    def test_empty_whitelist_stored_as_none(self):
        """Test that empty whitelist is stored as None."""
        projector = ServerclassProjector()
        stanza = ParsedStanza(
            name="serverClass:minimal",
            keys={
                "restartSplunkd": "true",
            },
        )

        result = projector.project(stanza, run_id=1)

        assert result is not None
        assert result["whitelist"] is None


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

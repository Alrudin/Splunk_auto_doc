"""Golden fixture tests for real-world Splunk .conf files.

These tests parse actual Splunk configuration samples and verify that
the parser produces expected results for production-like scenarios.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser

# Base path for fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGoldenFixtures:
    """Test parser against real-world configuration files."""

    def test_hf_inputs_conf(self):
        """Test parsing Heavy Forwarder inputs.conf."""
        parser = ConfParser()
        fixture_path = FIXTURES_DIR / "hf_inputs.conf"
        stanzas = parser.parse_file(fixture_path)

        # Should have multiple stanzas
        assert len(stanzas) > 0

        # Check for default stanza
        default_stanzas = [s for s in stanzas if s.name == "default"]
        assert len(default_stanzas) == 1
        assert default_stanzas[0].keys["host"] == "hf-01.example.com"

        # Check monitor input
        monitor_stanzas = [
            s for s in stanzas if s.name.startswith("monitor:///var/log/app/")
        ]
        assert len(monitor_stanzas) >= 1
        monitor = monitor_stanzas[0]
        assert monitor.keys["index"] == "main"
        assert monitor.keys["sourcetype"] == "app:log"

        # Check TCP input
        tcp_stanzas = [s for s in stanzas if s.name == "tcp://9997"]
        assert len(tcp_stanzas) == 1
        assert tcp_stanzas[0].keys["connection_host"] == "ip"

        # Check line continuation
        script_stanzas = [s for s in stanzas if s.name.startswith("script://")]
        assert len(script_stanzas) == 1
        # Verify continuation was merged
        assert "description" in script_stanzas[0].keys
        assert "multiple lines" in script_stanzas[0].keys["description"]

        # Check last-wins for repeated key
        debug_stanzas = [
            s for s in stanzas if "debug.log" in s.name
        ]
        assert len(debug_stanzas) >= 1
        # Final index should be "debug" due to last-wins
        assert debug_stanzas[0].keys["index"] == "debug"

    def test_props_conf(self):
        """Test parsing props.conf with transforms."""
        parser = ConfParser()
        fixture_path = FIXTURES_DIR / "props.conf"
        stanzas = parser.parse_file(fixture_path)

        assert len(stanzas) > 0

        # Check default stanza
        default_stanzas = [s for s in stanzas if s.name == "default"]
        assert len(default_stanzas) == 1

        # Check sourcetype stanza
        app_log_stanzas = [s for s in stanzas if s.name == "app:log"]
        assert len(app_log_stanzas) == 1
        app_log = app_log_stanzas[0]
        assert "TRANSFORMS-routing" in app_log.keys
        assert "EXTRACT-fields" in app_log.keys

        # Check SEDCMD preservation
        custom_data_stanzas = [s for s in stanzas if s.name == "custom:data"]
        assert len(custom_data_stanzas) >= 1
        custom = custom_data_stanzas[0]
        assert "SEDCMD-remove_sensitive" in custom.keys
        assert "SEDCMD-normalize_dates" in custom.keys

        # Check continuation in transform list
        json_api_stanzas = [s for s in stanzas if s.name == "json:api"]
        if json_api_stanzas:
            json_api = json_api_stanzas[0]
            # Should have merged continuation lines
            cleanup_key = [k for k in json_api.keys if "cleanup" in k.lower()]
            assert len(cleanup_key) > 0

        # Check repeated keys (last-wins)
        multi_stanzas = [s for s in stanzas if s.name == "multi:transform"]
        if multi_stanzas:
            multi = multi_stanzas[0]
            # Last value for TRANSFORMS-first should be transform_a_override
            assert multi.keys.get("TRANSFORMS-first") == "transform_a_override"

    def test_transforms_conf(self):
        """Test parsing transforms.conf."""
        parser = ConfParser()
        fixture_path = FIXTURES_DIR / "transforms.conf"
        stanzas = parser.parse_file(fixture_path)

        assert len(stanzas) > 0

        # Check basic transform
        route_stanzas = [s for s in stanzas if "route_to_index" in s.name]
        # Should have 2 due to repeated definition
        assert len(route_stanzas) == 2

        # Last one should override
        last_route = route_stanzas[-1]
        assert "CRITICAL" in last_route.keys.get("REGEX", "") or "ERROR" in last_route.keys.get("REGEX", "")

        # Check DEST_KEY patterns
        for stanza in stanzas:
            if "DEST_KEY" in stanza.keys:
                dest_key = stanza.keys["DEST_KEY"]
                # Should be one of the known patterns
                assert any(
                    x in dest_key
                    for x in ["_MetaData:Index", "MetaData:Sourcetype", "_raw"]
                )

    def test_outputs_conf(self):
        """Test parsing outputs.conf."""
        parser = ConfParser()
        fixture_path = FIXTURES_DIR / "outputs.conf"
        stanzas = parser.parse_file(fixture_path)

        assert len(stanzas) > 0

        # Check tcpout default
        tcpout_stanzas = [s for s in stanzas if s.name == "tcpout"]
        assert len(tcpout_stanzas) == 1
        assert tcpout_stanzas[0].keys.get("defaultGroup") == "primary_indexers"

        # Check server groups
        primary_stanzas = [s for s in stanzas if "primary_indexers" in s.name]
        assert len(primary_stanzas) >= 1
        primary = primary_stanzas[0]
        assert "server" in primary.keys
        assert "indexer1.example.com" in primary.keys["server"]

        # Check last-wins for repeated server key
        dynamic_stanzas = [s for s in stanzas if "dynamic_group" in s.name]
        assert len(dynamic_stanzas) >= 1
        dynamic = dynamic_stanzas[0]
        # Last server value should have new1 and new2
        assert "new1.example.com" in dynamic.keys["server"]
        assert "new2.example.com" in dynamic.keys["server"]

    def test_serverclass_conf(self):
        """Test parsing serverclass.conf."""
        parser = ConfParser()
        fixture_path = FIXTURES_DIR / "serverclass.conf"
        stanzas = parser.parse_file(fixture_path)

        assert len(stanzas) > 0

        # Check global stanza
        global_stanzas = [s for s in stanzas if s.name == "global"]
        assert len(global_stanzas) == 1

        # Check server class
        prod_stanzas = [s for s in stanzas if s.name == "serverClass:production"]
        assert len(prod_stanzas) >= 1
        prod = prod_stanzas[0]
        assert "whitelist.0" in prod.keys
        assert "prod-hf-*" in prod.keys["whitelist.0"] or "prod-uf-*" in prod.keys.get("whitelist.1", "")

        # Check app assignments
        app_stanzas = [
            s for s in stanzas if ":app:" in s.name
        ]
        assert len(app_stanzas) > 0

        # Check repeated whitelist (last-wins)
        test_stanzas = [s for s in stanzas if s.name == "serverClass:test"]
        if test_stanzas:
            test = test_stanzas[0]
            # whitelist.0 should have been overridden
            assert test.keys["whitelist.0"] == "test-new.example.com"

    def test_indexes_conf(self):
        """Test parsing indexes.conf."""
        parser = ConfParser()
        fixture_path = FIXTURES_DIR / "indexes.conf"
        stanzas = parser.parse_file(fixture_path)

        assert len(stanzas) > 0

        # Check default stanza
        default_stanzas = [s for s in stanzas if s.name == "default"]
        assert len(default_stanzas) == 1
        default = default_stanzas[0]
        assert "frozenTimePeriodInSecs" in default.keys
        assert "homePath" in default.keys

        # Check main index
        main_stanzas = [s for s in stanzas if s.name == "main"]
        assert len(main_stanzas) == 1
        assert "maxTotalDataSizeMB" in main_stanzas[0].keys

        # Check metrics index
        metrics_stanzas = [s for s in stanzas if s.name == "metrics"]
        assert len(metrics_stanzas) >= 1
        metrics = metrics_stanzas[0]
        assert metrics.keys.get("datatype") == "metric"

        # Check repeated setting (last-wins)
        test_index_stanzas = [s for s in stanzas if s.name == "test_index"]
        if test_index_stanzas:
            test_index = test_index_stanzas[0]
            # Should be 50000 due to last-wins
            assert test_index.keys["maxTotalDataSizeMB"] == "50000"

        # Check line continuation
        long_path_stanzas = [s for s in stanzas if s.name == "long_path_index"]
        if long_path_stanzas:
            long_path = long_path_stanzas[0]
            # homePath should have continuation merged
            assert "db" in long_path.keys["homePath"]

    def test_stanza_ordering(self):
        """Test that stanza order is preserved across all fixtures."""
        parser = ConfParser()

        for fixture in FIXTURES_DIR.glob("*.conf"):
            stanzas = parser.parse_file(fixture)

            # Verify order_in_file is sequential
            for i, stanza in enumerate(stanzas):
                assert stanza.provenance.order_in_file == i

    def test_all_fixtures_parse_without_error(self):
        """Test that all fixtures parse without raising exceptions."""
        parser = ConfParser()
        fixture_count = 0

        for fixture in FIXTURES_DIR.glob("*.conf"):
            fixture_count += 1
            # Should not raise any exception
            stanzas = parser.parse_file(fixture)
            # Should have at least one stanza
            assert len(stanzas) > 0

        # Ensure we actually tested some fixtures
        assert fixture_count >= 6


def run_tests():
    """Run all golden fixture tests."""
    import sys

    test_class = TestGoldenFixtures()
    test_methods = [
        method
        for method in dir(test_class)
        if method.startswith("test_") and callable(getattr(test_class, method))
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    print("Golden Fixture Tests:")
    for method_name in test_methods:
        total_tests += 1
        try:
            method = getattr(test_class, method_name)
            method()
            print(f"  ✓ {method_name}")
            passed_tests += 1
        except AssertionError as e:
            print(f"  ✗ {method_name}: {e}")
            failed_tests.append(method_name)
        except Exception as e:
            print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
            failed_tests.append(method_name)

    print(f"\n{'=' * 60}")
    print(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
        sys.exit(1)
    else:
        print("\n✅ All golden fixture tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()

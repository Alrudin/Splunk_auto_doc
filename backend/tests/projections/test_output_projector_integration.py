"""Integration tests for OutputProjector with golden fixtures.

Tests the complete flow: parse outputs.conf → project to Output records.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser
from app.projections.outputs import OutputProjector

# Path to golden fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "parser" / "fixtures"


class TestGoldenFixtures:
    """Test projection with golden fixture files."""

    def test_outputs_conf(self):
        """Test projection of outputs.conf fixture."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        # Parse the file
        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Project all stanzas
        projector = OutputProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Should have multiple stanzas
        assert len(projections) > 0
        assert len(projections) == 7  # Based on fixture

        # Verify tcpout default stanza
        tcpout_default = next(
            (p for p in projections if p["group_name"] == "tcpout"), None
        )
        assert tcpout_default is not None
        assert tcpout_default["servers"] is None  # No server fields
        assert tcpout_default["kv"] is not None
        assert tcpout_default["kv"]["defaultGroup"] == "primary_indexers"
        assert tcpout_default["kv"]["indexAndForward"] == "false"
        assert tcpout_default["kv"]["forwardedindex.filter.disable"] == "true"

        # Verify primary_indexers group
        primary = next(
            (p for p in projections if p["group_name"] == "tcpout:primary_indexers"),
            None,
        )
        assert primary is not None
        assert primary["servers"] is not None
        assert "server" in primary["servers"]
        # Server list should contain all three indexers (comma-separated)
        # Note: These assertions verify configuration parsing, not URL sanitization
        # lgtm [py/incomplete-url-substring-sanitization]
        assert "indexer1.example.com:9997" in primary["servers"]["server"]
        # lgtm [py/incomplete-url-substring-sanitization]
        assert "indexer2.example.com:9997" in primary["servers"]["server"]
        # lgtm [py/incomplete-url-substring-sanitization]
        assert "indexer3.example.com:9997" in primary["servers"]["server"]
        # Configuration options in kv
        assert primary["kv"]["autoLBFrequency"] == "30"
        assert primary["kv"]["maxQueueSize"] == "10MB"
        assert primary["kv"]["compressed"] == "true"

        # Verify backup_indexers group
        backup = next(
            (p for p in projections if p["group_name"] == "tcpout:backup_indexers"),
            None,
        )
        assert backup is not None
        assert (
            backup["servers"]["server"]
            == "backup1.example.com:9997, backup2.example.com:9997"
        )
        assert backup["kv"]["autoLBFrequency"] == "60"

        # Verify syslog output
        syslog = next(
            (p for p in projections if p["group_name"] == "syslog:siem_output"), None
        )
        assert syslog is not None
        assert syslog["servers"]["server"] == "siem.example.com:514"
        assert syslog["kv"]["type"] == "tcp"
        assert syslog["kv"]["priority"] == "<134>"

        # Verify HTTP Event Collector output
        httpout = next(
            (p for p in projections if p["group_name"] == "httpout:hec_output"), None
        )
        assert httpout is not None
        assert (
            httpout["servers"]["uri"]
            == "https://hec.splunkcloud.com:8088/services/collector"
        )
        assert httpout["kv"]["token"] == "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        assert httpout["kv"]["sslVerifyServerCert"] == "true"

        # Verify clone group with target_group
        clone = next(
            (p for p in projections if p["group_name"] == "tcpout:clone_group"), None
        )
        assert clone is not None
        assert clone["servers"]["target_group"] == "primary_indexers, backup_indexers"
        # Only target_group, so kv should be None
        assert clone["kv"] is None

        # Verify dynamic group (last-wins semantics)
        dynamic = next(
            (p for p in projections if p["group_name"] == "tcpout:dynamic_group"), None
        )
        assert dynamic is not None
        # Should have the last server value (new1 and new2)
        assert (
            dynamic["servers"]["server"]
            == "new1.example.com:9997, new2.example.com:9997"
        )
        # Should NOT contain old1 or old2
        assert "old1.example.com" not in dynamic["servers"]["server"]
        assert "old2.example.com" not in dynamic["servers"]["server"]

    def test_last_wins_semantics(self):
        """Test that last-wins semantics are preserved through projection."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        # Find the stanza with repeated server key
        repeated_stanza = next(
            (s for s in stanzas if s.name == "tcpout:dynamic_group"), None
        )
        assert repeated_stanza is not None

        # Verify parser captured all three values in history
        assert len(repeated_stanza.key_history.get("server", [])) == 3
        assert repeated_stanza.key_history["server"][0] == "old1.example.com:9997"
        assert repeated_stanza.key_history["server"][1] == "old2.example.com:9997"
        assert (
            repeated_stanza.key_history["server"][2]
            == "new1.example.com:9997, new2.example.com:9997"
        )

        # Verify projection uses last value
        projector = OutputProjector()
        result = projector.project(repeated_stanza, run_id=1)
        assert (
            result["servers"]["server"]
            == "new1.example.com:9997, new2.example.com:9997"
        )

    def test_run_id_consistency(self):
        """Test that all projections use the same run_id."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = OutputProjector()
        run_id = 42
        projections = [projector.project(stanza, run_id=run_id) for stanza in stanzas]

        # All projections should have the same run_id
        for projection in projections:
            assert projection["run_id"] == run_id

    def test_all_stanza_types(self):
        """Test that all output types are properly projected."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = OutputProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # Collect unique output types (prefix before colon)
        output_types = set()
        for p in projections:
            group_name = p["group_name"]
            output_type = group_name.split(":")[0] if ":" in group_name else group_name
            output_types.add(output_type)

        # Should have tcpout, syslog, and httpout
        assert "tcpout" in output_types
        assert "syslog" in output_types
        assert "httpout" in output_types

    def test_server_vs_uri_separation(self):
        """Test that server and uri are properly separated by output type."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = OutputProjector()
        projections = [projector.project(stanza, run_id=1) for stanza in stanzas]

        # TCP outputs should use 'server'
        tcp_outputs = [
            p
            for p in projections
            if p["group_name"].startswith("tcpout:") and p["servers"]
        ]
        for tcp_out in tcp_outputs:
            if "server" in tcp_out["servers"] or "target_group" in tcp_out["servers"]:
                # Either server or target_group, but not uri
                assert "uri" not in tcp_out["servers"]

        # HTTP outputs should use 'uri'
        http_outputs = [
            p for p in projections if p["group_name"].startswith("httpout:")
        ]
        for http_out in http_outputs:
            if http_out["servers"]:
                assert "uri" in http_out["servers"]
                assert "server" not in http_out["servers"]


class TestPropertyTests:
    """Property-based tests for projection invariants."""

    def test_no_data_loss(self):
        """Test that all keys from stanza appear in either servers or kv."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = OutputProjector()

        for stanza in stanzas:
            projection = projector.project(stanza, run_id=1)

            # Collect all keys from projection
            projected_keys = set()
            if projection["servers"]:
                projected_keys.update(projection["servers"].keys())
            if projection["kv"]:
                projected_keys.update(projection["kv"].keys())

            # All original keys should be in projection
            original_keys = set(stanza.keys.keys())
            assert projected_keys == original_keys, (
                f"Key mismatch in stanza {stanza.name}: "
                f"original={original_keys}, projected={projected_keys}"
            )

    def test_no_key_duplication(self):
        """Test that no key appears in both servers and kv."""
        fixture_path = FIXTURES_DIR / "outputs.conf"

        parser = ConfParser()
        stanzas = parser.parse_file(str(fixture_path))

        projector = OutputProjector()

        for stanza in stanzas:
            projection = projector.project(stanza, run_id=1)

            if projection["servers"] and projection["kv"]:
                servers_keys = set(projection["servers"].keys())
                kv_keys = set(projection["kv"].keys())

                # No overlap allowed
                overlap = servers_keys & kv_keys
                assert len(overlap) == 0, (
                    f"Key duplication in stanza {stanza.name}: "
                    f"overlapping keys={overlap}"
                )


if __name__ == "__main__":
    import sys

    # Simple test runner
    test_classes = [TestGoldenFixtures, TestPropertyTests]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        test_instance = test_class()
        test_methods = [
            method
            for method in dir(test_instance)
            if method.startswith("test_") and callable(getattr(test_instance, method))
        ]

        for method_name in sorted(test_methods):
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ✗ {method_name}")
                print(f"    {e}")
                failed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}")
                print(f"    Unexpected error: {e}")
                failed_tests += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed_tests}/{total_tests} passed, {failed_tests} failed")
    print(f"{'=' * 60}")

    sys.exit(0 if failed_tests == 0 else 1)

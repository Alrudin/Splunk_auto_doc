"""Unit tests for OutputProjector - outputs.conf typed projection."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.types import ParsedStanza, Provenance
from app.projections.outputs import OutputProjector


class TestServersBuilding:
    """Test servers dict building with server-related fields."""

    def test_server_field_extracted(self):
        """Test that server field is extracted to servers dict."""
        projector = OutputProjector()
        keys = {
            "server": "indexer1.example.com:9997, indexer2.example.com:9997",
            "compressed": "true",
            "autoLBFrequency": "30",
        }
        servers = projector._build_servers(keys)
        assert "server" in servers
        assert (
            servers["server"] == "indexer1.example.com:9997, indexer2.example.com:9997"
        )

    def test_uri_field_extracted(self):
        """Test that uri field is extracted to servers dict."""
        projector = OutputProjector()
        keys = {
            "uri": "https://hec.splunkcloud.com:8088/services/collector",
            "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        }
        servers = projector._build_servers(keys)
        assert "uri" in servers
        assert servers["uri"] == "https://hec.splunkcloud.com:8088/services/collector"

    def test_target_group_extracted(self):
        """Test that target_group field is extracted to servers dict."""
        projector = OutputProjector()
        keys = {
            "target_group": "primary_indexers, backup_indexers",
            "compressed": "true",
        }
        servers = projector._build_servers(keys)
        assert "target_group" in servers
        assert servers["target_group"] == "primary_indexers, backup_indexers"

    def test_non_server_fields_excluded(self):
        """Test that non-server fields are not in servers dict."""
        projector = OutputProjector()
        keys = {
            "server": "indexer1.example.com:9997",
            "compressed": "true",
            "maxQueueSize": "10MB",
            "autoLBFrequency": "30",
        }
        servers = projector._build_servers(keys)
        assert "compressed" not in servers
        assert "maxQueueSize" not in servers
        assert "autoLBFrequency" not in servers

    def test_empty_servers(self):
        """Test with no server fields."""
        projector = OutputProjector()
        keys = {
            "defaultGroup": "primary_indexers",
            "indexAndForward": "false",
        }
        servers = projector._build_servers(keys)
        assert servers == {}

    def test_multiple_server_fields(self):
        """Test with multiple server-related fields."""
        projector = OutputProjector()
        keys = {
            "server": "indexer1.example.com:9997",
            "uri": "https://example.com",
            "target_group": "group1",
            "compressed": "true",
        }
        servers = projector._build_servers(keys)
        # Should only have one of server/uri/target_group in practice,
        # but projector should handle all if present
        assert "server" in servers
        assert "uri" in servers
        assert "target_group" in servers
        assert "compressed" not in servers


class TestKVBuilding:
    """Test kv dict building with non-server fields."""

    def test_server_field_excluded(self):
        """Test that server field is not in kv."""
        projector = OutputProjector()
        keys = {
            "server": "indexer1.example.com:9997",
            "compressed": "true",
        }
        kv = projector._build_kv(keys)
        assert "server" not in kv

    def test_uri_field_excluded(self):
        """Test that uri field is not in kv."""
        projector = OutputProjector()
        keys = {
            "uri": "https://hec.splunkcloud.com:8088/services/collector",
            "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        }
        kv = projector._build_kv(keys)
        assert "uri" not in kv
        assert "token" in kv

    def test_target_group_excluded(self):
        """Test that target_group field is not in kv."""
        projector = OutputProjector()
        keys = {
            "target_group": "primary_indexers, backup_indexers",
            "compressed": "true",
        }
        kv = projector._build_kv(keys)
        assert "target_group" not in kv
        assert "compressed" in kv

    def test_non_server_fields_included(self):
        """Test that non-server fields are in kv."""
        projector = OutputProjector()
        keys = {
            "server": "indexer1.example.com:9997",
            "compressed": "true",
            "maxQueueSize": "10MB",
            "autoLBFrequency": "30",
        }
        kv = projector._build_kv(keys)
        assert kv["compressed"] == "true"
        assert kv["maxQueueSize"] == "10MB"
        assert kv["autoLBFrequency"] == "30"

    def test_empty_keys(self):
        """Test with empty keys dict."""
        projector = OutputProjector()
        kv = projector._build_kv({})
        assert kv == {}

    def test_only_server_fields(self):
        """Test with only server fields."""
        projector = OutputProjector()
        keys = {
            "server": "indexer1.example.com:9997",
            "uri": "https://example.com",
        }
        kv = projector._build_kv(keys)
        assert kv == {}


class TestProjection:
    """Test complete projection of stanzas to Output records."""

    def test_tcpout_group_projection(self):
        """Test projection of tcpout group with servers."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/outputs.conf",
            app=None,
            scope="local",
            layer="system",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="tcpout:primary_indexers",
            keys={
                "server": "indexer1.example.com:9997, indexer2.example.com:9997",
                "autoLBFrequency": "30",
                "maxQueueSize": "10MB",
                "compressed": "true",
            },
            provenance=provenance,
        )

        projector = OutputProjector()
        result = projector.project(stanza, run_id=42)

        assert result["run_id"] == 42
        assert result["group_name"] == "tcpout:primary_indexers"
        assert result["servers"] is not None
        assert (
            result["servers"]["server"]
            == "indexer1.example.com:9997, indexer2.example.com:9997"
        )
        assert result["kv"] is not None
        assert result["kv"]["autoLBFrequency"] == "30"
        assert result["kv"]["maxQueueSize"] == "10MB"
        assert result["kv"]["compressed"] == "true"
        assert "server" not in result["kv"]

    def test_syslog_output_projection(self):
        """Test projection of syslog output."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/myapp/local/outputs.conf",
            app="myapp",
            scope="local",
            layer="app",
            order_in_file=1,
        )
        stanza = ParsedStanza(
            name="syslog:siem_output",
            keys={
                "server": "siem.example.com:514",
                "type": "tcp",
                "priority": "<134>",
            },
            provenance=provenance,
        )

        projector = OutputProjector()
        result = projector.project(stanza, run_id=100)

        assert result["run_id"] == 100
        assert result["group_name"] == "syslog:siem_output"
        assert result["servers"]["server"] == "siem.example.com:514"
        assert result["kv"]["type"] == "tcp"
        assert result["kv"]["priority"] == "<134>"

    def test_httpout_projection(self):
        """Test projection of HTTP Event Collector output."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/outputs.conf",
            app=None,
            scope="local",
            layer="system",
            order_in_file=2,
        )
        stanza = ParsedStanza(
            name="httpout:hec_output",
            keys={
                "uri": "https://hec.splunkcloud.com:8088/services/collector",
                "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "sslVerifyServerCert": "true",
            },
            provenance=provenance,
        )

        projector = OutputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["group_name"] == "httpout:hec_output"
        assert (
            result["servers"]["uri"]
            == "https://hec.splunkcloud.com:8088/services/collector"
        )
        assert result["kv"]["token"] == "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        assert result["kv"]["sslVerifyServerCert"] == "true"
        assert "uri" not in result["kv"]

    def test_tcpout_default_projection(self):
        """Test projection of default tcpout stanza."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/default/outputs.conf",
            app=None,
            scope="default",
            layer="system",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="tcpout",
            keys={
                "defaultGroup": "primary_indexers",
                "indexAndForward": "false",
                "forwardedindex.filter.disable": "true",
            },
            provenance=provenance,
        )

        projector = OutputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["group_name"] == "tcpout"
        # No server fields, so servers should be None
        assert result["servers"] is None
        # All fields in kv
        assert result["kv"]["defaultGroup"] == "primary_indexers"
        assert result["kv"]["indexAndForward"] == "false"
        assert result["kv"]["forwardedindex.filter.disable"] == "true"

    def test_clone_group_projection(self):
        """Test projection of clone group with target_group."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/myapp/local/outputs.conf",
            app="myapp",
            scope="local",
            layer="app",
            order_in_file=3,
        )
        stanza = ParsedStanza(
            name="tcpout:clone_group",
            keys={
                "target_group": "primary_indexers, backup_indexers",
            },
            provenance=provenance,
        )

        projector = OutputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["group_name"] == "tcpout:clone_group"
        assert result["servers"]["target_group"] == "primary_indexers, backup_indexers"
        # No other fields, so kv should be None
        assert result["kv"] is None

    def test_empty_stanza_projection(self):
        """Test projection of stanza with no keys."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/outputs.conf",
            app=None,
            scope="local",
            layer="system",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="tcpout:empty_group",
            keys={},
            provenance=provenance,
        )

        projector = OutputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["group_name"] == "tcpout:empty_group"
        assert result["servers"] is None
        assert result["kv"] is None


class TestPropertyTests:
    """Test projection invariants and properties."""

    def test_run_id_preserved(self):
        """Test that run_id is correctly preserved in projection."""
        stanza = ParsedStanza(
            name="tcpout:test",
            keys={"server": "test.example.com:9997"},
            provenance=None,
        )

        projector = OutputProjector()
        for run_id in [1, 42, 999]:
            result = projector.project(stanza, run_id=run_id)
            assert result["run_id"] == run_id

    def test_group_name_preserved(self):
        """Test that group name is preserved exactly as stanza name."""
        projector = OutputProjector()

        test_names = [
            "tcpout",
            "tcpout:primary_indexers",
            "syslog:siem_output",
            "httpout:hec_output",
            "tcpout:clone_group",
        ]

        for name in test_names:
            stanza = ParsedStanza(name=name, keys={}, provenance=None)
            result = projector.project(stanza, run_id=1)
            assert result["group_name"] == name

    def test_servers_kv_separation(self):
        """Test that server fields and kv fields are properly separated."""
        projector = OutputProjector()
        stanza = ParsedStanza(
            name="tcpout:test",
            keys={
                "server": "indexer1.example.com:9997",
                "compressed": "true",
                "maxQueueSize": "10MB",
            },
            provenance=None,
        )

        result = projector.project(stanza, run_id=1)

        # Server field should be in servers, not kv
        assert "server" in result["servers"]
        assert "server" not in result["kv"]

        # Other fields should be in kv, not servers
        assert "compressed" in result["kv"]
        assert "maxQueueSize" in result["kv"]
        assert "compressed" not in result["servers"]
        assert "maxQueueSize" not in result["servers"]


if __name__ == "__main__":
    import sys

    # Simple test runner
    test_classes = [
        TestServersBuilding,
        TestKVBuilding,
        TestProjection,
        TestPropertyTests,
    ]

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

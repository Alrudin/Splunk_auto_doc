"""Unit tests for InputProjector - inputs.conf typed projection."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.types import ParsedStanza, Provenance
from app.projections.inputs import InputProjector


class TestStanzaTypeExtraction:
    """Test stanza type extraction from stanza names."""

    def test_monitor_input(self):
        """Test extraction of monitor:// type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("monitor:///var/log/app.log") == "monitor"

    def test_tcp_input(self):
        """Test extraction of tcp:// type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("tcp://9997") == "tcp"

    def test_udp_input(self):
        """Test extraction of udp:// type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("udp://514") == "udp"

    def test_script_input(self):
        """Test extraction of script:// type."""
        projector = InputProjector()
        assert (
            projector._extract_stanza_type("script://./bin/custom_script.sh")
            == "script"
        )

    def test_wineventlog_input(self):
        """Test extraction of WinEventLog:// type."""
        projector = InputProjector()
        assert (
            projector._extract_stanza_type("WinEventLog://Application")
            == "wineventlog"
        )

    def test_splunktcp_input(self):
        """Test extraction of splunktcp:// type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("splunktcp://9997") == "splunktcp"

    def test_http_input(self):
        """Test extraction of http:// type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("http://collector") == "http"

    def test_fifo_input(self):
        """Test extraction of fifo:// type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("fifo:///tmp/mypipe") == "fifo"

    def test_default_stanza(self):
        """Test that default stanza has no type."""
        projector = InputProjector()
        assert projector._extract_stanza_type("default") is None

    def test_case_insensitive(self):
        """Test that type extraction is case-insensitive."""
        projector = InputProjector()
        assert projector._extract_stanza_type("Monitor:///var/log") == "monitor"
        assert projector._extract_stanza_type("TCP://9997") == "tcp"


class TestDisabledNormalization:
    """Test disabled field normalization."""

    def test_disabled_string_0(self):
        """Test disabled='0' converts to False."""
        projector = InputProjector()
        assert projector._normalize_disabled("0") is False

    def test_disabled_string_1(self):
        """Test disabled='1' converts to True."""
        projector = InputProjector()
        assert projector._normalize_disabled("1") is True

    def test_disabled_true(self):
        """Test disabled='true' converts to True."""
        projector = InputProjector()
        assert projector._normalize_disabled("true") is True
        assert projector._normalize_disabled("TRUE") is True
        assert projector._normalize_disabled("True") is True

    def test_disabled_false(self):
        """Test disabled='false' converts to False."""
        projector = InputProjector()
        assert projector._normalize_disabled("false") is False
        assert projector._normalize_disabled("FALSE") is False
        assert projector._normalize_disabled("False") is False

    def test_disabled_yes_no(self):
        """Test disabled='yes'/'no' conversion."""
        projector = InputProjector()
        assert projector._normalize_disabled("yes") is True
        assert projector._normalize_disabled("no") is False

    def test_disabled_none(self):
        """Test that None returns None."""
        projector = InputProjector()
        assert projector._normalize_disabled(None) is None

    def test_disabled_whitespace(self):
        """Test that whitespace is trimmed."""
        projector = InputProjector()
        assert projector._normalize_disabled("  0  ") is False
        assert projector._normalize_disabled("\t1\t") is True


class TestKVBuilding:
    """Test kv dict building with non-extracted fields."""

    def test_extracted_fields_excluded(self):
        """Test that extracted fields are not in kv."""
        projector = InputProjector()
        keys = {
            "index": "main",
            "sourcetype": "app:log",
            "disabled": "0",
            "followTail": "1",
            "recursive": "true",
        }
        kv = projector._build_kv(keys)
        assert "index" not in kv
        assert "sourcetype" not in kv
        assert "disabled" not in kv

    def test_non_extracted_fields_included(self):
        """Test that non-extracted fields are in kv."""
        projector = InputProjector()
        keys = {
            "index": "main",
            "followTail": "1",
            "recursive": "true",
            "ignoreOlderThan": "7d",
        }
        kv = projector._build_kv(keys)
        assert kv["followTail"] == "1"
        assert kv["recursive"] == "true"
        assert kv["ignoreOlderThan"] == "7d"

    def test_empty_keys(self):
        """Test with empty keys dict."""
        projector = InputProjector()
        kv = projector._build_kv({})
        assert kv == {}

    def test_only_extracted_fields(self):
        """Test with only extracted fields."""
        projector = InputProjector()
        keys = {"index": "main", "sourcetype": "app:log", "disabled": "0"}
        kv = projector._build_kv(keys)
        assert kv == {}


class TestProjection:
    """Test complete projection of stanzas to Input records."""

    def test_monitor_input_projection(self):
        """Test projection of monitor:// input."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/search/local/inputs.conf",
            app="search",
            scope="local",
            layer="app",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="monitor:///var/log/app.log",
            keys={
                "index": "main",
                "sourcetype": "app:log",
                "disabled": "0",
                "followTail": "1",
            },
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=42)

        assert result["run_id"] == 42
        assert (
            result["source_path"]
            == "/opt/splunk/etc/apps/search/local/inputs.conf"
        )
        assert result["stanza_type"] == "monitor"
        assert result["index"] == "main"
        assert result["sourcetype"] == "app:log"
        assert result["disabled"] is False
        assert result["kv"] == {"followTail": "1"}
        assert result["app"] == "search"
        assert result["scope"] == "local"
        assert result["layer"] == "app"

    def test_tcp_input_projection(self):
        """Test projection of tcp:// input."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/inputs.conf",
            app=None,
            scope="local",
            layer="system",
            order_in_file=1,
        )
        stanza = ParsedStanza(
            name="tcp://9997",
            keys={
                "disabled": "false",
                "connection_host": "ip",
                "sourcetype": "splunk:tcp",
            },
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=100)

        assert result["run_id"] == 100
        assert result["stanza_type"] == "tcp"
        assert result["index"] is None
        assert result["sourcetype"] == "splunk:tcp"
        assert result["disabled"] is False
        assert result["kv"] == {"connection_host": "ip"}
        assert result["app"] is None
        assert result["scope"] == "local"
        assert result["layer"] == "system"

    def test_default_stanza_projection(self):
        """Test projection of [default] stanza."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/myapp/default/inputs.conf",
            app="myapp",
            scope="default",
            layer="app",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="default",
            keys={"host": "hf-01.example.com", "index": "default"},
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["stanza_type"] is None
        assert result["index"] == "default"
        assert result["sourcetype"] is None
        assert result["disabled"] is None
        assert result["kv"] == {"host": "hf-01.example.com"}

    def test_disabled_enabled_input(self):
        """Test projection with disabled=1."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/test/local/inputs.conf",
            app="test",
            scope="local",
            layer="app",
        )
        stanza = ParsedStanza(
            name="monitor:///var/log/disabled.log",
            keys={"index": "test", "disabled": "1"},
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=5)

        assert result["disabled"] is True

    def test_no_provenance(self):
        """Test projection when provenance is None."""
        stanza = ParsedStanza(
            name="udp://514", keys={"sourcetype": "syslog"}, provenance=None
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=99)

        assert result["run_id"] == 99
        assert result["source_path"] == "<unknown>"
        assert result["stanza_type"] == "udp"
        assert result["app"] is None
        assert result["scope"] is None
        assert result["layer"] is None

    def test_wineventlog_projection(self):
        """Test projection of WinEventLog:// input."""
        provenance = Provenance(
            source_path="C:/Program Files/Splunk/etc/apps/windows/local/inputs.conf",
            app="windows",
            scope="local",
            layer="app",
        )
        stanza = ParsedStanza(
            name="WinEventLog://Application",
            keys={"disabled": "false", "index": "windows", "sourcetype": "WinEventLog:Application"},
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=50)

        assert result["stanza_type"] == "wineventlog"
        assert result["index"] == "windows"
        assert result["disabled"] is False

    def test_script_input_with_interval(self):
        """Test projection of script:// input with additional properties."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/custom/local/inputs.conf",
            app="custom",
            scope="local",
            layer="app",
        )
        stanza = ParsedStanza(
            name="script://./bin/custom_script.sh",
            keys={
                "disabled": "0",
                "interval": "300",
                "sourcetype": "custom:script",
                "description": "Custom monitoring script",
            },
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=25)

        assert result["stanza_type"] == "script"
        assert result["sourcetype"] == "custom:script"
        assert result["disabled"] is False
        assert result["kv"]["interval"] == "300"
        assert result["kv"]["description"] == "Custom monitoring script"

    def test_empty_kv_becomes_none(self):
        """Test that empty kv dict becomes None."""
        provenance = Provenance(source_path="/test/inputs.conf")
        stanza = ParsedStanza(
            name="tcp://9997",
            keys={"index": "main", "sourcetype": "test"},
            provenance=provenance,
        )

        projector = InputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["kv"] is None


class TestPropertyTests:
    """Property-based tests for projection invariants."""

    def test_run_id_preserved(self):
        """Test that run_id is always preserved."""
        projector = InputProjector()
        stanza = ParsedStanza(name="monitor:///test", provenance=None)

        for run_id in [1, 100, 999999]:
            result = projector.project(stanza, run_id=run_id)
            assert result["run_id"] == run_id

    def test_stanza_type_lowercase(self):
        """Test that stanza types are always lowercase."""
        projector = InputProjector()
        test_cases = [
            "Monitor:///test",
            "TCP://9997",
            "UDP://514",
            "WinEventLog://App",
        ]

        for name in test_cases:
            stanza = ParsedStanza(name=name, provenance=None)
            result = projector.project(stanza, run_id=1)
            if result["stanza_type"]:
                assert result["stanza_type"] == result["stanza_type"].lower()

    def test_provenance_metadata_preserved(self):
        """Test that provenance metadata is preserved in projection."""
        provenance = Provenance(
            source_path="/test/inputs.conf",
            app="testapp",
            scope="local",
            layer="app",
            order_in_file=5,
        )
        stanza = ParsedStanza(name="monitor:///test", provenance=provenance)

        projector = InputProjector()
        result = projector.project(stanza, run_id=1)

        assert result["source_path"] == provenance.source_path
        assert result["app"] == provenance.app
        assert result["scope"] == provenance.scope
        assert result["layer"] == provenance.layer


if __name__ == "__main__":
    # Run tests with simple test runner
    import traceback

    test_classes = [
        TestStanzaTypeExtraction,
        TestDisabledNormalization,
        TestKVBuilding,
        TestProjection,
        TestPropertyTests,
    ]

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

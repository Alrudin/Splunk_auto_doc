"""Unit tests for IndexProjector - indexes.conf typed projection."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.types import ParsedStanza, Provenance
from app.projections.indexes import IndexProjector


class TestKVBuilding:
    """Test kv dict building with all fields."""

    def test_all_fields_included(self):
        """Test that all fields are included in kv."""
        projector = IndexProjector()
        keys = {
            "homePath": "$SPLUNK_DB/main/db",
            "coldPath": "$SPLUNK_DB/main/colddb",
            "thawedPath": "$SPLUNK_DB/main/thaweddb",
            "maxTotalDataSizeMB": "500000",
            "frozenTimePeriodInSecs": "188697600",
        }
        kv = projector._build_kv(keys)
        assert kv["homePath"] == "$SPLUNK_DB/main/db"
        assert kv["coldPath"] == "$SPLUNK_DB/main/colddb"
        assert kv["thawedPath"] == "$SPLUNK_DB/main/thaweddb"
        assert kv["maxTotalDataSizeMB"] == "500000"
        assert kv["frozenTimePeriodInSecs"] == "188697600"

    def test_empty_keys(self):
        """Test with empty keys dict."""
        projector = IndexProjector()
        kv = projector._build_kv({})
        assert kv == {}

    def test_single_field(self):
        """Test with single field."""
        projector = IndexProjector()
        keys = {"datatype": "metric"}
        kv = projector._build_kv(keys)
        assert kv == {"datatype": "metric"}

    def test_special_characters(self):
        """Test with special characters in values."""
        projector = IndexProjector()
        keys = {
            "homePath": "/path/with spaces/db",
            "coldToFrozenDir": "/archive/$_index_name",
        }
        kv = projector._build_kv(keys)
        assert kv["homePath"] == "/path/with spaces/db"
        assert kv["coldToFrozenDir"] == "/archive/$_index_name"


class TestProjection:
    """Test complete projection of stanzas to Index records."""

    def test_main_index_projection(self):
        """Test projection of main index."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/indexes.conf",
            app=None,
            scope="local",
            layer="system",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="main",
            keys={
                "homePath": "$SPLUNK_DB/defaultdb/db",
                "coldPath": "$SPLUNK_DB/defaultdb/colddb",
                "thawedPath": "$SPLUNK_DB/defaultdb/thaweddb",
                "maxTotalDataSizeMB": "1000000",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=42)

        assert result["run_id"] == 42
        assert result["name"] == "main"
        assert result["kv"]["homePath"] == "$SPLUNK_DB/defaultdb/db"
        assert result["kv"]["coldPath"] == "$SPLUNK_DB/defaultdb/colddb"
        assert result["kv"]["thawedPath"] == "$SPLUNK_DB/defaultdb/thaweddb"
        assert result["kv"]["maxTotalDataSizeMB"] == "1000000"

    def test_custom_app_index_projection(self):
        """Test projection of custom application index."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/myapp/local/indexes.conf",
            app="myapp",
            scope="local",
            layer="app",
            order_in_file=1,
        )
        stanza = ParsedStanza(
            name="app_index",
            keys={
                "homePath": "/fast-storage/splunk/app_index/db",
                "coldPath": "/archive-storage/splunk/app_index/colddb",
                "thawedPath": "/archive-storage/splunk/app_index/thaweddb",
                "frozenTimePeriodInSecs": "31536000",
                "maxTotalDataSizeMB": "250000",
                "maxHotBuckets": "10",
                "maxWarmDBCount": "300",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=100)

        assert result["run_id"] == 100
        assert result["name"] == "app_index"
        assert result["kv"]["homePath"] == "/fast-storage/splunk/app_index/db"
        assert result["kv"]["coldPath"] == "/archive-storage/splunk/app_index/colddb"
        assert result["kv"]["frozenTimePeriodInSecs"] == "31536000"
        assert result["kv"]["maxTotalDataSizeMB"] == "250000"
        assert result["kv"]["maxHotBuckets"] == "10"
        assert result["kv"]["maxWarmDBCount"] == "300"

    def test_metrics_index_projection(self):
        """Test projection of metrics index with datatype."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/indexes.conf",
            app=None,
            scope="local",
            layer="system",
            order_in_file=2,
        )
        stanza = ParsedStanza(
            name="metrics",
            keys={
                "datatype": "metric",
                "frozenTimePeriodInSecs": "7776000",
                "maxTotalDataSizeMB": "50000",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=50)

        assert result["run_id"] == 50
        assert result["name"] == "metrics"
        assert result["kv"]["datatype"] == "metric"
        assert result["kv"]["frozenTimePeriodInSecs"] == "7776000"
        assert result["kv"]["maxTotalDataSizeMB"] == "50000"

    def test_default_stanza_projection(self):
        """Test projection of [default] stanza."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/default/indexes.conf",
            app=None,
            scope="default",
            layer="system",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="default",
            keys={
                "frozenTimePeriodInSecs": "188697600",
                "maxTotalDataSizeMB": "500000",
                "homePath": "$SPLUNK_DB/$_index_name/db",
                "coldPath": "$SPLUNK_DB/$_index_name/colddb",
                "thawedPath": "$SPLUNK_DB/$_index_name/thaweddb",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["name"] == "default"
        assert result["kv"]["frozenTimePeriodInSecs"] == "188697600"
        assert result["kv"]["homePath"] == "$SPLUNK_DB/$_index_name/db"

    def test_audit_index_with_frozen_dir(self):
        """Test projection of audit index with coldToFrozenDir."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/indexes.conf",
            app=None,
            scope="local",
            layer="system",
        )
        stanza = ParsedStanza(
            name="audit",
            keys={
                "homePath": "$SPLUNK_DB/audit/db",
                "coldPath": "$SPLUNK_DB/audit/colddb",
                "frozenTimePeriodInSecs": "315360000",
                "coldToFrozenDir": "/compliance-archive/audit",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=25)

        assert result["name"] == "audit"
        assert result["kv"]["frozenTimePeriodInSecs"] == "315360000"
        assert result["kv"]["coldToFrozenDir"] == "/compliance-archive/audit"

    def test_summary_index_projection(self):
        """Test projection of summary index."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/indexes.conf",
        )
        stanza = ParsedStanza(
            name="summary",
            keys={
                "frozenTimePeriodInSecs": "31536000",
                "maxTotalDataSizeMB": "100000",
                "maxHotBuckets": "3",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=5)

        assert result["name"] == "summary"
        assert result["kv"]["maxHotBuckets"] == "3"

    def test_no_provenance(self):
        """Test projection when provenance is None."""
        stanza = ParsedStanza(
            name="test_index",
            keys={"maxTotalDataSizeMB": "10000"},
            provenance=None,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=99)

        assert result["run_id"] == 99
        assert result["name"] == "test_index"
        assert result["kv"]["maxTotalDataSizeMB"] == "10000"

    def test_empty_kv_becomes_none(self):
        """Test that empty kv dict becomes None."""
        provenance = Provenance(source_path="/test/indexes.conf")
        stanza = ParsedStanza(
            name="empty_index",
            keys={},
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=1)

        assert result["kv"] is None

    def test_index_with_special_settings(self):
        """Test projection of index with various special settings."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/custom/local/indexes.conf",
            app="custom",
            scope="local",
            layer="app",
        )
        stanza = ParsedStanza(
            name="special_index",
            keys={
                "homePath": "$SPLUNK_DB/special/db",
                "coldPath": "$SPLUNK_DB/special/colddb",
                "maxHotBuckets": "10",
                "maxWarmDBCount": "300",
                "maxDataSize": "auto",
                "frozenTimePeriodInSecs": "94608000",
                "maxTotalDataSizeMB": "250000",
                "compressRawdata": "true",
                "enableTsidxReduction": "true",
                "tsidxReductionCheckPeriodInSec": "600",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=75)

        assert result["name"] == "special_index"
        assert result["kv"]["maxDataSize"] == "auto"
        assert result["kv"]["compressRawdata"] == "true"
        assert result["kv"]["enableTsidxReduction"] == "true"
        assert result["kv"]["tsidxReductionCheckPeriodInSec"] == "600"

    def test_index_with_replication_settings(self):
        """Test projection of index with replication settings."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/indexes.conf",
        )
        stanza = ParsedStanza(
            name="replicated_index",
            keys={
                "homePath": "$SPLUNK_DB/replicated/db",
                "coldPath": "$SPLUNK_DB/replicated/colddb",
                "repFactor": "auto",
                "maxGlobalRawDataSizeMB": "10000",
            },
            provenance=provenance,
        )

        projector = IndexProjector()
        result = projector.project(stanza, run_id=33)

        assert result["name"] == "replicated_index"
        assert result["kv"]["repFactor"] == "auto"
        assert result["kv"]["maxGlobalRawDataSizeMB"] == "10000"


class TestPropertyTests:
    """Property-based tests for projection invariants."""

    def test_run_id_preserved(self):
        """Test that run_id is always preserved."""
        projector = IndexProjector()
        stanza = ParsedStanza(name="test_index", provenance=None)

        for run_id in [1, 100, 999999]:
            result = projector.project(stanza, run_id=run_id)
            assert result["run_id"] == run_id

    def test_name_preserved(self):
        """Test that index name is always preserved exactly."""
        projector = IndexProjector()
        test_names = [
            "main",
            "app_index",
            "metrics",
            "audit",
            "default",
            "_internal",
            "summary",
            "test_index_123",
        ]

        for name in test_names:
            stanza = ParsedStanza(name=name, provenance=None)
            result = projector.project(stanza, run_id=1)
            assert result["name"] == name

    def test_all_keys_in_kv(self):
        """Test that all keys from stanza are in kv."""
        projector = IndexProjector()
        keys = {
            "homePath": "$SPLUNK_DB/test/db",
            "coldPath": "$SPLUNK_DB/test/colddb",
            "maxTotalDataSizeMB": "100000",
            "frozenTimePeriodInSecs": "31536000",
            "datatype": "event",
        }
        stanza = ParsedStanza(name="test", keys=keys, provenance=None)

        result = projector.project(stanza, run_id=1)

        # All keys should be in kv
        for key in keys:
            assert key in result["kv"]
            assert result["kv"][key] == keys[key]


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_index_name_with_special_chars(self):
        """Test index names with underscores and numbers."""
        projector = IndexProjector()
        test_names = ["app_index", "_internal", "test_123", "index-name"]

        for name in test_names:
            stanza = ParsedStanza(name=name, provenance=None)
            result = projector.project(stanza, run_id=1)
            assert result["name"] == name

    def test_large_retention_values(self):
        """Test with very large retention values."""
        projector = IndexProjector()
        stanza = ParsedStanza(
            name="longterm",
            keys={
                "frozenTimePeriodInSecs": "999999999",
                "maxTotalDataSizeMB": "9999999999",
            },
            provenance=None,
        )

        result = projector.project(stanza, run_id=1)
        assert result["kv"]["frozenTimePeriodInSecs"] == "999999999"
        assert result["kv"]["maxTotalDataSizeMB"] == "9999999999"

    def test_path_with_variables(self):
        """Test paths with Splunk variables."""
        projector = IndexProjector()
        stanza = ParsedStanza(
            name="var_test",
            keys={
                "homePath": "$SPLUNK_DB/$_index_name/db",
                "coldPath": "$SPLUNK_DB/$_index_name/colddb",
                "thawedPath": "$SPLUNK_DB/$_index_name/thaweddb",
            },
            provenance=None,
        )

        result = projector.project(stanza, run_id=1)
        assert result["kv"]["homePath"] == "$SPLUNK_DB/$_index_name/db"
        assert "$_index_name" in result["kv"]["coldPath"]

    def test_windows_paths(self):
        """Test with Windows-style paths."""
        projector = IndexProjector()
        stanza = ParsedStanza(
            name="windows_index",
            keys={
                "homePath": "C:\\Program Files\\Splunk\\var\\lib\\splunk\\main\\db",
                "coldPath": "D:\\SplunkArchive\\main\\colddb",
            },
            provenance=None,
        )

        result = projector.project(stanza, run_id=1)
        assert "C:\\" in result["kv"]["homePath"]
        assert "D:\\" in result["kv"]["coldPath"]

    def test_repeated_keys_last_wins(self):
        """Test that last-wins semantics are preserved from parser."""
        projector = IndexProjector()
        # Parser should have already applied last-wins
        stanza = ParsedStanza(
            name="test_index",
            keys={"maxTotalDataSizeMB": "50000"},  # Last value wins in parser
            provenance=None,
        )

        result = projector.project(stanza, run_id=1)
        assert result["kv"]["maxTotalDataSizeMB"] == "50000"


if __name__ == "__main__":
    # Run tests with simple test runner
    import traceback

    test_classes = [
        TestKVBuilding,
        TestProjection,
        TestPropertyTests,
        TestEdgeCases,
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
            except Exception:
                print(f"  ✗ {method_name} (error)")
                traceback.print_exc()
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 60}")

    if failed > 0:
        exit(1)

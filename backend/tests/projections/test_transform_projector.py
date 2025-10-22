"""Unit tests for TransformProjector - transforms.conf typed projection."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser.types import ParsedStanza, Provenance
from app.projections.transforms import TransformProjector


class TestDestKeyExtraction:
    """Test DEST_KEY extraction and normalization."""

    def test_metadata_index(self):
        """Test extraction of _MetaData:Index."""
        projector = TransformProjector()
        assert projector._extract_dest_key("_MetaData:Index") == "_MetaData:Index"

    def test_metadata_sourcetype(self):
        """Test extraction of MetaData:Sourcetype."""
        projector = TransformProjector()
        assert (
            projector._extract_dest_key("MetaData:Sourcetype") == "MetaData:Sourcetype"
        )

    def test_raw_dest_key(self):
        """Test extraction of _raw."""
        projector = TransformProjector()
        assert projector._extract_dest_key("_raw") == "_raw"

    def test_queue_dest_key(self):
        """Test extraction of queue."""
        projector = TransformProjector()
        assert projector._extract_dest_key("queue") == "queue"

    def test_none_value(self):
        """Test that None returns None."""
        projector = TransformProjector()
        assert projector._extract_dest_key(None) is None

    def test_whitespace_trimmed(self):
        """Test that whitespace is trimmed."""
        projector = TransformProjector()
        assert projector._extract_dest_key("  _MetaData:Index  ") == "_MetaData:Index"


class TestWritesMetaIndexDetection:
    """Test detection of writes to _MetaData:Index."""

    def test_metadata_index_lowercase(self):
        """Test detection with lowercase _metadata:index."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_index("_metadata:index") is True

    def test_metadata_index_uppercase(self):
        """Test detection with uppercase _MetaData:Index."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_index("_MetaData:Index") is True

    def test_metadata_index_mixedcase(self):
        """Test detection with mixed case _MetaData:index."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_index("_MetaData:index") is True

    def test_non_metadata_index(self):
        """Test that non-metadata DEST_KEY returns False."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_index("_raw") is False

    def test_none_value(self):
        """Test that None returns None."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_index(None) is None


class TestWritesMetaSourcetypeDetection:
    """Test detection of writes to _MetaData:Sourcetype or MetaData:Sourcetype."""

    def test_metadata_sourcetype_with_underscore(self):
        """Test detection with _MetaData:Sourcetype."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_sourcetype("_MetaData:Sourcetype") is True

    def test_metadata_sourcetype_without_underscore(self):
        """Test detection with MetaData:Sourcetype."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_sourcetype("MetaData:Sourcetype") is True

    def test_metadata_sourcetype_lowercase(self):
        """Test detection with lowercase metadata:sourcetype."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_sourcetype("metadata:sourcetype") is True

    def test_metadata_sourcetype_mixedcase(self):
        """Test detection with mixed case MetaData:sourcetype."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_sourcetype("MetaData:sourcetype") is True

    def test_non_metadata_sourcetype(self):
        """Test that non-metadata DEST_KEY returns False."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_sourcetype("_raw") is False

    def test_none_value(self):
        """Test that None returns None."""
        projector = TransformProjector()
        assert projector._detect_writes_meta_sourcetype(None) is None


class TestKVBuilding:
    """Test kv dict building with non-extracted fields."""

    def test_extracted_fields_excluded(self):
        """Test that extracted fields are not in kv."""
        projector = TransformProjector()
        keys = {
            "DEST_KEY": "_MetaData:Index",
            "REGEX": "level=ERROR",
            "FORMAT": "error_index",
            "PRIORITY": "100",
        }
        kv = projector._build_kv(keys)
        assert "DEST_KEY" not in kv
        assert "REGEX" not in kv
        assert "FORMAT" not in kv

    def test_non_extracted_fields_included(self):
        """Test that non-extracted fields are in kv."""
        projector = TransformProjector()
        keys = {
            "REGEX": "pattern",
            "PRIORITY": "100",
            "MV_ADD": "true",
            "WRITE_META": "true",
        }
        kv = projector._build_kv(keys)
        assert kv["PRIORITY"] == "100"
        assert kv["MV_ADD"] == "true"
        assert kv["WRITE_META"] == "true"

    def test_empty_keys(self):
        """Test with empty keys dict."""
        projector = TransformProjector()
        kv = projector._build_kv({})
        assert kv == {}

    def test_only_extracted_fields(self):
        """Test with only extracted fields."""
        projector = TransformProjector()
        keys = {
            "DEST_KEY": "_raw",
            "REGEX": "pattern",
            "FORMAT": "output",
        }
        kv = projector._build_kv(keys)
        assert kv == {}


class TestProjection:
    """Test complete projection of stanzas to Transform records."""

    def test_index_routing_transform(self):
        """Test projection of index routing transform."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/search/local/transforms.conf",
            app="search",
            scope="local",
            layer="app",
            order_in_file=0,
        )
        stanza = ParsedStanza(
            name="route_to_index",
            keys={
                "REGEX": "level=ERROR",
                "DEST_KEY": "_MetaData:Index",
                "FORMAT": "error_index",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=42)

        assert result["run_id"] == 42
        assert result["name"] == "route_to_index"
        assert result["dest_key"] == "_MetaData:Index"
        assert result["regex"] == "level=ERROR"
        assert result["format"] == "error_index"
        assert result["writes_meta_index"] is True
        assert result["writes_meta_sourcetype"] is False
        assert result["kv"] is None

    def test_sourcetype_routing_transform(self):
        """Test projection of sourcetype routing transform."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/myapp/default/transforms.conf",
            app="myapp",
            scope="default",
            layer="app",
        )
        stanza = ParsedStanza(
            name="override_sourcetype",
            keys={
                "REGEX": ".",
                "DEST_KEY": "MetaData:Sourcetype",
                "FORMAT": "sourcetype::overridden:log",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=100)

        assert result["run_id"] == 100
        assert result["name"] == "override_sourcetype"
        assert result["dest_key"] == "MetaData:Sourcetype"
        assert result["regex"] == "."
        assert result["format"] == "sourcetype::overridden:log"
        assert result["writes_meta_index"] is False
        assert result["writes_meta_sourcetype"] is True

    def test_field_extraction_transform(self):
        """Test projection of field extraction transform."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/system/local/transforms.conf",
        )
        stanza = ParsedStanza(
            name="extract_special_fields",
            keys={
                "REGEX": r"^(?P<event_id>\d+)\s+(?P<severity>\w+)",
                "FORMAT": "event_id::$1 severity::$2",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=5)

        assert result["run_id"] == 5
        assert result["name"] == "extract_special_fields"
        assert result["dest_key"] is None
        assert result["regex"] == r"^(?P<event_id>\d+)\s+(?P<severity>\w+)"
        assert result["format"] == "event_id::$1 severity::$2"
        assert result["writes_meta_index"] is None
        assert result["writes_meta_sourcetype"] is None
        assert result["kv"] is None

    def test_data_masking_transform(self):
        """Test projection of data masking transform."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/security/local/transforms.conf",
        )
        stanza = ParsedStanza(
            name="mask_sensitive_data",
            keys={
                "REGEX": r"(password|ssn|credit_card)=(\S+)",
                "FORMAT": "$1=***MASKED***",
                "DEST_KEY": "_raw",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=25)

        assert result["name"] == "mask_sensitive_data"
        assert result["dest_key"] == "_raw"
        assert result["regex"] == r"(password|ssn|credit_card)=(\S+)"
        assert result["format"] == "$1=***MASKED***"
        assert result["writes_meta_index"] is False
        assert result["writes_meta_sourcetype"] is False

    def test_transform_with_additional_properties(self):
        """Test projection with additional non-extracted fields."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/custom/local/transforms.conf",
        )
        stanza = ParsedStanza(
            name="complex_transform",
            keys={
                "REGEX": "pattern",
                "FORMAT": "output",
                "PRIORITY": "100",
                "MV_ADD": "true",
                "WRITE_META": "true",
                "LOOKAHEAD": "1000",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=10)

        assert result["regex"] == "pattern"
        assert result["format"] == "output"
        assert result["kv"]["PRIORITY"] == "100"
        assert result["kv"]["MV_ADD"] == "true"
        assert result["kv"]["WRITE_META"] == "true"
        assert result["kv"]["LOOKAHEAD"] == "1000"

    def test_minimal_transform(self):
        """Test projection with minimal fields."""
        provenance = Provenance(
            source_path="/opt/splunk/etc/apps/test/local/transforms.conf",
        )
        stanza = ParsedStanza(
            name="simple_transform",
            keys={
                "REGEX": "test",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=1)

        assert result["run_id"] == 1
        assert result["name"] == "simple_transform"
        assert result["dest_key"] is None
        assert result["regex"] == "test"
        assert result["format"] is None
        assert result["writes_meta_index"] is None
        assert result["writes_meta_sourcetype"] is None
        assert result["kv"] is None

    def test_empty_kv_becomes_none(self):
        """Test that empty kv dict becomes None."""
        provenance = Provenance(source_path="/test/transforms.conf")
        stanza = ParsedStanza(
            name="test_transform",
            keys={
                "REGEX": "pattern",
                "FORMAT": "output",
            },
            provenance=provenance,
        )

        projector = TransformProjector()
        result = projector.project(stanza, run_id=1)

        assert result["kv"] is None


class TestPropertyTests:
    """Property-based tests for projection invariants."""

    def test_run_id_preserved(self):
        """Test that run_id is always preserved."""
        projector = TransformProjector()
        stanza = ParsedStanza(name="test_transform", provenance=None)

        for run_id in [1, 100, 999999]:
            result = projector.project(stanza, run_id=run_id)
            assert result["run_id"] == run_id

    def test_name_always_present(self):
        """Test that name is always preserved from stanza."""
        projector = TransformProjector()
        test_names = [
            "route_to_index",
            "extract_fields",
            "mask_data",
            "complex-transform-123",
        ]

        for name in test_names:
            stanza = ParsedStanza(name=name, provenance=None)
            result = projector.project(stanza, run_id=1)
            assert result["name"] == name

    def test_boolean_flags_consistency(self):
        """Test that metadata write flags are consistent."""
        projector = TransformProjector()

        # Test index metadata
        stanza = ParsedStanza(
            name="test",
            keys={"DEST_KEY": "_MetaData:Index"},
            provenance=None,
        )
        result = projector.project(stanza, run_id=1)
        assert result["writes_meta_index"] is True
        assert result["writes_meta_sourcetype"] is False

        # Test sourcetype metadata
        stanza = ParsedStanza(
            name="test",
            keys={"DEST_KEY": "MetaData:Sourcetype"},
            provenance=None,
        )
        result = projector.project(stanza, run_id=1)
        assert result["writes_meta_index"] is False
        assert result["writes_meta_sourcetype"] is True

        # Test no metadata
        stanza = ParsedStanza(
            name="test",
            keys={"REGEX": "pattern"},
            provenance=None,
        )
        result = projector.project(stanza, run_id=1)
        assert result["writes_meta_index"] is None
        assert result["writes_meta_sourcetype"] is None


if __name__ == "__main__":
    # Run tests with simple test runner
    import traceback

    test_classes = [
        TestDestKeyExtraction,
        TestWritesMetaIndexDetection,
        TestWritesMetaSourcetypeDetection,
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
            except Exception:
                print(f"  ✗ {method_name} (error)")
                traceback.print_exc()
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 60}")

    if failed > 0:
        exit(1)

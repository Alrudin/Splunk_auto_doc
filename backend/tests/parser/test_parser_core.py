"""Unit tests for the Splunk .conf parser core functionality."""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser


class TestBasicParsing:
    """Test basic parsing functionality."""

    def test_simple_stanza(self):
        """Test parsing a simple stanza with key-value pairs."""
        content = """
[test_stanza]
key1 = value1
key2 = value2
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert len(stanzas) == 1
        assert stanzas[0].name == "test_stanza"
        assert stanzas[0].keys["key1"] == "value1"
        assert stanzas[0].keys["key2"] == "value2"

    def test_multiple_stanzas(self):
        """Test parsing multiple stanzas in order."""
        content = """
[stanza1]
key1 = value1

[stanza2]
key2 = value2

[stanza3]
key3 = value3
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert len(stanzas) == 3
        assert stanzas[0].name == "stanza1"
        assert stanzas[1].name == "stanza2"
        assert stanzas[2].name == "stanza3"

    def test_empty_file(self):
        """Test parsing an empty file."""
        parser = ConfParser()
        stanzas = parser.parse_string("")

        assert len(stanzas) == 0

    def test_stanza_with_whitespace(self):
        """Test handling of whitespace around stanza headers and keys."""
        content = """
[ test_stanza ]
  key1  =  value1
key2=value2
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert len(stanzas) == 1
        assert stanzas[0].name == "test_stanza"
        assert stanzas[0].keys["key1"] == "value1"
        assert stanzas[0].keys["key2"] == "value2"


class TestComments:
    """Test comment handling."""

    def test_full_line_comments(self):
        """Test that full-line comments are ignored."""
        content = """
# This is a comment
[test_stanza]
# Another comment
key1 = value1
# Comment at end
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert len(stanzas) == 1
        assert stanzas[0].name == "test_stanza"
        assert len(stanzas[0].keys) == 1

    def test_inline_comments(self):
        """Test inline comment removal."""
        content = """
[test_stanza]
key1 = value1 # inline comment
key2 = value2# no space before comment
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == "value1"
        assert stanzas[0].keys["key2"] == "value2"

    def test_hash_in_value(self):
        """Test that # in quoted values is preserved."""
        content = """
[test_stanza]
key1 = "value with # hash"
key2 = 'another # hash'
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        # The simple heuristic should preserve # in quotes
        assert "#" in stanzas[0].keys["key1"]
        assert "#" in stanzas[0].keys["key2"]


class TestLineContinuation:
    """Test line continuation handling."""

    def test_simple_continuation(self):
        """Test basic line continuation with backslash."""
        content = """
[test_stanza]
key1 = value1 \\
continued
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == "value1 continued"

    def test_multiple_continuations(self):
        """Test multiple line continuations."""
        content = """
[test_stanza]
key1 = line1 \\
line2 \\
line3
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == "line1 line2 line3"

    def test_continuation_with_whitespace(self):
        """Test continuation handling with various whitespace."""
        content = """
[test_stanza]
key1 = value1\\
  continued
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        # Leading whitespace on continuation line is preserved
        assert "continued" in stanzas[0].keys["key1"]


class TestRepeatedKeys:
    """Test repeated key handling (last-wins with history)."""

    def test_last_wins(self):
        """Test that last value wins for repeated keys."""
        content = """
[test_stanza]
key1 = value1
key1 = value2
key1 = value3
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == "value3"

    def test_key_history(self):
        """Test that key history is preserved."""
        content = """
[test_stanza]
key1 = value1
key1 = value2
key1 = value3
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        history = stanzas[0].key_history["key1"]
        assert len(history) == 3
        assert history[0] == "value1"
        assert history[1] == "value2"
        assert history[2] == "value3"

    def test_key_order(self):
        """Test that key order is preserved."""
        content = """
[test_stanza]
key1 = value1
key2 = value2
key1 = value3
key3 = value4
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].key_order == ["key1", "key2", "key1", "key3"]


class TestProvenance:
    """Test provenance metadata extraction."""

    def test_app_path_extraction(self):
        """Test extraction of app name from path."""
        parser = ConfParser()
        provenance = parser._extract_provenance(
            "/opt/splunk/etc/apps/search/local/inputs.conf"
        )

        assert provenance.app == "search"
        assert provenance.scope == "local"
        assert provenance.layer == "app"

    def test_system_path_extraction(self):
        """Test extraction from system path."""
        parser = ConfParser()
        provenance = parser._extract_provenance(
            "/opt/splunk/etc/system/default/outputs.conf"
        )

        assert provenance.app is None
        assert provenance.scope == "default"
        assert provenance.layer == "system"

    def test_order_in_file(self):
        """Test that order_in_file is tracked correctly."""
        content = """
[stanza1]
key1 = value1

[stanza2]
key2 = value2

[stanza3]
key3 = value3
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].provenance.order_in_file == 0
        assert stanzas[1].provenance.order_in_file == 1
        assert stanzas[2].provenance.order_in_file == 2


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_keys_before_stanza(self):
        """Test handling of keys before any stanza header."""
        content = """
key1 = value1
[stanza1]
key2 = value2
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        # Should create a default stanza for orphaned keys
        assert len(stanzas) == 2
        assert stanzas[0].name == "default"
        assert stanzas[0].keys["key1"] == "value1"
        assert stanzas[1].name == "stanza1"

    def test_empty_stanza(self):
        """Test stanza with no keys."""
        content = """
[empty_stanza]

[stanza_with_keys]
key1 = value1
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert len(stanzas) == 2
        assert stanzas[0].name == "empty_stanza"
        assert len(stanzas[0].keys) == 0

    def test_special_characters_in_stanza_name(self):
        """Test stanzas with special characters."""
        content = """
[monitor:///var/log/app.log]
index = main

[tcp://9997]
connection_host = ip
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert len(stanzas) == 2
        assert stanzas[0].name == "monitor:///var/log/app.log"
        assert stanzas[1].name == "tcp://9997"

    def test_equals_in_value(self):
        """Test values containing equals signs."""
        content = """
[test_stanza]
key1 = value=with=equals
regex = ^(?P<field>[^=]+)=(?P<value>.*)$
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == "value=with=equals"
        assert "=" in stanzas[0].keys["regex"]

    def test_empty_value(self):
        """Test keys with empty values."""
        content = """
[test_stanza]
key1 =
key2 =
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == ""
        assert stanzas[0].keys["key2"] == ""

    def test_unicode_content(self):
        """Test handling of unicode characters."""
        content = """
[test_stanza]
key1 = 日本語
key2 = Ñoño
key3 = 🎉
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        assert stanzas[0].keys["key1"] == "日本語"
        assert stanzas[0].keys["key2"] == "Ñoño"
        assert stanzas[0].keys["key3"] == "🎉"


class TestPropertyInvariants:
    """Test property-based invariants."""

    def test_order_preservation(self):
        """Test that stanza order matches input order."""
        content = """
[z_last]
key = value

[a_first]
key = value

[m_middle]
key = value
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        # Order should be z_last, a_first, m_middle (file order, not alphabetical)
        assert stanzas[0].name == "z_last"
        assert stanzas[1].name == "a_first"
        assert stanzas[2].name == "m_middle"

    def test_last_wins_semantic(self):
        """Test last-wins semantic for multiple stanzas with same name."""
        content = """
[duplicate]
key1 = first

[duplicate]
key1 = second
key2 = new
"""
        parser = ConfParser()
        stanzas = parser.parse_string(content)

        # Both stanzas should be preserved (they're separate in the file)
        assert len(stanzas) == 2
        assert stanzas[0].name == "duplicate"
        assert stanzas[1].name == "duplicate"
        assert stanzas[0].keys["key1"] == "first"
        assert stanzas[1].keys["key1"] == "second"


def run_tests():
    """Run all parser tests."""
    import sys

    # Collect all test classes
    test_classes = [
        TestBasicParsing,
        TestComments,
        TestLineContinuation,
        TestRepeatedKeys,
        TestProvenance,
        TestEdgeCases,
        TestPropertyInvariants,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        test_instance = test_class()

        # Get all test methods
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
            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                failed_tests.append(f"{test_class.__name__}.{method_name}")
            except Exception as e:
                print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
                failed_tests.append(f"{test_class.__name__}.{method_name}")

    print(f"\n{'=' * 60}")
    print(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()

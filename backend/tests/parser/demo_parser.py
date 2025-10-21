#!/usr/bin/env python3
"""Demo script showing the Splunk .conf parser in action.

This script demonstrates key features of the parser by parsing sample
configurations and displaying the results.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser


def demo_basic_parsing():
    """Demonstrate basic parsing functionality."""
    print("=" * 70)
    print("DEMO 1: Basic Parsing")
    print("=" * 70)

    sample = """
# Sample inputs.conf
[default]
host = myhost

[monitor:///var/log/app.log]
index = main
sourcetype = app:log
disabled = false
"""

    parser = ConfParser()
    stanzas = parser.parse_string(sample)

    print(f"\nParsed {len(stanzas)} stanzas:\n")
    for stanza in stanzas:
        print(f"[{stanza.name}]")
        for key, value in stanza.keys.items():
            print(f"  {key} = {value}")
        print()


def demo_line_continuation():
    """Demonstrate line continuation handling."""
    print("=" * 70)
    print("DEMO 2: Line Continuation")
    print("=" * 70)

    sample = """
[transform]
# Long regex spanning multiple lines
REGEX = ^(?P<timestamp>\\S+)\\s+ \\
(?P<level>\\w+)\\s+ \\
(?P<message>.*)$
"""

    parser = ConfParser()
    stanzas = parser.parse_string(sample)

    print("\nOriginal (with backslash continuations):")
    print(sample)

    print("\nParsed result:")
    for stanza in stanzas:
        print(f"[{stanza.name}]")
        for key, value in stanza.keys.items():
            print(f"  {key} = {value}")


def demo_repeated_keys():
    """Demonstrate repeated key handling."""
    print("\n" + "=" * 70)
    print("DEMO 3: Repeated Keys (Last-Wins with History)")
    print("=" * 70)

    sample = """
[test_stanza]
index = dev
sourcetype = test:data
index = staging
index = production
"""

    parser = ConfParser()
    stanzas = parser.parse_string(sample)

    stanza = stanzas[0]
    print(f"\n[{stanza.name}]")
    print("\nCurrent value (last-wins):")
    print(f"  index = {stanza.keys['index']}")

    print("\nComplete history:")
    for i, value in enumerate(stanza.key_history["index"], 1):
        print(f"  {i}. {value}")

    print("\nKey order (including repeats):")
    print(f"  {stanza.key_order}")


def demo_provenance():
    """Demonstrate provenance tracking."""
    print("\n" + "=" * 70)
    print("DEMO 4: Provenance Tracking")
    print("=" * 70)

    # Simulate parsing files from different paths
    paths = [
        "/opt/splunk/etc/apps/search/local/inputs.conf",
        "/opt/splunk/etc/apps/TA-myapp/default/props.conf",
        "/opt/splunk/etc/system/local/outputs.conf",
    ]

    parser = ConfParser()

    print("\nProvenance extracted from file paths:\n")
    for path in paths:
        provenance = parser._extract_provenance(path)
        print(f"Path: {path}")
        print(f"  App:   {provenance.app or 'N/A'}")
        print(f"  Scope: {provenance.scope or 'N/A'}")
        print(f"  Layer: {provenance.layer or 'N/A'}")
        print()


def demo_real_world_fixture():
    """Parse a real-world fixture file."""
    print("=" * 70)
    print("DEMO 5: Real-World Configuration")
    print("=" * 70)

    fixture_path = Path(__file__).parent / "fixtures" / "hf_inputs.conf"

    if not fixture_path.exists():
        print(f"\nFixture not found: {fixture_path}")
        return

    parser = ConfParser()
    stanzas = parser.parse_file(fixture_path)

    print(f"\nParsed {len(stanzas)} stanzas from {fixture_path.name}\n")

    # Show summary
    stanza_types = {}
    for stanza in stanzas:
        # Classify by type prefix
        prefix = stanza.name.split(":")[0] if ":" in stanza.name else "other"
        stanza_types[prefix] = stanza_types.get(prefix, 0) + 1

    print("Stanza types:")
    for stanza_type, count in sorted(stanza_types.items()):
        print(f"  {stanza_type}: {count}")

    print("\nSample stanzas:")
    for stanza in stanzas[:3]:
        print(f"\n[{stanza.name}]")
        for key, value in list(stanza.keys.items())[:3]:
            print(f"  {key} = {value}")
        if len(stanza.keys) > 3:
            print(f"  ... ({len(stanza.keys) - 3} more keys)")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Splunk .conf Parser Demo" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    demo_basic_parsing()
    demo_line_continuation()
    demo_repeated_keys()
    demo_provenance()
    demo_real_world_fixture()

    print("\n" + "=" * 70)
    print("Demo complete! Parser ready for production use.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

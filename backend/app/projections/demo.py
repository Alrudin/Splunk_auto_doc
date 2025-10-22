#!/usr/bin/env python3
"""Demo script showing InputProjector usage.

This script demonstrates how to parse inputs.conf and project stanzas
to typed Input records.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parser import ConfParser
from app.projections import InputProjector


def main() -> int:
    """Run the demo."""
    # Use the golden fixture
    fixture_path = (
        Path(__file__).parent.parent.parent
        / "tests"
        / "parser"
        / "fixtures"
        / "hf_inputs.conf"
    )

    if not fixture_path.exists():
        print(f"Error: Fixture file not found at {fixture_path}")
        return 1

    print("=" * 70)
    print("InputProjector Demo")
    print("=" * 70)
    print(f"\nParsing: {fixture_path.name}\n")

    # Step 1: Parse the file
    parser = ConfParser()
    stanzas = parser.parse_file(str(fixture_path))
    print(f"Parsed {len(stanzas)} stanzas\n")

    # Step 2: Project stanzas
    projector = InputProjector()

    print("-" * 70)
    print("Projection Results")
    print("-" * 70)

    for idx, stanza in enumerate(stanzas, 1):
        projection = projector.project(stanza, run_id=1)

        print(f"\n{idx}. Stanza: {stanza.name}")
        print(f"   Type: {projection['stanza_type'] or 'N/A'}")
        print(f"   Index: {projection['index'] or 'N/A'}")
        print(f"   Sourcetype: {projection['sourcetype'] or 'N/A'}")
        print(f"   Disabled: {projection['disabled']}")

        if projection["kv"]:
            print(f"   Additional properties: {list(projection['kv'].keys())}")

        if projection["app"] or projection["scope"]:
            print(
                f"   Provenance: app={projection['app']}, scope={projection['scope']}, layer={projection['layer']}"
            )

    # Show statistics
    print("\n" + "=" * 70)
    print("Statistics")
    print("=" * 70)

    projections = [projector.project(s, run_id=1) for s in stanzas]

    # Count by type
    type_counts: dict[str, int] = {}
    for p in projections:
        stanza_type = p["stanza_type"] or "default/other"
        type_counts[stanza_type] = type_counts.get(stanza_type, 0) + 1

    print("\nInput Types:")
    for input_type, count in sorted(type_counts.items()):
        print(f"  {input_type}: {count}")

    # Count disabled
    disabled_count = sum(1 for p in projections if p["disabled"] is True)
    enabled_count = sum(1 for p in projections if p["disabled"] is False)

    print("\nStatus:")
    print(f"  Enabled: {enabled_count}")
    print(f"  Disabled: {disabled_count}")
    print(f"  Unspecified: {len(projections) - enabled_count - disabled_count}")

    # Count with additional properties
    with_kv = sum(1 for p in projections if p["kv"])
    print(f"\nWith additional properties: {with_kv}/{len(projections)}")

    print("\n" + "=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Verification script for OutputProjector implementation.

This script demonstrates the complete flow:
1. Parse outputs.conf fixture
2. Project stanzas using OutputProjector
3. Display results in a readable format
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parser.core import ConfParser
from app.projections import OutputProjector


def main():
    """Run verification of OutputProjector."""
    print("=" * 70)
    print("OutputProjector Implementation Verification")
    print("=" * 70)

    # Parse outputs.conf fixture
    fixture_path = Path(__file__).parent / "parser" / "fixtures" / "outputs.conf"
    print(f"\n1. Parsing fixture: {fixture_path.name}")

    parser = ConfParser()
    stanzas = parser.parse_file(str(fixture_path))
    print(f"   Found {len(stanzas)} stanzas")

    # Project stanzas
    print("\n2. Projecting stanzas to Output records:")
    projector = OutputProjector()
    projections = []

    for stanza in stanzas:
        output_data = projector.project(stanza, run_id=1)
        projections.append(output_data)

        print(f"\n   Group: {output_data['group_name']}")
        print(f"   Run ID: {output_data['run_id']}")

        if output_data["servers"]:
            print("   Servers:")
            for key, value in output_data["servers"].items():
                if len(str(value)) > 60:
                    print(f"     {key}: {str(value)[:57]}...")
                else:
                    print(f"     {key}: {value}")
        else:
            print("   Servers: None")

        if output_data["kv"]:
            print("   Config:")
            for key, value in sorted(output_data["kv"].items()):
                print(f"     {key}: {value}")
        else:
            print("   Config: None")

    # Summary statistics
    print("\n" + "=" * 70)
    print("3. Summary Statistics:")
    print(f"   Total projections: {len(projections)}")

    with_servers = sum(1 for p in projections if p["servers"])
    print(f"   With servers: {with_servers}")

    with_kv = sum(1 for p in projections if p["kv"])
    print(f"   With config: {with_kv}")

    # Output types
    output_types = set()
    for p in projections:
        group_name = p["group_name"]
        output_type = group_name.split(":")[0] if ":" in group_name else group_name
        output_types.add(output_type)

    print(f"   Output types: {', '.join(sorted(output_types))}")

    # Verify data integrity
    print("\n4. Data Integrity Checks:")

    all_passed = True
    for projection in projections:
        # Check run_id
        if projection["run_id"] != 1:
            print(f"   ✗ FAIL: run_id mismatch in {projection['group_name']}")
            all_passed = False

        # Check group_name
        if not projection["group_name"]:
            print("   ✗ FAIL: empty group_name")
            all_passed = False

    if all_passed:
        print("   ✓ All data integrity checks passed")

    # Verify no key duplication
    print("\n5. Key Duplication Check:")
    duplication_found = False

    for projection in projections:
        if projection["servers"] and projection["kv"]:
            servers_keys = set(projection["servers"].keys())
            kv_keys = set(projection["kv"].keys())
            overlap = servers_keys & kv_keys

            if overlap:
                print(
                    f"   ✗ FAIL: Key duplication in {projection['group_name']}: {overlap}"
                )
                duplication_found = True

    if not duplication_found:
        print("   ✓ No key duplication detected")

    print("\n" + "=" * 70)
    print("Verification Complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

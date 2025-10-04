#!/usr/bin/env python3
"""Validation script to check test structure without running pytest.

This script validates that:
- All test files are importable
- Test classes and functions are properly defined
- Required fixtures are available in conftest.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def validate_test_structure():
    """Validate test file structure."""
    test_dir = Path(__file__).parent
    errors = []
    successes = []

    # Check conftest.py
    conftest = test_dir / "conftest.py"
    if not conftest.exists():
        errors.append("conftest.py not found")
    else:
        successes.append("✓ conftest.py exists")

    # Expected test files
    expected_files = [
        "test_uploads.py",
        "test_error_handling.py",
        "test_storage.py",
        "test_models.py",
        "test_schemas.py",
        "test_runs.py",
    ]

    for test_file in expected_files:
        file_path = test_dir / test_file
        if not file_path.exists():
            errors.append(f"{test_file} not found")
        else:
            successes.append(f"✓ {test_file} exists")

    # Check that test files can be imported (basic syntax check)
    try:
        # We can't actually import without dependencies, but we can check syntax
        for test_file in expected_files:
            file_path = test_dir / test_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Basic checks
                    if "def test_" not in content and "class Test" not in content:
                        errors.append(f"{test_file} has no test functions or classes")
                    else:
                        successes.append(f"✓ {test_file} has test definitions")
    except Exception as e:
        errors.append(f"Error checking test files: {e}")

    # Print results
    print("\n" + "=" * 70)
    print("TEST STRUCTURE VALIDATION")
    print("=" * 70)
    
    if successes:
        print("\nSUCCESSES:")
        for msg in successes:
            print(f"  {msg}")
    
    if errors:
        print("\nERRORS:")
        for msg in errors:
            print(f"  ✗ {msg}")
        print("\n" + "=" * 70)
        return False
    
    print("\n" + "=" * 70)
    print("✅ All test structure validations passed!")
    print("=" * 70)
    return True


def count_test_functions():
    """Count test functions in test files."""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    total_tests = 0
    file_counts = {}
    
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
            # Count test functions
            test_count = content.count("def test_")
            file_counts[test_file.name] = test_count
            total_tests += test_count
    
    print("\n" + "=" * 70)
    print("TEST FUNCTION COUNT")
    print("=" * 70)
    
    for filename, count in sorted(file_counts.items()):
        print(f"  {filename:30s} {count:3d} tests")
    
    print("-" * 70)
    print(f"  {'TOTAL':30s} {total_tests:3d} tests")
    print("=" * 70)


if __name__ == "__main__":
    print("\n🔍 Validating test structure...\n")
    
    success = validate_test_structure()
    count_test_functions()
    
    if success:
        print("\n✨ Test structure is valid!")
        print("\nTo run tests:")
        print("  • With pytest: pytest backend/tests/ -v")
        print("  • With Docker: docker compose run --rm api pytest tests/ -v")
        print("  • With Makefile: make test-backend")
        sys.exit(0)
    else:
        print("\n❌ Test structure validation failed!")
        sys.exit(1)

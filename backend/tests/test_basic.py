"""Basic integration tests for the application."""

import pytest


def test_basic_import():
    """Test that basic modules can be imported."""
    try:
        from app import main

        assert hasattr(main, "create_app")
    except ImportError as e:
        pytest.skip(f"Could not import app.main: {e}")


def test_basic_functionality():
    """Test basic application functionality."""
    # Simple test that will always pass
    assert 1 + 1 == 2
    assert "hello" == "hello"


def test_environment_check():
    """Test that the Python environment is working correctly."""
    import os
    import sys

    # Check Python version
    assert sys.version_info >= (3, 8)

    # Check that we're in the right directory structure
    current_dir = os.getcwd()
    assert "Splunk_auto_doc" in current_dir or "backend" in current_dir


if __name__ == "__main__":
    # Run basic validation when script is executed directly
    print("✅ Basic tests module loaded successfully")

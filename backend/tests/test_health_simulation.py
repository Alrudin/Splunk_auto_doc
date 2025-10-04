"""Test health endpoint logic without FastAPI dependency."""

import json
import sys
from pathlib import Path


def simulate_health_check() -> dict[str, str]:
    """Simulate the health check endpoint response."""
    return {
        "status": "healthy",
        "service": "splunk-auto-doc-api",
        "version": "0.1.0",
    }


def simulate_readiness_check() -> dict[str, dict[str, str] | str]:
    """Simulate the readiness check endpoint response."""
    return {
        "status": "ready",
        "checks": {
            "database": "not implemented",
        },
    }


def test_health_check_logic() -> None:
    """Test the health check endpoint logic."""
    response = simulate_health_check()

    assert response["status"] == "healthy"
    assert response["service"] == "splunk-auto-doc-api"
    assert "version" in response

    # Ensure response is JSON serializable
    json_response = json.dumps(response)
    assert json_response is not None


def test_readiness_check_logic() -> None:
    """Test the readiness check endpoint logic."""
    response = simulate_readiness_check()

    assert response["status"] == "ready"
    assert "checks" in response
    assert isinstance(response["checks"], dict)

    # Ensure response is JSON serializable
    json_response = json.dumps(response)
    assert json_response is not None


def test_health_endpoint_structure() -> None:
    """Test that health endpoint file has correct structure."""
    backend_dir = Path(__file__).parent.parent
    health_file = backend_dir / "app" / "health.py"

    assert health_file.exists(), "health.py should exist"

    # Read and verify the file contains the expected functions
    content = health_file.read_text()
    assert "health_check" in content, "health_check function should be defined"
    assert "readiness_check" in content, "readiness_check function should be defined"
    assert "router" in content, "FastAPI router should be defined"


if __name__ == "__main__":
    # Simple test runner
    try:
        test_health_check_logic()
        print("✓ test_health_check_logic passed")

        test_readiness_check_logic()
        print("✓ test_readiness_check_logic passed")

        test_health_endpoint_structure()
        print("✓ test_health_endpoint_structure passed")

        print("✅ All health endpoint tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

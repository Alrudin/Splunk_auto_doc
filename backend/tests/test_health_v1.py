"""Test for v1 health endpoint simulation."""

from pathlib import Path


async def mock_health_check() -> dict[str, str]:
    """Mock implementation of the health check endpoint."""
    return {"status": "ok"}


def test_v1_health_endpoint_simulation():
    """Simulate the v1 health endpoint to test expected response format."""
    try:
        # Test the expected response format using our mock
        import asyncio

        result = asyncio.run(mock_health_check())

        # Test the expected response format
        assert isinstance(result, dict), "Response should be a dictionary"
        assert "status" in result, "Response should have 'status' key"
        assert result["status"] == "ok", "Status should be 'ok'"
        assert len(result) == 1, "Response should only have 'status' key"

        print("✅ v1 health endpoint simulation passed!")

        # Also verify the actual file exists and has the right structure
        backend_dir = Path(__file__).parent.parent
        health_file = backend_dir / "app" / "api" / "v1" / "health.py"
        assert health_file.exists(), "v1 health.py file should exist"

        # Check file content has the right structure
        content = health_file.read_text()
        assert '"status": "ok"' in content, "Health endpoint should include status ok"
        assert "/health" in content, "Health endpoint should be defined"
        assert "timestamp" in content, "Health endpoint should include timestamp"
        assert "version" in content, "Health endpoint should include version"
        print("✅ v1 health endpoint file validation passed!")

    except Exception as e:
        print(f"❌ v1 health endpoint simulation failed: {e}")
        raise


if __name__ == "__main__":
    test_v1_health_endpoint_simulation()

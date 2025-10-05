"""Test for runs endpoints - fixed version."""

import pytest

try:
    from tests.conftest import DEPENDENCIES_AVAILABLE, SKIP_REASON
except ImportError:
    # Fallback for when SKIP_REASON is not available
    from tests.conftest import DEPENDENCIES_AVAILABLE

    SKIP_REASON = "Dependencies not available"


@pytest.mark.database
class TestRunsListEndpointFixed:
    """Tests for the GET /v1/runs endpoint - fixed version."""

    def test_list_runs_empty(self, client):
        """Test listing runs when database is empty."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip(SKIP_REASON)

        response = client.get("/v1/runs")

        assert response.status_code == 200
        data = response.json()

        assert data["runs"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 50

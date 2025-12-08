"""
Unit tests for system routes.

Tests cover basic route accessibility and response structure.
"""


class TestSystemRoutes:
    """Tests for /api/system/* endpoints."""

    def test_status_endpoint_accessible(self, api_client):
        """Status endpoint should be accessible."""
        response = api_client.get("/api/system/status")
        assert response.status_code == 200

    def test_connections_endpoint_accessible(self, api_client):
        """Connections endpoint should be accessible."""
        response = api_client.get("/api/system/connections")
        assert response.status_code == 200

    def test_info_endpoint_accessible(self, api_client):
        """Info endpoint should be accessible."""
        response = api_client.get("/api/system/info")
        assert response.status_code == 200

    def test_status_returns_json(self, api_client):
        """Status should return JSON response."""
        response = api_client.get("/api/system/status")
        data = response.json()
        assert isinstance(data, dict)

    def test_info_contains_system_data(self, api_client):
        """Info should contain system data."""
        response = api_client.get("/api/system/info")
        data = response.json()
        # Should have success and data fields
        assert "success" in data
        assert "data" in data
        # Data should have system info like platform
        assert "platform" in data.get("data", {})

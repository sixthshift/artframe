"""
Unit tests for plugin routes.

Tests cover basic route accessibility and response structure.
"""


class TestPluginRoutes:
    """Tests for /api/plugins/* endpoints."""

    def test_list_plugins_accessible(self, api_client):
        """List plugins endpoint should be accessible."""
        response = api_client.get("/api/plugins")
        assert response.status_code == 200

    def test_list_plugins_returns_json(self, api_client):
        """List plugins should return JSON."""
        response = api_client.get("/api/plugins")
        data = response.json()
        assert isinstance(data, dict)
        assert "success" in data

    def test_list_plugins_has_data_field(self, api_client):
        """List plugins should have data field."""
        response = api_client.get("/api/plugins")
        data = response.json()
        assert "data" in data
        # Data should be a list (may be empty)
        assert isinstance(data["data"], list)

    def test_get_nonexistent_plugin_returns_404(self, api_client):
        """Get non-existent plugin should return 404."""
        response = api_client.get("/api/plugins/nonexistent-plugin")
        assert response.status_code == 404

    def test_get_plugin_returns_error_detail(self, api_client):
        """Get non-existent plugin should include error detail."""
        response = api_client.get("/api/plugins/nonexistent-plugin")
        data = response.json()
        assert "detail" in data

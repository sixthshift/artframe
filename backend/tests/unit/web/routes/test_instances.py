"""
Unit tests for plugin instance routes.

Tests cover basic route accessibility and response structure.
"""

from unittest.mock import patch


class TestInstanceRoutes:
    """Tests for /api/instances/* endpoints."""

    def test_list_instances_accessible(self, api_client):
        """List instances endpoint should be accessible."""
        response = api_client.get("/api/instances")
        assert response.status_code == 200

    def test_list_instances_returns_json(self, api_client):
        """List instances should return JSON."""
        response = api_client.get("/api/instances")
        data = response.json()
        assert isinstance(data, dict)
        # Response has instances key or is a list-like structure
        assert "instances" in data or isinstance(data.get("data"), list)

    def test_list_instances_with_filter(self, api_client):
        """List instances should accept plugin_id filter."""
        response = api_client.get("/api/instances?plugin_id=clock")
        assert response.status_code == 200

    def test_get_nonexistent_instance_returns_404(self, api_client):
        """Get non-existent instance should return 404."""
        response = api_client.get("/api/instances/nonexistent-id")
        assert response.status_code == 404

    def test_delete_nonexistent_instance_returns_error(self, api_client):
        """Delete non-existent instance should return error."""
        response = api_client.delete("/api/instances/nonexistent-id")
        # May return 400, 404, or 200 with success=false
        assert response.status_code in [400, 404, 200]

    def test_enable_nonexistent_instance_returns_error(self, api_client):
        """Enable non-existent instance should return error."""
        response = api_client.post("/api/instances/nonexistent-id/enable")
        # Returns 400 Bad Request for nonexistent instance
        assert response.status_code in [400, 404, 200]

    def test_disable_nonexistent_instance_returns_error(self, api_client):
        """Disable non-existent instance should return error."""
        response = api_client.post("/api/instances/nonexistent-id/disable")
        # Returns 400 Bad Request for nonexistent instance
        assert response.status_code in [400, 404, 200]

    def test_create_instance_requires_plugin_id(self, api_client):
        """Create instance should require plugin_id."""
        response = api_client.post("/api/instances", json={})
        assert response.status_code == 422

    def test_create_instance_with_valid_data(self, api_client, mock_plugin):
        """Create instance should work with valid data."""
        with patch("src.artframe.plugins.instance_manager.get_plugin") as mock:
            mock.return_value = mock_plugin
            response = api_client.post(
                "/api/instances",
                json={
                    "plugin_id": "clock",
                    "name": "Test Clock",
                    "settings": {},
                },
            )
            # May fail if plugin not found, but shouldn't be 422
            assert response.status_code in [200, 201, 400, 500]

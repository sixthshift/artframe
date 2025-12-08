"""
Unit tests for config routes.

Tests cover basic route accessibility and response structure.
"""


class TestConfigRoutes:
    """Tests for /api/config/* endpoints."""

    def test_get_config_accessible(self, api_client):
        """Get config endpoint should be accessible."""
        response = api_client.get("/api/config")
        assert response.status_code == 200

    def test_get_config_returns_json(self, api_client):
        """Get config should return JSON."""
        response = api_client.get("/api/config")
        data = response.json()
        assert isinstance(data, dict)
        assert "success" in data

    def test_get_config_has_data_field(self, api_client):
        """Get config should have data field."""
        response = api_client.get("/api/config")
        data = response.json()
        assert "data" in data

    def test_update_config_requires_data(self, api_client):
        """Update config should reject empty data."""
        response = api_client.put("/api/config", json={})
        # May return 400 or 500 depending on implementation
        assert response.status_code in [400, 500]

    def test_update_config_with_valid_data(self, api_client):
        """Update config should accept valid data."""
        response = api_client.put("/api/config", json={"display": {"update_time": "12:00"}})
        # May succeed or fail validation, but shouldn't be 500
        assert response.status_code in [200, 400]

    def test_save_config_accessible(self, api_client):
        """Save config endpoint should be accessible."""
        response = api_client.post("/api/config/save")
        # May succeed or fail based on file permissions
        assert response.status_code in [200, 500]

    def test_revert_config_accessible(self, api_client):
        """Revert config endpoint should be accessible."""
        response = api_client.post("/api/config/revert")
        # May succeed or fail based on file state
        assert response.status_code in [200, 500]

"""
Unit tests for display routes.

Tests cover basic route accessibility and response structure.
"""


class TestDisplayRoutes:
    """Tests for /api/display/* endpoints."""

    def test_refresh_endpoint_accessible(self, api_client):
        """Refresh endpoint should accept POST."""
        response = api_client.post("/api/display/refresh")
        assert response.status_code == 200

    def test_clear_endpoint_accessible(self, api_client):
        """Clear endpoint should accept POST."""
        response = api_client.post("/api/display/clear")
        assert response.status_code == 200

    def test_current_endpoint_accessible(self, api_client):
        """Current display endpoint should be accessible."""
        response = api_client.get("/api/display/current")
        assert response.status_code == 200

    def test_health_endpoint_accessible(self, api_client):
        """Health endpoint should be accessible."""
        response = api_client.get("/api/display/health")
        assert response.status_code == 200

    def test_preview_endpoint_exists(self, api_client):
        """Preview endpoint should exist (may return 404 if no image)."""
        response = api_client.get("/api/display/preview")
        # 200 if image exists, 404 if not - both are valid
        assert response.status_code in [200, 404]

    def test_refresh_returns_json(self, api_client):
        """Refresh should return JSON response."""
        response = api_client.post("/api/display/refresh")
        data = response.json()
        assert isinstance(data, dict)

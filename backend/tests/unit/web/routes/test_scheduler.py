"""
Unit tests for scheduler routes.

Tests cover basic route accessibility and response structure.
"""


class TestSchedulerRoutes:
    """Tests for /api/scheduler/* endpoints."""

    def test_get_scheduler_status_accessible(self, api_client):
        """Scheduler status endpoint should be accessible."""
        response = api_client.get("/api/scheduler/status")
        assert response.status_code == 200

    def test_get_scheduler_status_returns_json(self, api_client):
        """Scheduler status should return JSON."""
        response = api_client.get("/api/scheduler/status")
        data = response.json()
        assert isinstance(data, dict)
        assert "success" in data

    def test_get_scheduler_status_has_data(self, api_client):
        """Scheduler status should have data field."""
        response = api_client.get("/api/scheduler/status")
        data = response.json()
        assert "data" in data

    def test_pause_scheduler_accessible(self, api_client):
        """Pause scheduler endpoint should be accessible."""
        response = api_client.post("/api/scheduler/pause")
        assert response.status_code == 200

    def test_pause_scheduler_returns_json(self, api_client):
        """Pause scheduler should return JSON."""
        response = api_client.post("/api/scheduler/pause")
        data = response.json()
        assert isinstance(data, dict)
        assert "success" in data

    def test_resume_scheduler_accessible(self, api_client):
        """Resume scheduler endpoint should be accessible."""
        response = api_client.post("/api/scheduler/resume")
        assert response.status_code == 200

    def test_resume_scheduler_returns_json(self, api_client):
        """Resume scheduler should return JSON."""
        response = api_client.post("/api/scheduler/resume")
        data = response.json()
        assert isinstance(data, dict)
        assert "success" in data

    def test_scheduler_pause_resume_cycle(self, api_client):
        """Scheduler should handle pause/resume cycle."""
        # Pause
        pause_response = api_client.post("/api/scheduler/pause")
        assert pause_response.status_code == 200

        # Resume
        resume_response = api_client.post("/api/scheduler/resume")
        assert resume_response.status_code == 200

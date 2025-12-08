"""
Unit tests for schedule routes.

Tests cover basic route accessibility and response structure.
"""


class TestScheduleRoutes:
    """Tests for /api/schedules/* endpoints."""

    def test_get_schedules_accessible(self, api_client):
        """Get schedules endpoint should be accessible."""
        response = api_client.get("/api/schedules")
        assert response.status_code == 200

    def test_get_schedules_returns_json(self, api_client):
        """Get schedules should return JSON."""
        response = api_client.get("/api/schedules")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_current_schedule_accessible(self, api_client):
        """Get current schedule endpoint should be accessible."""
        response = api_client.get("/api/schedules/current")
        assert response.status_code == 200

    def test_set_slot_with_valid_data(self, api_client):
        """Set slot should accept valid data."""
        response = api_client.post(
            "/api/schedules/slot",
            json={
                "day": 0,
                "hour": 9,
                "target_type": "instance",
                "target_id": "test-instance",
            },
        )
        assert response.status_code == 200

    def test_set_slot_with_boundary_day(self, api_client):
        """Set slot should handle boundary day values."""
        # Test day 6 (Sunday - valid boundary)
        response = api_client.post(
            "/api/schedules/slot",
            json={
                "day": 6,
                "hour": 9,
                "target_type": "instance",
                "target_id": "test",
            },
        )
        assert response.status_code == 200

    def test_set_slot_with_boundary_hour(self, api_client):
        """Set slot should handle boundary hour values."""
        # Test hour 23 (valid boundary)
        response = api_client.post(
            "/api/schedules/slot",
            json={
                "day": 0,
                "hour": 23,
                "target_type": "instance",
                "target_id": "test",
            },
        )
        assert response.status_code == 200

    def test_clear_slot_accessible(self, api_client):
        """Clear slot endpoint should be accessible."""
        response = api_client.delete("/api/schedules/slot?day=0&hour=9")
        assert response.status_code == 200

    def test_bulk_slots_accessible(self, api_client):
        """Bulk slots endpoint should be accessible."""
        response = api_client.post(
            "/api/schedules/slots/bulk",
            json={
                "slots": [
                    {"day": 0, "hour": 9, "target_type": "instance", "target_id": "inst1"},
                ]
            },
        )
        assert response.status_code == 200

    def test_clear_all_accessible(self, api_client):
        """Clear all slots endpoint should be accessible."""
        response = api_client.post("/api/schedules/clear")
        assert response.status_code == 200

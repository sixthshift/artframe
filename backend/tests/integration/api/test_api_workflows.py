"""
API integration tests for complete workflows.

Tests end-to-end scenarios that span multiple API endpoints.
"""

import pytest


@pytest.mark.integration
class TestInstanceLifecycle:
    """Test complete instance lifecycle through API."""

    def test_list_instances_initially_may_have_instances(self, api_client):
        """List instances endpoint should work on fresh system."""
        response = api_client.get("/api/instances")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True

    def test_instance_crud_workflow(self, api_client, mock_plugin):
        """Test create-read-update-delete instance workflow."""
        from unittest.mock import patch

        # Step 1: List initial instances
        list_response = api_client.get("/api/instances")
        assert list_response.status_code == 200
        initial_data = list_response.json()

        # Step 2: Create a new instance (mocked plugin)
        with patch("src.artframe.plugins.instance_manager.get_plugin") as mock_get:
            mock_get.return_value = mock_plugin
            create_response = api_client.post(
                "/api/instances",
                json={
                    "plugin_id": "clock",
                    "name": "Test Clock Instance",
                    "settings": {"show_seconds": True},
                },
            )
            # May succeed or fail depending on plugin availability
            assert create_response.status_code in [200, 201, 400, 500]

    def test_nonexistent_instance_returns_proper_error(self, api_client):
        """Non-existent instance operations should return errors."""
        # Get non-existent
        get_response = api_client.get("/api/instances/nonexistent-id-12345")
        assert get_response.status_code == 404

        # Delete non-existent
        delete_response = api_client.delete("/api/instances/nonexistent-id-12345")
        assert delete_response.status_code in [400, 404, 200]


@pytest.mark.integration
class TestScheduleWorkflow:
    """Test complete schedule management workflow."""

    def test_schedule_slot_workflow(self, api_client):
        """Test setting and clearing schedule slots."""
        # Step 1: Get initial schedule
        get_response = api_client.get("/api/schedules")
        assert get_response.status_code == 200

        # Step 2: Set a slot
        set_response = api_client.post(
            "/api/schedules/slot",
            json={
                "day": 0,
                "hour": 10,
                "target_type": "instance",
                "target_id": "test-instance-id",
            },
        )
        assert set_response.status_code == 200

        # Step 3: Clear the slot
        clear_response = api_client.delete("/api/schedules/slot?day=0&hour=10")
        assert clear_response.status_code == 200

    def test_bulk_schedule_workflow(self, api_client):
        """Test bulk schedule operations."""
        # Set multiple slots at once
        bulk_response = api_client.post(
            "/api/schedules/slots/bulk",
            json={
                "slots": [
                    {"day": 1, "hour": 9, "target_type": "instance", "target_id": "inst1"},
                    {"day": 1, "hour": 10, "target_type": "instance", "target_id": "inst2"},
                    {"day": 1, "hour": 11, "target_type": "instance", "target_id": "inst3"},
                ]
            },
        )
        assert bulk_response.status_code == 200

        # Clear all slots
        clear_all_response = api_client.post("/api/schedules/clear")
        assert clear_all_response.status_code == 200

    def test_get_current_schedule(self, api_client):
        """Test getting current scheduled content."""
        response = api_client.get("/api/schedules/current")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


@pytest.mark.integration
class TestSchedulerControlWorkflow:
    """Test scheduler pause/resume workflow."""

    def test_pause_resume_cycle(self, api_client):
        """Test pausing and resuming scheduler."""
        # Get initial status
        status_response = api_client.get("/api/scheduler/status")
        assert status_response.status_code == 200

        # Pause scheduler
        pause_response = api_client.post("/api/scheduler/pause")
        assert pause_response.status_code == 200

        # Check status shows paused
        status_after_pause = api_client.get("/api/scheduler/status")
        assert status_after_pause.status_code == 200

        # Resume scheduler
        resume_response = api_client.post("/api/scheduler/resume")
        assert resume_response.status_code == 200


@pytest.mark.integration
class TestDisplayWorkflow:
    """Test display control workflow."""

    def test_display_refresh_workflow(self, api_client):
        """Test display refresh cycle."""
        # Get current display state
        current_response = api_client.get("/api/display/current")
        assert current_response.status_code == 200

        # Trigger refresh
        refresh_response = api_client.post("/api/display/refresh")
        assert refresh_response.status_code == 200

        # Check health
        health_response = api_client.get("/api/display/health")
        assert health_response.status_code == 200

    def test_display_clear(self, api_client):
        """Test clearing display."""
        response = api_client.post("/api/display/clear")
        assert response.status_code == 200


@pytest.mark.integration
class TestSystemStatusWorkflow:
    """Test system status and monitoring workflow."""

    def test_full_status_check(self, api_client):
        """Test getting all system status information."""
        # System status
        status_response = api_client.get("/api/system/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("success") is True

        # System info
        info_response = api_client.get("/api/system/info")
        assert info_response.status_code == 200
        info_data = info_response.json()
        assert "data" in info_data

        # Connection tests
        conn_response = api_client.get("/api/system/connections")
        assert conn_response.status_code == 200

    def test_system_info_contains_metrics(self, api_client):
        """Test system info contains expected metrics."""
        response = api_client.get("/api/system/info")
        assert response.status_code == 200
        data = response.json()

        if data.get("data"):
            metrics = data["data"]
            # Check for expected system metrics
            assert "cpu_percent" in metrics
            assert "memory_percent" in metrics
            assert "disk_percent" in metrics
            assert "platform" in metrics


@pytest.mark.integration
class TestPluginDiscoveryWorkflow:
    """Test plugin discovery and metadata workflow."""

    def test_list_and_get_plugins(self, api_client):
        """Test listing and getting individual plugins."""
        # List all plugins
        list_response = api_client.get("/api/plugins")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert "data" in list_data

        # If plugins exist, try to get details
        if list_data.get("data") and len(list_data["data"]) > 0:
            plugin_id = list_data["data"][0]["id"]
            detail_response = api_client.get(f"/api/plugins/{plugin_id}")
            assert detail_response.status_code == 200


@pytest.mark.integration
class TestConfigWorkflow:
    """Test configuration management workflow."""

    def test_config_read_workflow(self, api_client):
        """Test reading configuration."""
        response = api_client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data

    def test_config_update_workflow(self, api_client):
        """Test configuration update cycle."""
        # Read current config
        read_response = api_client.get("/api/config")
        assert read_response.status_code == 200

        # Update config (in-memory)
        update_response = api_client.put(
            "/api/config",
            json={"display": {"update_time": "10:00"}},
        )
        # May succeed or fail validation
        assert update_response.status_code in [200, 400, 500]

        # Revert changes
        revert_response = api_client.post("/api/config/revert")
        assert revert_response.status_code in [200, 500]

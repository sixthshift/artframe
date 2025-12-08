"""
Unit tests for ArtframeController.

Tests cover initialization, status reporting, and component orchestration.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestControllerInitialization:
    """Tests for ArtframeController initialization."""

    @patch("src.artframe.controller.ConfigManager")
    @patch("src.artframe.controller.StorageManager")
    @patch("src.artframe.controller.DisplayController")
    @patch("src.artframe.controller.InstanceManager")
    @patch("src.artframe.controller.ScheduleManager")
    @patch("src.artframe.controller.ContentOrchestrator")
    @patch("src.artframe.controller.Logger")
    def test_initialization_creates_components(
        self,
        mock_logger,
        mock_orchestrator,
        mock_schedule_manager,
        mock_instance_manager,
        mock_display_controller,
        mock_storage_manager,
        mock_config_manager,
    ):
        """Controller initialization should create all required components."""
        from src.artframe.controller import ArtframeController

        # Setup config manager mock
        config_instance = MagicMock()
        config_instance.get_data_dir.return_value = Path("/tmp/test_data")
        config_instance.get_cache_dir.return_value = Path("/tmp/test_cache")
        config_instance.get_timezone.return_value = "UTC"
        config_instance.get_display_config.return_value = {"driver": "mock", "config": {}}
        config_instance.get_display_dimensions.return_value = (800, 480)
        mock_config_manager.return_value = config_instance

        controller = ArtframeController()

        # Verify components were created
        assert controller.config_manager is not None
        assert controller.storage_manager is not None
        assert controller.display_controller is not None
        assert controller.instance_manager is not None
        assert controller.schedule_manager is not None
        assert controller.orchestrator is not None

    @patch("src.artframe.controller.ConfigManager")
    @patch("src.artframe.controller.StorageManager")
    @patch("src.artframe.controller.DisplayController")
    @patch("src.artframe.controller.InstanceManager")
    @patch("src.artframe.controller.ScheduleManager")
    @patch("src.artframe.controller.ContentOrchestrator")
    @patch("src.artframe.controller.Logger")
    def test_initialization_sets_running_false(
        self,
        mock_logger,
        mock_orchestrator,
        mock_schedule_manager,
        mock_instance_manager,
        mock_display_controller,
        mock_storage_manager,
        mock_config_manager,
    ):
        """Controller should start with running=False."""
        from src.artframe.controller import ArtframeController

        # Setup config manager mock
        config_instance = MagicMock()
        config_instance.get_data_dir.return_value = Path("/tmp/test_data")
        config_instance.get_cache_dir.return_value = Path("/tmp/test_cache")
        config_instance.get_timezone.return_value = "UTC"
        config_instance.get_display_config.return_value = {"driver": "mock", "config": {}}
        config_instance.get_display_dimensions.return_value = (800, 480)
        mock_config_manager.return_value = config_instance

        controller = ArtframeController()

        assert controller.running is False
        assert controller.last_update is None


class TestControllerStatus:
    """Tests for controller status methods."""

    @pytest.fixture
    def mock_controller(self):
        """Create a controller with mocked dependencies."""
        with (
            patch("src.artframe.controller.ConfigManager") as mock_config,
            patch("src.artframe.controller.StorageManager") as mock_storage,
            patch("src.artframe.controller.DisplayController") as mock_display,
            patch("src.artframe.controller.InstanceManager") as mock_instance,
            patch("src.artframe.controller.ScheduleManager") as mock_schedule,
            patch("src.artframe.controller.ContentOrchestrator") as mock_orchestrator,
            patch("src.artframe.controller.Logger"),
        ):
            from src.artframe.controller import ArtframeController

            # Setup config manager mock
            config_instance = MagicMock()
            config_instance.get_data_dir.return_value = Path("/tmp/test_data")
            config_instance.get_cache_dir.return_value = Path("/tmp/test_cache")
            config_instance.get_timezone.return_value = "UTC"
            config_instance.get_display_config.return_value = {"driver": "mock", "config": {}}
            config_instance.get_display_dimensions.return_value = (800, 480)
            mock_config.return_value = config_instance

            # Setup display controller mock
            display_instance = MagicMock()
            display_state = MagicMock()
            display_state.current_image_id = "test_img_123"
            display_state.last_refresh = datetime(2024, 1, 1, 12, 0, 0)
            display_instance.get_state.return_value = display_state
            mock_display.return_value = display_instance

            # Setup orchestrator mock
            orchestrator_instance = MagicMock()
            orchestrator_instance.get_current_status.return_value = {"status": "idle"}
            orchestrator_instance.get_next_update_time.return_value = datetime(2024, 1, 1, 13, 0, 0)
            mock_orchestrator.return_value = orchestrator_instance

            # Setup storage mock with proper storage_dir
            storage_instance = MagicMock()
            storage_dir_mock = MagicMock()
            storage_dir_mock.exists.return_value = True
            storage_instance.storage_dir = storage_dir_mock
            mock_storage.return_value = storage_instance

            controller = ArtframeController()
            yield controller

    def test_get_status_returns_dict(self, mock_controller):
        """get_status should return a dictionary."""
        status = mock_controller.get_status()
        assert isinstance(status, dict)

    def test_get_status_contains_running_state(self, mock_controller):
        """get_status should include running state."""
        status = mock_controller.get_status()
        assert "running" in status
        assert status["running"] is False

    def test_get_status_contains_last_update(self, mock_controller):
        """get_status should include last_update."""
        status = mock_controller.get_status()
        assert "last_update" in status

    def test_get_status_contains_next_scheduled(self, mock_controller):
        """get_status should include next_scheduled time."""
        status = mock_controller.get_status()
        assert "next_scheduled" in status

    def test_get_status_contains_orchestrator_status(self, mock_controller):
        """get_status should include orchestrator status."""
        status = mock_controller.get_status()
        assert "orchestrator" in status

    def test_get_status_contains_display_state(self, mock_controller):
        """get_status should include display state."""
        status = mock_controller.get_status()
        assert "display_state" in status
        assert "current_image_id" in status["display_state"]
        assert "last_refresh" in status["display_state"]

    def test_test_connections_returns_dict(self, mock_controller):
        """test_connections should return a dictionary."""
        connections = mock_controller.test_connections()
        assert isinstance(connections, dict)

    def test_test_connections_checks_display(self, mock_controller):
        """test_connections should check display status."""
        connections = mock_controller.test_connections()
        assert "display" in connections
        assert connections["display"] is True

    def test_test_connections_checks_storage(self, mock_controller):
        """test_connections should check storage status."""
        connections = mock_controller.test_connections()
        assert "storage" in connections


class TestControllerOperations:
    """Tests for controller operations."""

    @pytest.fixture
    def mock_controller(self):
        """Create a controller with mocked dependencies."""
        with (
            patch("src.artframe.controller.ConfigManager") as mock_config,
            patch("src.artframe.controller.StorageManager"),
            patch("src.artframe.controller.DisplayController") as mock_display,
            patch("src.artframe.controller.InstanceManager"),
            patch("src.artframe.controller.ScheduleManager"),
            patch("src.artframe.controller.ContentOrchestrator") as mock_orchestrator,
            patch("src.artframe.controller.Logger"),
        ):
            from src.artframe.controller import ArtframeController

            # Setup config manager mock
            config_instance = MagicMock()
            config_instance.get_data_dir.return_value = Path("/tmp/test_data")
            config_instance.get_cache_dir.return_value = Path("/tmp/test_cache")
            config_instance.get_timezone.return_value = "UTC"
            config_instance.get_display_config.return_value = {"driver": "mock", "config": {}}
            config_instance.get_display_dimensions.return_value = (800, 480)
            mock_config.return_value = config_instance

            # Setup display controller mock
            display_instance = MagicMock()
            display_instance.initialize.return_value = None
            mock_display.return_value = display_instance

            # Setup orchestrator mock
            orchestrator_instance = MagicMock()
            orchestrator_instance.force_refresh.return_value = True
            orchestrator_instance.stop.return_value = None
            mock_orchestrator.return_value = orchestrator_instance

            controller = ArtframeController()
            yield controller

    def test_manual_refresh_returns_bool(self, mock_controller):
        """manual_refresh should return a boolean."""
        result = mock_controller.manual_refresh()
        assert isinstance(result, bool)

    def test_manual_refresh_success_updates_last_update(self, mock_controller):
        """Successful refresh should update last_update timestamp."""
        mock_controller.orchestrator.force_refresh.return_value = True
        result = mock_controller.manual_refresh()
        assert result is True
        assert mock_controller.last_update is not None

    def test_manual_refresh_failure_returns_false(self, mock_controller):
        """Failed refresh should return False."""
        mock_controller.orchestrator.force_refresh.return_value = False
        result = mock_controller.manual_refresh()
        assert result is False

    def test_manual_refresh_exception_returns_false(self, mock_controller):
        """Exception during refresh should return False."""
        mock_controller.orchestrator.force_refresh.side_effect = Exception("Test error")
        result = mock_controller.manual_refresh()
        assert result is False

    def test_stop_sets_running_false(self, mock_controller):
        """stop() should set running to False."""
        mock_controller.running = True
        mock_controller.stop()
        assert mock_controller.running is False

    def test_stop_calls_orchestrator_stop(self, mock_controller):
        """stop() should call orchestrator.stop()."""
        mock_controller.stop()
        mock_controller.orchestrator.stop.assert_called_once()

    def test_initialize_initializes_display(self, mock_controller):
        """initialize() should initialize the display controller."""
        mock_controller.initialize()
        mock_controller.display_controller.initialize.assert_called_once()

    def test_initialize_exception_raises(self, mock_controller):
        """initialize() should raise on display initialization failure."""
        mock_controller.display_controller.initialize.side_effect = Exception("Display error")
        with pytest.raises(Exception, match="Display error"):
            mock_controller.initialize()


class TestDeviceConfig:
    """Tests for device configuration."""

    @patch("src.artframe.controller.ConfigManager")
    @patch("src.artframe.controller.StorageManager")
    @patch("src.artframe.controller.DisplayController")
    @patch("src.artframe.controller.InstanceManager")
    @patch("src.artframe.controller.ScheduleManager")
    @patch("src.artframe.controller.ContentOrchestrator")
    @patch("src.artframe.controller.Logger")
    def test_device_config_has_required_fields(
        self,
        mock_logger,
        mock_orchestrator,
        mock_schedule_manager,
        mock_instance_manager,
        mock_display_controller,
        mock_storage_manager,
        mock_config_manager,
    ):
        """Device config should have width, height, rotation, color_mode, timezone."""
        from src.artframe.controller import ArtframeController

        # Setup config manager mock
        config_instance = MagicMock()
        config_instance.get_data_dir.return_value = Path("/tmp/test_data")
        config_instance.get_cache_dir.return_value = Path("/tmp/test_cache")
        config_instance.get_timezone.return_value = "UTC"
        config_instance.get_display_config.return_value = {
            "driver": "mock",
            "config": {"rotation": 90},
        }
        config_instance.get_display_dimensions.return_value = (800, 480)
        mock_config_manager.return_value = config_instance

        controller = ArtframeController()
        device_config = controller._get_device_config()

        assert "width" in device_config
        assert "height" in device_config
        assert "rotation" in device_config
        assert "color_mode" in device_config
        assert "timezone" in device_config

    @patch("src.artframe.controller.ConfigManager")
    @patch("src.artframe.controller.StorageManager")
    @patch("src.artframe.controller.DisplayController")
    @patch("src.artframe.controller.InstanceManager")
    @patch("src.artframe.controller.ScheduleManager")
    @patch("src.artframe.controller.ContentOrchestrator")
    @patch("src.artframe.controller.Logger")
    def test_device_config_values_from_config(
        self,
        mock_logger,
        mock_orchestrator,
        mock_schedule_manager,
        mock_instance_manager,
        mock_display_controller,
        mock_storage_manager,
        mock_config_manager,
    ):
        """Device config values should come from ConfigManager."""
        from src.artframe.controller import ArtframeController

        # Setup config manager mock
        config_instance = MagicMock()
        config_instance.get_data_dir.return_value = Path("/tmp/test_data")
        config_instance.get_cache_dir.return_value = Path("/tmp/test_cache")
        config_instance.get_timezone.return_value = "Australia/Sydney"
        config_instance.get_display_config.return_value = {
            "driver": "waveshare_7in3f",
            "config": {"rotation": 180},
        }
        config_instance.get_display_dimensions.return_value = (800, 480)
        mock_config_manager.return_value = config_instance

        controller = ArtframeController()
        device_config = controller._get_device_config()

        assert device_config["width"] == 800
        assert device_config["height"] == 480
        assert device_config["rotation"] == 180
        assert device_config["timezone"] == "Australia/Sydney"

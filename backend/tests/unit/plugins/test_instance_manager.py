"""
Unit tests for InstanceManager.

Tests cover:
- Instance CRUD operations
- Settings validation
- Instance persistence
- Enable/disable lifecycle
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.artframe.models import PluginInstance
from src.artframe.plugins.instance_manager import InstanceManager


@pytest.fixture
def mock_get_plugin():
    """Mock the get_plugin function."""
    mock_plugin = MagicMock()
    mock_plugin.validate_settings.return_value = (True, "")
    mock_plugin.on_enable.return_value = None
    mock_plugin.on_disable.return_value = None
    mock_plugin.on_settings_change.return_value = None
    mock_plugin.generate_image.return_value = MagicMock()

    with patch("src.artframe.plugins.instance_manager.get_plugin") as mock:
        mock.return_value = mock_plugin
        yield mock, mock_plugin


class TestInstanceManagerInitialization:
    """Tests for InstanceManager initialization."""

    def test_creates_storage_directory(self, temp_dir: Path):
        """Should create storage directory if it doesn't exist."""
        storage_path = temp_dir / "instances"
        manager = InstanceManager(storage_dir=storage_path)

        assert storage_path.exists()

    def test_initializes_empty_instances(self, temp_dir: Path):
        """Should initialize with no instances."""
        manager = InstanceManager(storage_dir=temp_dir)

        assert manager.get_instance_count() == 0

    def test_loads_existing_instances(self, temp_dir: Path, mock_get_plugin):
        """Should load existing instances from storage."""
        # Create first manager and add instance
        manager1 = InstanceManager(storage_dir=temp_dir)
        manager1.create_instance("clock", "Test Clock", {"key": "value"})

        # Create second manager - should load existing instance
        manager2 = InstanceManager(storage_dir=temp_dir)

        assert manager2.get_instance_count() == 1


class TestCreateInstance:
    """Tests for instance creation."""

    def test_create_instance_success(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should successfully create a new instance."""
        result = instance_manager.create_instance(
            plugin_id="clock", name="My Clock", settings={"format": "24h"}
        )

        assert result is not None
        assert result.plugin_id == "clock"
        assert result.name == "My Clock"
        assert result.settings == {"format": "24h"}
        assert result.enabled is True

    def test_create_instance_generates_uuid(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should generate a UUID for new instance."""
        result = instance_manager.create_instance("clock", "Test", {})

        assert result is not None
        assert len(result.id) == 36  # UUID format

    def test_create_instance_calls_on_enable(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should call plugin's on_enable hook."""
        mock, mock_plugin = mock_get_plugin
        settings = {"key": "value"}

        instance_manager.create_instance("clock", "Test", settings)

        mock_plugin.on_enable.assert_called_once_with(settings)

    def test_create_instance_plugin_not_found(self, instance_manager: InstanceManager):
        """Should return None if plugin doesn't exist."""
        with patch("src.artframe.plugins.instance_manager.get_plugin") as mock:
            mock.return_value = None

            result = instance_manager.create_instance("nonexistent", "Test", {})

            assert result is None

    def test_create_instance_invalid_settings(self, instance_manager: InstanceManager):
        """Should return None if settings are invalid."""
        mock_plugin = MagicMock()
        mock_plugin.validate_settings.return_value = (False, "Invalid settings")

        with patch("src.artframe.plugins.instance_manager.get_plugin") as mock:
            mock.return_value = mock_plugin

            result = instance_manager.create_instance("clock", "Test", {"bad": "settings"})

            assert result is None


class TestGetInstance:
    """Tests for instance retrieval."""

    def test_get_instance_success(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should retrieve existing instance by ID."""
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        result = instance_manager.get_instance(created.id)

        assert result is not None
        assert result.id == created.id

    def test_get_instance_not_found(self, instance_manager: InstanceManager):
        """Should return None for non-existent ID."""
        result = instance_manager.get_instance("nonexistent-id")

        assert result is None


class TestListInstances:
    """Tests for listing instances."""

    def test_list_instances_empty(self, instance_manager: InstanceManager):
        """Should return empty list when no instances."""
        result = instance_manager.list_instances()

        assert result == []

    def test_list_instances_returns_all(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return all instances."""
        instance_manager.create_instance("clock", "Clock 1", {})
        instance_manager.create_instance("clock", "Clock 2", {})

        result = instance_manager.list_instances()

        assert len(result) == 2

    def test_list_instances_filter_by_plugin(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should filter by plugin ID."""
        instance_manager.create_instance("clock", "Clock", {})
        instance_manager.create_instance("weather", "Weather", {})

        result = instance_manager.list_instances(plugin_id="clock")

        assert len(result) == 1
        assert result[0].plugin_id == "clock"


class TestUpdateInstance:
    """Tests for instance updates."""

    def test_update_instance_name(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should update instance name."""
        created = instance_manager.create_instance("clock", "Old Name", {})
        assert created is not None

        result = instance_manager.update_instance(created.id, name="New Name")

        assert result is True
        updated = instance_manager.get_instance(created.id)
        assert updated is not None
        assert updated.name == "New Name"

    def test_update_instance_settings(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should update instance settings."""
        mock, mock_plugin = mock_get_plugin
        created = instance_manager.create_instance("clock", "Test", {"old": "value"})
        assert created is not None

        result = instance_manager.update_instance(created.id, settings={"new": "value"})

        assert result is True
        updated = instance_manager.get_instance(created.id)
        assert updated is not None
        assert updated.settings == {"new": "value"}

    def test_update_instance_calls_settings_change_hook(
        self, instance_manager: InstanceManager, mock_get_plugin
    ):
        """Should call plugin's on_settings_change hook."""
        mock, mock_plugin = mock_get_plugin
        created = instance_manager.create_instance("clock", "Test", {"old": "value"})
        assert created is not None

        instance_manager.update_instance(created.id, settings={"new": "value"})

        mock_plugin.on_settings_change.assert_called_once()

    def test_update_instance_not_found(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return False for non-existent instance."""
        result = instance_manager.update_instance("nonexistent", name="New")

        assert result is False

    def test_update_instance_invalid_settings(self, instance_manager: InstanceManager):
        """Should return False for invalid settings."""
        mock_plugin = MagicMock()
        mock_plugin.validate_settings.side_effect = [
            (True, ""),  # For creation
            (False, "Invalid"),  # For update
        ]
        mock_plugin.on_enable.return_value = None

        with patch("src.artframe.plugins.instance_manager.get_plugin") as mock:
            mock.return_value = mock_plugin

            created = instance_manager.create_instance("clock", "Test", {})
            assert created is not None

            result = instance_manager.update_instance(created.id, settings={"bad": "settings"})

            assert result is False


class TestDeleteInstance:
    """Tests for instance deletion."""

    def test_delete_instance_success(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should successfully delete instance."""
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        result = instance_manager.delete_instance(created.id)

        assert result is True
        assert instance_manager.get_instance(created.id) is None

    def test_delete_instance_calls_on_disable(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should call plugin's on_disable hook."""
        mock, mock_plugin = mock_get_plugin
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        instance_manager.delete_instance(created.id)

        mock_plugin.on_disable.assert_called()

    def test_delete_instance_not_found(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return False for non-existent instance."""
        result = instance_manager.delete_instance("nonexistent")

        assert result is False


class TestEnableDisableInstance:
    """Tests for enable/disable operations."""

    def test_enable_instance_success(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should enable a disabled instance."""
        mock, mock_plugin = mock_get_plugin
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None
        instance_manager.disable_instance(created.id)

        result = instance_manager.enable_instance(created.id)

        assert result is True
        updated = instance_manager.get_instance(created.id)
        assert updated is not None
        assert updated.enabled is True

    def test_enable_instance_calls_on_enable(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should call plugin's on_enable hook."""
        mock, mock_plugin = mock_get_plugin
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None
        instance_manager.disable_instance(created.id)
        mock_plugin.on_enable.reset_mock()

        instance_manager.enable_instance(created.id)

        mock_plugin.on_enable.assert_called_once()

    def test_enable_already_enabled(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return True for already enabled instance."""
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        result = instance_manager.enable_instance(created.id)

        assert result is True

    def test_disable_instance_success(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should disable an enabled instance."""
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        result = instance_manager.disable_instance(created.id)

        assert result is True
        updated = instance_manager.get_instance(created.id)
        assert updated is not None
        assert updated.enabled is False

    def test_disable_instance_calls_on_disable(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should call plugin's on_disable hook."""
        mock, mock_plugin = mock_get_plugin
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        instance_manager.disable_instance(created.id)

        mock_plugin.on_disable.assert_called()

    def test_disable_already_disabled(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return True for already disabled instance."""
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None
        instance_manager.disable_instance(created.id)

        result = instance_manager.disable_instance(created.id)

        assert result is True


class TestTestInstance:
    """Tests for instance testing."""

    def test_test_instance_success(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return success for valid instance."""
        created = instance_manager.create_instance("clock", "Test", {})
        assert created is not None

        success, error = instance_manager.test_instance(
            created.id, {"width": 800, "height": 480}
        )

        assert success is True
        assert error is None

    def test_test_instance_not_found(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return error for non-existent instance."""
        success, error = instance_manager.test_instance(
            "nonexistent", {"width": 800, "height": 480}
        )

        assert success is False
        assert "not found" in error.lower()


class TestGetEnabledInstances:
    """Tests for getting enabled instances."""

    def test_get_enabled_instances(self, instance_manager: InstanceManager, mock_get_plugin):
        """Should return only enabled instances."""
        inst1 = instance_manager.create_instance("clock", "Clock 1", {})
        inst2 = instance_manager.create_instance("clock", "Clock 2", {})
        assert inst1 and inst2
        instance_manager.disable_instance(inst2.id)

        result = instance_manager.get_enabled_instances()

        assert len(result) == 1
        assert result[0].id == inst1.id

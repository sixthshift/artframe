"""
Component integration tests for storage and plugin systems.

Tests real interactions between storage, plugins, and instance management.
"""

import tempfile
from pathlib import Path

import pytest
from PIL import Image


@pytest.mark.integration
class TestStoragePluginIntegration:
    """Tests for storage and plugin system integration."""

    @pytest.fixture
    def integration_temp_dir(self):
        """Create a temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_storage_manager_creates_directories(self, integration_temp_dir):
        """StorageManager should create required directory structure."""
        from src.artframe.storage.manager import StorageManager

        storage_dir = integration_temp_dir / "storage"
        manager = StorageManager(storage_dir=storage_dir)

        # Verify directories were created
        assert storage_dir.exists()
        assert (storage_dir / "metadata").exists()

    def test_storage_manager_photo_persistence(self, integration_temp_dir):
        """StorageManager should persist photos across instances."""
        from src.artframe.storage.manager import StorageManager
        from src.artframe.models import Photo
        from datetime import datetime

        storage_dir = integration_temp_dir / "storage"

        # Create first instance and store photo
        manager1 = StorageManager(storage_dir=storage_dir)

        # Create a test image
        img_path = integration_temp_dir / "test_photo.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img_path)

        photo = Photo(
            id="integration_test_photo",
            source_url="http://example.com/photo.jpg",
            retrieved_at=datetime.now(),
            original_path=img_path,
            metadata={"test": True},
        )
        manager1.store_photo(photo)

        # Create second instance and verify persistence
        manager2 = StorageManager(storage_dir=storage_dir)
        retrieved = manager2.get_photo("integration_test_photo")

        assert retrieved is not None
        assert retrieved.id == "integration_test_photo"
        assert retrieved.metadata.get("test") is True


@pytest.mark.integration
class TestInstanceManagerIntegration:
    """Tests for instance manager with real storage."""

    @pytest.fixture
    def integration_temp_dir(self):
        """Create a temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_instance_manager_creates_storage(self, integration_temp_dir):
        """InstanceManager should create storage directory."""
        from src.artframe.plugins.instance_manager import InstanceManager

        storage_dir = integration_temp_dir / "data"
        manager = InstanceManager(storage_dir=storage_dir, timezone="UTC")

        # Should have created storage directory
        assert storage_dir.exists()
        # Should have instances file path configured
        assert manager.instances_file.parent == storage_dir

    def test_instance_manager_persistence(self, integration_temp_dir):
        """InstanceManager should persist instances across restarts."""
        from src.artframe.plugins.instance_manager import InstanceManager
        from unittest.mock import MagicMock

        # Create mock plugin
        mock_plugin = MagicMock()
        mock_plugin.validate_settings.return_value = (True, "")
        mock_plugin.get_settings_schema.return_value = {"sections": []}

        # Create first manager instance and create an instance
        manager1 = InstanceManager(storage_dir=integration_temp_dir, timezone="UTC")

        # Manually add an instance to simulate creation
        from src.artframe.models import PluginInstance
        from datetime import datetime

        instance = PluginInstance(
            id="test_persistence_instance",
            plugin_id="test_plugin",
            name="Test Instance",
            settings={},
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        manager1._instances[instance.id] = instance
        manager1._save_instances()

        # Create second manager instance and verify persistence
        manager2 = InstanceManager(storage_dir=integration_temp_dir, timezone="UTC")
        retrieved = manager2.get_instance("test_persistence_instance")

        assert retrieved is not None
        assert retrieved.name == "Test Instance"
        assert retrieved.plugin_id == "test_plugin"


@pytest.mark.integration
class TestScheduleManagerIntegration:
    """Tests for schedule manager with real storage."""

    @pytest.fixture
    def integration_temp_dir(self):
        """Create a temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_schedule_manager_persistence(self, integration_temp_dir):
        """ScheduleManager should persist schedules across restarts."""
        from src.artframe.scheduling.schedule_manager import ScheduleManager

        # Create first manager and set slots
        manager1 = ScheduleManager(storage_dir=integration_temp_dir, timezone="UTC")
        manager1.set_slot(0, 9, "instance", "morning_instance")
        manager1.set_slot(0, 17, "instance", "evening_instance")

        # Create second manager and verify persistence
        manager2 = ScheduleManager(storage_dir=integration_temp_dir, timezone="UTC")
        slots = manager2.get_all_slots()

        # Should have persisted the slots
        assert len(slots) == 2

    def test_schedule_manager_bulk_operations(self, integration_temp_dir):
        """ScheduleManager bulk operations should work correctly."""
        from src.artframe.scheduling.schedule_manager import ScheduleManager

        manager = ScheduleManager(storage_dir=integration_temp_dir, timezone="UTC")

        # Set multiple slots
        slots_to_set = [
            (0, 9, "instance", "inst1"),
            (0, 10, "instance", "inst2"),
            (0, 11, "instance", "inst3"),
        ]
        for day, hour, target_type, target_id in slots_to_set:
            manager.set_slot(day, hour, target_type, target_id)

        # Verify all slots exist
        all_slots = manager.get_all_slots()
        assert len(all_slots) == 3

        # Clear all
        manager.clear_all_slots()
        all_slots_after = manager.get_all_slots()
        assert len(all_slots_after) == 0


@pytest.mark.integration
class TestDisplayControllerIntegration:
    """Tests for display controller with mock driver."""

    @pytest.fixture
    def integration_temp_dir(self):
        """Create a temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_display_controller_initialization(self):
        """DisplayController should initialize with mock driver."""
        from src.artframe.display.controller import DisplayController

        config = {"driver": "mock", "config": {"width": 800, "height": 480}}
        controller = DisplayController(config, timezone="UTC")

        # Should be able to get display size
        width, height = controller.get_display_size()
        assert width == 800
        assert height == 480

    def test_display_controller_display_image(self, integration_temp_dir):
        """DisplayController should display images."""
        from src.artframe.display.controller import DisplayController

        config = {"driver": "mock", "config": {"width": 800, "height": 480}}
        controller = DisplayController(config, timezone="UTC")
        controller.initialize()

        # Create test image
        img = Image.new("RGB", (800, 480), color="blue")

        # Display should work without error
        controller.display_image(img)

        # State should be updated with last_refresh time
        state = controller.get_state()
        assert state.last_refresh is not None

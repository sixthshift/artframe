"""
Pytest configuration and fixtures for Artframe tests.

This module provides shared fixtures for testing various components
of the Artframe system including storage, plugins, scheduling, and web API.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, Mock, patch
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from src.artframe.models import (
    ContentSource,
    DisplayState,
    Photo,
    PluginInstance,
    StorageStats,
    StyledImage,
    TimeSlot,
)


# =============================================================================
# Core Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def fixed_datetime() -> datetime:
    """A fixed datetime for deterministic tests."""
    return datetime(2024, 6, 15, 14, 30, 0, tzinfo=ZoneInfo("UTC"))


@pytest.fixture
def utc_tz() -> ZoneInfo:
    """UTC timezone for tests."""
    return ZoneInfo("UTC")


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample system configuration for testing."""
    return {
        "artframe": {
            "display": {
                "driver": "mock",
                "config": {"width": 800, "height": 480, "rotation": 0},
            },
            "storage": {
                "data_dir": "/tmp/test_data",
                "cache_dir": "/tmp/test_cache",
                "cache_max_mb": 500,
                "cache_retention_days": 30,
            },
            "logging": {
                "level": "INFO",
                "dir": "/tmp/test_logs",
                "max_size_mb": 10,
                "backup_count": 5,
            },
            "web": {"host": "127.0.0.1", "port": 8000, "debug": False},
            "scheduler": {"timezone": "UTC"},
        }
    }


@pytest.fixture
def sample_config_sydney() -> dict[str, Any]:
    """Sample system configuration with Sydney timezone."""
    return {
        "artframe": {
            "display": {
                "driver": "mock",
                "config": {"width": 800, "height": 480, "rotation": 0},
            },
            "storage": {
                "data_dir": "/tmp/test_data",
                "cache_dir": "/tmp/test_cache",
            },
            "logging": {"level": "DEBUG"},
            "web": {"host": "0.0.0.0", "port": 8080},
            "scheduler": {"timezone": "Australia/Sydney"},
        }
    }


@pytest.fixture
def test_config_file(temp_dir: Path, sample_config: dict[str, Any]) -> Path:
    """Create a test configuration file."""
    import yaml

    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)

    return config_file


@pytest.fixture
def device_config() -> dict[str, Any]:
    """Device configuration for image generation."""
    return {
        "width": 800,
        "height": 480,
        "rotation": 0,
        "color_mode": "grayscale",
        "timezone": "UTC",
    }


# =============================================================================
# Image Fixtures
# =============================================================================


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample PIL Image for testing."""
    return Image.new("RGB", (100, 100), color="red")


@pytest.fixture
def sample_image_file(temp_dir: Path, sample_image: Image.Image) -> Path:
    """Create a sample image file."""
    img_path = temp_dir / "test_image.jpg"
    sample_image.save(img_path)
    return img_path


@pytest.fixture
def large_sample_image() -> Image.Image:
    """Create a larger sample image matching display dimensions."""
    return Image.new("RGB", (800, 480), color="blue")


# =============================================================================
# Model Fixtures
# =============================================================================


@pytest.fixture
def sample_photo(temp_dir: Path, sample_image: Image.Image) -> Photo:
    """Sample Photo object for testing."""
    img_path = temp_dir / "test_photo.jpg"
    sample_image.save(img_path)

    return Photo(
        id="test_photo_123",
        source_url="http://example.com/photo.jpg",
        retrieved_at=datetime.now(),
        original_path=img_path,
        metadata={
            "original_filename": "photo.jpg",
            "file_created_at": "2024-01-01T12:00:00",
            "device_id": "camera_123",
        },
    )


@pytest.fixture
def sample_styled_image(temp_dir: Path, sample_image: Image.Image) -> StyledImage:
    """Sample StyledImage object for testing."""
    img_path = temp_dir / "test_styled.jpg"
    sample_image.save(img_path)

    return StyledImage(
        original_photo_id="test_photo_123",
        style_name="ghibli",
        styled_path=img_path,
        created_at=datetime.now(),
        metadata={"dimensions": (100, 100), "file_size": 1024},
    )


@pytest.fixture
def sample_plugin_instance(fixed_datetime: datetime) -> PluginInstance:
    """Sample PluginInstance for testing."""
    return PluginInstance(
        id="instance_123",
        plugin_id="clock",
        name="Test Clock",
        settings={"show_seconds": True, "format": "24h"},
        enabled=True,
        created_at=fixed_datetime,
        updated_at=fixed_datetime,
    )


@pytest.fixture
def sample_time_slot() -> TimeSlot:
    """Sample TimeSlot for testing."""
    return TimeSlot(
        day=0,  # Monday
        hour=9,  # 9 AM
        target_type="instance",
        target_id="instance_123",
    )


@pytest.fixture
def sample_display_state(fixed_datetime: datetime) -> DisplayState:
    """Sample DisplayState for testing."""
    return DisplayState(
        current_image_id="img_123",
        last_refresh=fixed_datetime,
        next_scheduled=fixed_datetime,
    )


@pytest.fixture
def sample_storage_stats() -> StorageStats:
    """Sample StorageStats for testing."""
    return StorageStats(
        total_photos=10,
        total_styled_images=5,
        total_size_mb=150.5,
        storage_directory="/tmp/test_storage",
    )


@pytest.fixture
def sample_content_source(sample_plugin_instance: PluginInstance) -> ContentSource:
    """Sample ContentSource for testing."""
    return ContentSource(
        instance=sample_plugin_instance,
        duration_seconds=3600,
        source_type="schedule",
        source_id="0-9",
        source_name="Monday 9 AM",
    )


# =============================================================================
# Storage Fixtures
# =============================================================================


@pytest.fixture
def storage_manager(temp_dir: Path):
    """Create a StorageManager instance for testing."""
    from src.artframe.storage.manager import StorageManager

    return StorageManager(storage_dir=temp_dir / "storage")


# =============================================================================
# Display Fixtures
# =============================================================================


@pytest.fixture
def mock_display_driver():
    """Create a mock display driver."""
    driver = MagicMock()
    driver.get_display_size.return_value = (800, 480)
    driver.display_image.return_value = None
    driver.clear_display.return_value = None
    driver.initialize.return_value = None
    driver.sleep.return_value = None
    driver.wake.return_value = None
    return driver


@pytest.fixture
def display_controller(sample_config: dict[str, Any]):
    """Create a DisplayController with mock driver."""
    from src.artframe.display.controller import DisplayController

    display_config = sample_config["artframe"]["display"]
    return DisplayController(display_config, timezone="UTC")


# =============================================================================
# Plugin Fixtures
# =============================================================================


@pytest.fixture
def mock_plugin():
    """Create a mock plugin for testing."""
    plugin = MagicMock()
    plugin.generate_image.return_value = Image.new("RGB", (800, 480), "white")
    plugin.validate_settings.return_value = (True, "")
    plugin.get_refresh_interval.return_value = 60
    plugin.on_enable.return_value = None
    plugin.on_disable.return_value = None
    return plugin


@pytest.fixture
def instance_manager(temp_dir: Path):
    """Create an InstanceManager for testing."""
    from src.artframe.plugins.instance_manager import InstanceManager

    return InstanceManager(storage_dir=temp_dir / "instances", timezone="UTC")


# =============================================================================
# Schedule Fixtures
# =============================================================================


@pytest.fixture
def schedule_manager(temp_dir: Path):
    """Create a ScheduleManager for testing."""
    from src.artframe.scheduling.schedule_manager import ScheduleManager

    return ScheduleManager(storage_dir=temp_dir / "schedules", timezone="UTC")


@pytest.fixture
def populated_schedule_manager(schedule_manager):
    """ScheduleManager with some pre-configured slots."""
    # Monday 9-17 (work hours)
    for hour in range(9, 17):
        schedule_manager.set_slot(0, hour, "instance", "work_instance")

    # Weekend all day
    for day in [5, 6]:  # Saturday, Sunday
        for hour in range(24):
            schedule_manager.set_slot(day, hour, "instance", "weekend_instance")

    return schedule_manager


# =============================================================================
# Web/API Fixtures
# =============================================================================


@pytest.fixture
def mock_controller(
    temp_dir: Path,
    storage_manager,
    display_controller,
    instance_manager,
    schedule_manager,
):
    """Create a mock ArtframeController for API testing."""
    controller = MagicMock()
    controller.storage_manager = storage_manager
    controller.display_controller = display_controller
    controller.instance_manager = instance_manager
    controller.schedule_manager = schedule_manager
    controller.running = False
    controller.last_update = None
    controller.get_status.return_value = {
        "running": False,
        "last_update": None,
        "next_scheduled": datetime.now().isoformat(),
        "orchestrator": {"status": "idle"},
        "display_state": {"current_image_id": None, "last_refresh": None},
    }
    controller.test_connections.return_value = {"display": True, "storage": True}
    controller.manual_refresh.return_value = True

    # Mock orchestrator for scheduler routes
    orchestrator = MagicMock()
    orchestrator.get_scheduler_status.return_value = {
        "paused": False,
        "next_update": datetime.now().isoformat(),
        "last_update": None,
        "current_time": datetime.now().isoformat(),
        "timezone": "UTC",
        "update_time": "00:00",
    }
    orchestrator.pause.return_value = None
    orchestrator.resume.return_value = None
    controller.orchestrator = orchestrator

    # Mock config_manager for config routes
    config_manager = MagicMock()
    config_manager.config = {
        "display": {"driver": "mock", "update_time": "09:00"},
        "storage": {"data_dir": str(temp_dir / "data")},
    }
    config_manager.update_config.return_value = None
    config_manager.save_to_file.return_value = None
    config_manager.revert_to_file.return_value = None
    controller.config_manager = config_manager

    return controller


@pytest.fixture
def api_client(mock_controller):
    """Create a FastAPI TestClient for API testing."""
    from fastapi.testclient import TestClient

    from src.artframe.web.app import create_app

    # Patch load_plugins to avoid loading actual plugins
    with patch("src.artframe.web.app.load_plugins"):
        # Prevent background scheduler thread from starting
        mock_controller.run_scheduled_loop = lambda: None
        app = create_app(mock_controller)

        # Use TestClient as context manager so lifespan runs
        with TestClient(app) as client:
            yield client


# =============================================================================
# Mock Fixtures for External Services
# =============================================================================


@pytest.fixture
def mock_requests():
    """Mock requests module for testing external API calls."""
    mock = Mock()
    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {"status": "ok"}
    mock.get.return_value.content = b"fake image data"
    mock.post.return_value.status_code = 200
    mock.post.return_value.json.return_value = {"job_id": "test_job_123"}
    return mock


@pytest.fixture
def mock_gpio():
    """Mock RPi.GPIO for testing without hardware."""
    mock = Mock()
    mock.BCM = "BCM"
    mock.OUT = "OUT"
    mock.IN = "IN"
    mock.HIGH = 1
    mock.LOW = 0
    mock.setmode = Mock()
    mock.setup = Mock()
    mock.output = Mock()
    mock.cleanup = Mock()
    return mock


@pytest.fixture
def mock_spi():
    """Mock SPI device for hardware testing."""
    mock = Mock()
    mock.open = Mock()
    mock.close = Mock()
    mock.writebytes = Mock()
    mock.xfer2 = Mock(return_value=[0])
    mock.max_speed_hz = 4000000
    mock.mode = 0
    return mock


# =============================================================================
# Pytest Markers
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "hardware: Tests requiring hardware")
    config.addinivalue_line("markers", "external: Tests requiring external services")

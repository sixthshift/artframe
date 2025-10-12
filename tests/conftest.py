"""
Pytest configuration and fixtures for Artframe tests.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.artframe.models import Photo, StyledImage


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "artframe": {
            "source": {
                "provider": "immich",
                "config": {"server_url": "http://localhost:2283", "api_key": "test_key"},
            },
            "style": {
                "provider": "nanobanana",
                "config": {
                    "api_url": "http://localhost:8080",
                    "api_key": "test_style_key",
                    "styles": ["ghibli", "watercolor"],
                },
            },
            "display": {"driver": "mock", "config": {"width": 600, "height": 448, "rotation": 0}},
            "storage": {"directory": "/tmp/test_cache"},
            "scheduler": {
                "timezone": "America/New_York",
                "default_duration": 3600,
                "refresh_interval": 86400,
            },
            "logging": {
                "level": "INFO",
                "file": "/tmp/test.log",
                "max_size_mb": 10,
                "backup_count": 5,
            },
            "web": {"host": "127.0.0.1", "port": 8000, "debug": False},
        }
    }


@pytest.fixture
def sample_photo(temp_dir):
    """Sample Photo object for testing."""
    # Create a dummy image file
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    img_path = temp_dir / "test_photo.jpg"
    img.save(img_path)

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
def sample_styled_image(temp_dir):
    """Sample StyledImage object for testing."""
    # Create a dummy styled image file
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="blue")
    img_path = temp_dir / "test_styled.jpg"
    img.save(img_path)

    return StyledImage(
        original_photo_id="test_photo_123",
        style_name="ghibli",
        styled_path=img_path,
        created_at=datetime.now(),
        metadata={"dimensions": (100, 100), "file_size": 1024},
    )


@pytest.fixture
def mock_requests():
    """Mock requests module for testing external API calls."""
    mock = Mock()
    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {"status": "ok"}
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
    return mock


@pytest.fixture
def test_config_file(temp_dir, sample_config):
    """Create a test configuration file."""
    import yaml

    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)

    return config_file

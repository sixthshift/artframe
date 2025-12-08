"""
Unit tests for BasePlugin abstract class.

Tests cover:
- Plugin lifecycle methods
- Settings validation
- Asset path resolution
- Refresh interval
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from PIL import Image

from src.artframe.plugins.base_plugin import BasePlugin


class ConcreteTestPlugin(BasePlugin):
    """Concrete implementation of BasePlugin for testing."""

    def __init__(self):
        super().__init__()
        self.generate_called = False
        self.run_active_called = False
        self.on_enable_called = False
        self.on_disable_called = False
        self.settings_change_called = False
        self._test_refresh_interval = 0

    def generate_image(
        self, settings: dict[str, Any], device_config: dict[str, Any]
    ) -> Image.Image:
        self.generate_called = True
        width = device_config.get("width", 800)
        height = device_config.get("height", 480)
        color = settings.get("color", "white")
        return Image.new("RGB", (width, height), color)

    def run_active(
        self,
        display_controller,
        settings: dict[str, Any],
        device_config: dict[str, Any],
        stop_event,
        plugin_info=None,
    ) -> None:
        self.run_active_called = True
        image = self.generate_image(settings, device_config)
        display_controller.display_image(image, plugin_info)
        stop_event.wait()

    def on_enable(self, settings: dict[str, Any]) -> None:
        self.on_enable_called = True

    def on_disable(self, settings: dict[str, Any]) -> None:
        self.on_disable_called = True

    def on_settings_change(
        self, old_settings: dict[str, Any], new_settings: dict[str, Any]
    ) -> None:
        self.settings_change_called = True

    def get_refresh_interval(self, settings: dict[str, Any]) -> int:
        return settings.get("refresh_interval", self._test_refresh_interval)


class ValidatingPlugin(BasePlugin):
    """Plugin with custom settings validation."""

    def generate_image(
        self, settings: dict[str, Any], device_config: dict[str, Any]
    ) -> Image.Image:
        return Image.new("RGB", (100, 100), "white")

    def run_active(self, display_controller, settings, device_config, stop_event, plugin_info=None):
        pass

    def validate_settings(self, settings: dict[str, Any]) -> tuple[bool, str]:
        if not settings.get("required_field"):
            return False, "required_field is required"
        if settings.get("number", 0) < 0:
            return False, "number must be non-negative"
        return True, ""


class TestBasePluginLifecycle:
    """Tests for plugin lifecycle methods."""

    def test_on_enable_called(self):
        """Should call on_enable when plugin is enabled."""
        plugin = ConcreteTestPlugin()
        settings = {"key": "value"}

        plugin.on_enable(settings)

        assert plugin.on_enable_called is True

    def test_on_disable_called(self):
        """Should call on_disable when plugin is disabled."""
        plugin = ConcreteTestPlugin()
        settings = {"key": "value"}

        plugin.on_disable(settings)

        assert plugin.on_disable_called is True

    def test_on_settings_change_called(self):
        """Should call on_settings_change when settings are updated."""
        plugin = ConcreteTestPlugin()
        old_settings = {"key": "old"}
        new_settings = {"key": "new"}

        plugin.on_settings_change(old_settings, new_settings)

        assert plugin.settings_change_called is True


class TestBasePluginImageGeneration:
    """Tests for image generation."""

    def test_generate_image_returns_pil_image(self):
        """Should return a PIL Image."""
        plugin = ConcreteTestPlugin()
        settings = {}
        device_config = {"width": 800, "height": 480}

        result = plugin.generate_image(settings, device_config)

        assert isinstance(result, Image.Image)

    def test_generate_image_uses_device_dimensions(self):
        """Should create image with device dimensions."""
        plugin = ConcreteTestPlugin()
        settings = {}
        device_config = {"width": 640, "height": 480}

        result = plugin.generate_image(settings, device_config)

        assert result.size == (640, 480)

    def test_generate_image_uses_settings(self):
        """Should use settings for image generation."""
        plugin = ConcreteTestPlugin()
        settings = {"color": "red"}
        device_config = {"width": 100, "height": 100}

        result = plugin.generate_image(settings, device_config)

        # Check that the image is red
        pixel = result.getpixel((0, 0))
        assert pixel == (255, 0, 0)


class TestBasePluginSettingsValidation:
    """Tests for settings validation."""

    def test_default_validation_returns_true(self):
        """Default validation should always return True."""
        plugin = ConcreteTestPlugin()

        is_valid, error = plugin.validate_settings({})

        assert is_valid is True
        assert error == ""

    def test_custom_validation_success(self):
        """Custom validation should pass with valid settings."""
        plugin = ValidatingPlugin()
        settings = {"required_field": "present", "number": 5}

        is_valid, error = plugin.validate_settings(settings)

        assert is_valid is True
        assert error == ""

    def test_custom_validation_missing_required(self):
        """Custom validation should fail for missing required field."""
        plugin = ValidatingPlugin()
        settings = {"number": 5}

        is_valid, error = plugin.validate_settings(settings)

        assert is_valid is False
        assert "required_field" in error

    def test_custom_validation_invalid_value(self):
        """Custom validation should fail for invalid value."""
        plugin = ValidatingPlugin()
        settings = {"required_field": "present", "number": -1}

        is_valid, error = plugin.validate_settings(settings)

        assert is_valid is False
        assert "non-negative" in error


class TestBasePluginRefreshInterval:
    """Tests for refresh interval."""

    def test_default_refresh_interval_is_zero(self):
        """Default refresh interval should be 0 (static content)."""
        plugin = ConcreteTestPlugin()
        plugin._test_refresh_interval = 0

        interval = plugin.get_refresh_interval({})

        assert interval == 0

    def test_custom_refresh_interval(self):
        """Should return custom refresh interval from settings."""
        plugin = ConcreteTestPlugin()
        settings = {"refresh_interval": 300}

        interval = plugin.get_refresh_interval(settings)

        assert interval == 300


class TestBasePluginDirectory:
    """Tests for plugin directory resolution."""

    def test_get_plugin_directory(self):
        """Should return plugin directory path."""
        plugin = ConcreteTestPlugin()
        # Set plugin directory manually for testing
        plugin._plugin_dir = Path("/path/to/plugin")

        result = plugin.get_plugin_directory()

        assert result == Path("/path/to/plugin")

    def test_get_asset_path(self):
        """Should return path to plugin asset."""
        plugin = ConcreteTestPlugin()
        plugin._plugin_dir = Path("/path/to/plugin")

        result = plugin.get_asset_path("icon.png")

        assert result == Path("/path/to/plugin/icon.png")


class TestBasePluginRunActive:
    """Tests for run_active method."""

    def test_run_active_generates_and_displays_image(self):
        """Should generate image and display it."""
        plugin = ConcreteTestPlugin()
        mock_display = MagicMock()
        mock_stop_event = MagicMock()
        mock_stop_event.wait.return_value = None  # Immediate return
        mock_stop_event.is_set.return_value = False

        settings = {}
        device_config = {"width": 800, "height": 480}

        plugin.run_active(mock_display, settings, device_config, mock_stop_event)

        assert plugin.run_active_called is True
        assert mock_display.display_image.called


class TestBasePluginRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Should return class name in repr."""
        plugin = ConcreteTestPlugin()

        result = repr(plugin)

        assert "ConcreteTestPlugin" in result

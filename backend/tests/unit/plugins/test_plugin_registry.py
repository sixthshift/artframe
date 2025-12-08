"""
Unit tests for plugin registry.

Tests cover:
- Plugin discovery
- Metadata loading
- Plugin class loading
- Registry operations
"""

import json
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from src.artframe.plugins.base_plugin import BasePlugin
from src.artframe.plugins.plugin_registry import (
    PLUGIN_CLASSES,
    PLUGIN_METADATA,
    discover_plugins,
    get_plugin,
    get_plugin_metadata,
    is_plugin_loaded,
    list_plugin_metadata,
    list_plugins,
    load_plugin_metadata,
    load_plugins,
)


class TestDiscoverPlugins:
    """Tests for plugin discovery."""

    def test_discover_plugins_empty_directory(self, temp_dir: Path):
        """Should return empty dict for empty directory."""
        result = discover_plugins(temp_dir)

        assert result == {}

    def test_discover_plugins_nonexistent_directory(self, temp_dir: Path):
        """Should return empty dict for non-existent directory."""
        result = discover_plugins(temp_dir / "nonexistent")

        assert result == {}

    def test_discover_plugins_finds_valid_plugin(self, temp_dir: Path):
        """Should discover plugin with plugin-info.json."""
        # Create a plugin directory with plugin-info.json
        plugin_dir = temp_dir / "test_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin-info.json").write_text('{"class": "TestPlugin"}')

        result = discover_plugins(temp_dir)

        assert "test_plugin" in result
        assert result["test_plugin"] == plugin_dir

    def test_discover_plugins_ignores_hidden_directories(self, temp_dir: Path):
        """Should ignore directories starting with . or _."""
        # Create hidden directories
        (temp_dir / ".hidden").mkdir()
        (temp_dir / ".hidden" / "plugin-info.json").write_text('{"class": "Hidden"}')

        (temp_dir / "_private").mkdir()
        (temp_dir / "_private" / "plugin-info.json").write_text('{"class": "Private"}')

        # Create valid plugin
        plugin_dir = temp_dir / "valid_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin-info.json").write_text('{"class": "Valid"}')

        result = discover_plugins(temp_dir)

        assert ".hidden" not in result
        assert "_private" not in result
        assert "valid_plugin" in result

    def test_discover_plugins_ignores_directories_without_plugin_info(self, temp_dir: Path):
        """Should ignore directories without plugin-info.json."""
        # Create directory without plugin-info.json
        (temp_dir / "incomplete_plugin").mkdir()

        # Create valid plugin
        plugin_dir = temp_dir / "valid_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin-info.json").write_text('{"class": "Valid"}')

        result = discover_plugins(temp_dir)

        assert "incomplete_plugin" not in result
        assert "valid_plugin" in result


class TestLoadPluginMetadata:
    """Tests for metadata loading."""

    def test_load_valid_metadata(self, temp_dir: Path):
        """Should load valid plugin metadata."""
        plugin_dir = temp_dir / "test_plugin"
        plugin_dir.mkdir()

        metadata = {
            "id": "test_plugin",
            "display_name": "Test Plugin",
            "class": "TestPlugin",
            "description": "A test plugin",
            "author": "Test Author",
            "version": "1.0.0",
        }
        (plugin_dir / "plugin-info.json").write_text(json.dumps(metadata))

        result = load_plugin_metadata(plugin_dir)

        assert result is not None
        assert result.plugin_id == "test_plugin"
        assert result.display_name == "Test Plugin"
        assert result.class_name == "TestPlugin"
        assert result.description == "A test plugin"
        assert result.author == "Test Author"
        assert result.version == "1.0.0"

    def test_load_metadata_with_defaults(self, temp_dir: Path):
        """Should use default values for optional fields."""
        plugin_dir = temp_dir / "minimal_plugin"
        plugin_dir.mkdir()

        # Only required field
        metadata = {"class": "MinimalPlugin"}
        (plugin_dir / "plugin-info.json").write_text(json.dumps(metadata))

        result = load_plugin_metadata(plugin_dir)

        assert result is not None
        assert result.plugin_id == "minimal_plugin"  # From directory name
        assert result.display_name == "Minimal Plugin"  # Auto-generated
        assert result.class_name == "MinimalPlugin"
        assert result.version == "1.0.0"  # Default

    def test_load_metadata_missing_class(self, temp_dir: Path):
        """Should return None if class field is missing."""
        plugin_dir = temp_dir / "no_class_plugin"
        plugin_dir.mkdir()

        # Missing class field
        metadata = {"id": "no_class", "display_name": "No Class"}
        (plugin_dir / "plugin-info.json").write_text(json.dumps(metadata))

        result = load_plugin_metadata(plugin_dir)

        assert result is None

    def test_load_metadata_invalid_json(self, temp_dir: Path):
        """Should return None for invalid JSON."""
        plugin_dir = temp_dir / "invalid_json_plugin"
        plugin_dir.mkdir()

        (plugin_dir / "plugin-info.json").write_text("not valid json {")

        result = load_plugin_metadata(plugin_dir)

        assert result is None

    def test_load_metadata_missing_file(self, temp_dir: Path):
        """Should return None if plugin-info.json doesn't exist."""
        plugin_dir = temp_dir / "no_info_plugin"
        plugin_dir.mkdir()

        result = load_plugin_metadata(plugin_dir)

        assert result is None

    def test_load_metadata_with_settings_schema(self, temp_dir: Path):
        """Should load settings_schema if present."""
        plugin_dir = temp_dir / "schema_plugin"
        plugin_dir.mkdir()

        metadata = {
            "class": "SchemaPlugin",
            "settings_schema": {
                "type": "object",
                "properties": {
                    "api_key": {"type": "string", "title": "API Key"},
                },
            },
        }
        (plugin_dir / "plugin-info.json").write_text(json.dumps(metadata))

        result = load_plugin_metadata(plugin_dir)

        assert result is not None
        assert result.settings_schema is not None
        assert "properties" in result.settings_schema


class TestRegistryOperations:
    """Tests for registry query operations."""

    def test_get_plugin_returns_none_for_unknown(self):
        """Should return None for unknown plugin ID."""
        result = get_plugin("nonexistent_plugin_xyz")

        assert result is None

    def test_get_plugin_metadata_returns_none_for_unknown(self):
        """Should return None for unknown plugin ID."""
        result = get_plugin_metadata("nonexistent_plugin_xyz")

        assert result is None

    def test_is_plugin_loaded_false_for_unknown(self):
        """Should return False for unknown plugin."""
        result = is_plugin_loaded("nonexistent_plugin_xyz")

        assert result is False

    def test_list_plugins_returns_list(self):
        """Should return list of plugin IDs."""
        result = list_plugins()

        assert isinstance(result, list)

    def test_list_plugin_metadata_returns_list(self):
        """Should return list of metadata objects."""
        result = list_plugin_metadata()

        assert isinstance(result, list)


class TestLoadPlugins:
    """Tests for full plugin loading."""

    def test_load_plugins_empty_directory(self, temp_dir: Path):
        """Should return 0 for empty directory."""
        result = load_plugins(temp_dir)

        assert result == 0

    def test_load_plugins_clears_existing_registry(self, temp_dir: Path):
        """Should clear existing registry before loading."""
        # Add something to registry
        PLUGIN_CLASSES["old_plugin"] = None  # type: ignore
        PLUGIN_METADATA["old_plugin"] = None  # type: ignore

        load_plugins(temp_dir)

        assert "old_plugin" not in PLUGIN_CLASSES
        assert "old_plugin" not in PLUGIN_METADATA

    def test_load_plugins_creates_valid_plugin(self, temp_dir: Path):
        """Should successfully load a valid plugin."""
        # Create a complete plugin
        plugin_dir = temp_dir / "simple_plugin"
        plugin_dir.mkdir()

        # Create plugin-info.json
        metadata = {
            "id": "simple_plugin",
            "display_name": "Simple Plugin",
            "class": "SimplePlugin",
        }
        (plugin_dir / "plugin-info.json").write_text(json.dumps(metadata))

        # Create plugin module
        plugin_code = '''
from PIL import Image
from src.artframe.plugins.base_plugin import BasePlugin

class SimplePlugin(BasePlugin):
    def generate_image(self, settings, device_config):
        return Image.new("RGB", (100, 100), "white")

    def run_active(self, display_controller, settings, device_config, stop_event, plugin_info=None):
        pass
'''
        (plugin_dir / "simple_plugin.py").write_text(plugin_code)

        result = load_plugins(temp_dir)

        assert result == 1
        assert "simple_plugin" in PLUGIN_CLASSES
        assert "simple_plugin" in PLUGIN_METADATA

    def test_load_plugins_skips_invalid_plugins(self, temp_dir: Path):
        """Should skip plugins with errors and continue loading others."""
        # Create an invalid plugin (missing module)
        invalid_dir = temp_dir / "invalid_plugin"
        invalid_dir.mkdir()
        (invalid_dir / "plugin-info.json").write_text('{"class": "InvalidPlugin"}')
        # No .py file created

        # Create a valid plugin
        valid_dir = temp_dir / "valid_plugin"
        valid_dir.mkdir()
        (valid_dir / "plugin-info.json").write_text(
            '{"id": "valid_plugin", "class": "ValidPlugin"}'
        )

        plugin_code = '''
from PIL import Image
from src.artframe.plugins.base_plugin import BasePlugin

class ValidPlugin(BasePlugin):
    def generate_image(self, settings, device_config):
        return Image.new("RGB", (100, 100), "white")

    def run_active(self, display_controller, settings, device_config, stop_event, plugin_info=None):
        pass
'''
        (valid_dir / "valid_plugin.py").write_text(plugin_code)

        result = load_plugins(temp_dir)

        # Only valid plugin should be loaded
        assert result == 1
        assert "valid_plugin" in PLUGIN_CLASSES
        assert "invalid_plugin" not in PLUGIN_CLASSES

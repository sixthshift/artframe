"""
Plugin registry for discovering, loading, and managing Artframe plugins.

Inspired by InkyPi's plugin system with automatic discovery.
"""

import json
import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
from dataclasses import dataclass

from .base_plugin import BasePlugin


logger = logging.getLogger(__name__)


# Global plugin registry
PLUGIN_CLASSES: Dict[str, BasePlugin] = {}
PLUGIN_METADATA: Dict[str, "PluginMetadata"] = {}


@dataclass
class PluginMetadata:
    """
    Plugin metadata from plugin-info.json.

    Minimal metadata following InkyPi's approach.
    """

    plugin_id: str  # Unique plugin identifier (e.g., "clock", "immich_photos")
    display_name: str  # Human-readable name (e.g., "Clock", "Immich Photos")
    class_name: str  # Python class name (e.g., "Clock", "ImmichPhotos")
    description: str = ""  # Optional description
    author: str = ""  # Optional author
    version: str = "1.0.0"  # Optional version
    icon: Optional[str] = None  # Optional icon filename


def discover_plugins(plugins_dir: Path) -> Dict[str, Path]:
    """
    Discover all plugins in the plugins directory.

    Scans for directories containing plugin-info.json.

    Args:
        plugins_dir: Path to plugins directory

    Returns:
        Dict mapping plugin_id to plugin directory path

    Example:
        plugins = discover_plugins(Path('src/artframe/plugins/builtin'))
        # Returns: {'clock': Path('.../clock'), 'weather': Path('.../weather')}
    """
    discovered = {}

    if not plugins_dir.exists():
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return discovered

    # Scan for plugin directories
    for item in plugins_dir.iterdir():
        if not item.is_dir():
            continue

        # Skip special directories
        if item.name.startswith("_") or item.name.startswith("."):
            continue

        # Check for plugin-info.json
        plugin_info_path = item / "plugin-info.json"
        if plugin_info_path.exists():
            discovered[item.name] = item
            logger.debug(f"Discovered plugin: {item.name} at {item}")

    logger.info(f"Discovered {len(discovered)} plugins")
    return discovered


def load_plugin_metadata(plugin_dir: Path) -> Optional[PluginMetadata]:
    """
    Load plugin metadata from plugin-info.json.

    Args:
        plugin_dir: Path to plugin directory

    Returns:
        PluginMetadata if successful, None if failed

    Example:
        metadata = load_plugin_metadata(Path('plugins/clock'))
        print(metadata.display_name)  # "Clock"
    """
    plugin_info_path = plugin_dir / "plugin-info.json"

    try:
        with open(plugin_info_path, "r") as f:
            data = json.load(f)

        # Required fields
        plugin_id = data.get("id", plugin_dir.name)
        display_name = data.get("display_name", plugin_id.replace("_", " ").title())
        class_name = data.get("class")

        if not class_name:
            logger.error(f"Plugin {plugin_id}: 'class' field required in plugin-info.json")
            return None

        # Optional fields
        description = data.get("description", "")
        author = data.get("author", "")
        version = data.get("version", "1.0.0")
        icon = data.get("icon", "icon.png")

        return PluginMetadata(
            plugin_id=plugin_id,
            display_name=display_name,
            class_name=class_name,
            description=description,
            author=author,
            version=version,
            icon=icon,
        )

    except FileNotFoundError:
        logger.error(f"Plugin {plugin_dir.name}: plugin-info.json not found")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Plugin {plugin_dir.name}: Invalid JSON in plugin-info.json: {e}")
        return None
    except Exception as e:
        logger.error(f"Plugin {plugin_dir.name}: Failed to load metadata: {e}")
        return None


def load_plugin_class(plugin_dir: Path, class_name: str) -> Optional[Type[BasePlugin]]:
    """
    Dynamically load plugin class from Python module.

    Args:
        plugin_dir: Path to plugin directory
        class_name: Name of plugin class to load

    Returns:
        Plugin class if successful, None if failed

    Example:
        ClockClass = load_plugin_class(Path('plugins/clock'), 'Clock')
        instance = ClockClass()
    """
    plugin_id = plugin_dir.name

    # Construct module path (e.g., "clock.clock" or "weather.weather")
    plugin_module_file = plugin_dir / f"{plugin_id}.py"

    if not plugin_module_file.exists():
        logger.error(f"Plugin {plugin_id}: Module file not found: {plugin_module_file}")
        return None

    try:
        # Load module dynamically
        spec = importlib.util.spec_from_file_location(
            f"artframe.plugins.{plugin_id}", plugin_module_file
        )

        if spec is None or spec.loader is None:
            logger.error(f"Plugin {plugin_id}: Failed to create module spec")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get class from module
        if not hasattr(module, class_name):
            logger.error(f"Plugin {plugin_id}: Class '{class_name}' not found in module")
            return None

        plugin_class = getattr(module, class_name)

        # Verify it's a BasePlugin subclass
        if not issubclass(plugin_class, BasePlugin):
            logger.error(f"Plugin {plugin_id}: Class '{class_name}' must inherit from BasePlugin")
            return None

        return plugin_class

    except Exception as e:
        logger.error(f"Plugin {plugin_id}: Failed to load module: {e}", exc_info=True)
        return None


def load_plugins(plugins_dir: Path) -> int:
    """
    Discover and load all plugins from directory.

    Populates the global PLUGIN_CLASSES and PLUGIN_METADATA registries.

    Args:
        plugins_dir: Path to plugins directory

    Returns:
        Number of plugins successfully loaded

    Example:
        loaded = load_plugins(Path('src/artframe/plugins/builtin'))
        print(f"Loaded {loaded} plugins")
    """
    global PLUGIN_CLASSES, PLUGIN_METADATA

    # Clear existing registries
    PLUGIN_CLASSES.clear()
    PLUGIN_METADATA.clear()

    # Discover plugins
    discovered = discover_plugins(plugins_dir)

    if not discovered:
        logger.warning("No plugins discovered")
        return 0

    # Load each plugin
    loaded_count = 0

    for plugin_id, plugin_dir in discovered.items():
        logger.info(f"Loading plugin: {plugin_id}")

        # Load metadata
        metadata = load_plugin_metadata(plugin_dir)
        if metadata is None:
            logger.error(f"Plugin {plugin_id}: Failed to load metadata, skipping")
            continue

        # Load plugin class
        plugin_class = load_plugin_class(plugin_dir, metadata.class_name)
        if plugin_class is None:
            logger.error(f"Plugin {plugin_id}: Failed to load class, skipping")
            continue

        # Instantiate plugin
        try:
            plugin_instance = plugin_class()
            plugin_instance._plugin_dir = plugin_dir  # Set plugin directory

            # Register plugin
            PLUGIN_CLASSES[plugin_id] = plugin_instance
            PLUGIN_METADATA[plugin_id] = metadata

            loaded_count += 1
            logger.info(f"✓ Plugin {plugin_id} loaded successfully")

        except Exception as e:
            logger.error(f"Plugin {plugin_id}: Failed to instantiate: {e}", exc_info=True)
            continue

    logger.info(f"Successfully loaded {loaded_count}/{len(discovered)} plugins")
    return loaded_count


def get_plugin(plugin_id: str) -> Optional[BasePlugin]:
    """
    Get plugin instance by ID.

    Args:
        plugin_id: Plugin identifier (e.g., "clock", "weather")

    Returns:
        Plugin instance if found, None otherwise

    Example:
        clock_plugin = get_plugin('clock')
        if clock_plugin:
            image = clock_plugin.generate_image(settings, device_config)
    """
    return PLUGIN_CLASSES.get(plugin_id)


def get_plugin_metadata(plugin_id: str) -> Optional[PluginMetadata]:
    """
    Get plugin metadata by ID.

    Args:
        plugin_id: Plugin identifier

    Returns:
        PluginMetadata if found, None otherwise

    Example:
        metadata = get_plugin_metadata('clock')
        print(metadata.display_name)  # "Clock"
    """
    return PLUGIN_METADATA.get(plugin_id)


def list_plugins() -> List[str]:
    """
    Get list of all loaded plugin IDs.

    Returns:
        List of plugin IDs

    Example:
        plugins = list_plugins()
        print(plugins)  # ['clock', 'weather', 'immich_photos']
    """
    return list(PLUGIN_CLASSES.keys())


def list_plugin_metadata() -> List[PluginMetadata]:
    """
    Get list of all loaded plugin metadata.

    Returns:
        List of PluginMetadata objects

    Example:
        for metadata in list_plugin_metadata():
            print(f"{metadata.display_name} v{metadata.version}")
    """
    return list(PLUGIN_METADATA.values())


def reload_plugins(plugins_dir: Path) -> int:
    """
    Reload all plugins from directory.

    Useful for development when plugins are updated.

    Args:
        plugins_dir: Path to plugins directory

    Returns:
        Number of plugins loaded

    Example:
        # After modifying a plugin
        reload_plugins(Path('src/artframe/plugins/builtin'))
    """
    logger.info("Reloading plugins...")
    return load_plugins(plugins_dir)


def is_plugin_loaded(plugin_id: str) -> bool:
    """
    Check if a plugin is loaded.

    Args:
        plugin_id: Plugin identifier

    Returns:
        True if plugin is loaded

    Example:
        if is_plugin_loaded('clock'):
            print("Clock plugin is available")
    """
    return plugin_id in PLUGIN_CLASSES

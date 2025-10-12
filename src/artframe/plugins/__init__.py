"""
Artframe plugin system.

Provides a simple, extensible plugin architecture for generating
content on e-ink displays. Inspired by InkyPi's plugin system.

Example:
    # Load plugins
    from artframe.plugins import load_plugins, get_plugin

    load_plugins(Path('src/artframe/plugins/builtin'))

    # Get a plugin
    clock = get_plugin('clock')

    # Generate image
    image = clock.generate_image(
        settings={'clock_face': 'digital'},
        device_config={'width': 600, 'height': 448}
    )
"""

from .base_plugin import BasePlugin
from .instance_manager import InstanceManager
from .plugin_registry import (
    PLUGIN_CLASSES,
    PLUGIN_METADATA,
    PluginMetadata,
    discover_plugins,
    get_plugin,
    get_plugin_metadata,
    is_plugin_loaded,
    list_plugin_metadata,
    list_plugins,
    load_plugin_metadata,
    load_plugins,
    reload_plugins,
)

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "InstanceManager",
    "discover_plugins",
    "load_plugins",
    "load_plugin_metadata",
    "get_plugin",
    "get_plugin_metadata",
    "list_plugins",
    "list_plugin_metadata",
    "reload_plugins",
    "is_plugin_loaded",
    "PLUGIN_CLASSES",
    "PLUGIN_METADATA",
]

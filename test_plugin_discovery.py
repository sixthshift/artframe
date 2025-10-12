"""Test plugin discovery for the new Immich plugin."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from artframe.plugins import load_plugins, list_plugins, list_plugin_metadata

# Load plugins from builtin directory
plugins_dir = Path(__file__).parent / "src" / "artframe" / "plugins" / "builtin"

print("=" * 60)
print("Plugin Discovery Test")
print("=" * 60)
print(f"\nSearching in: {plugins_dir}")
print()

# Load plugins
loaded_count = load_plugins(plugins_dir)

print(f"\nLoaded {loaded_count} plugins")
print()

# List all plugins
plugin_ids = list_plugins()
print("Available plugins:")
for plugin_id in sorted(plugin_ids):
    print(f"  - {plugin_id}")

print()

# Show detailed metadata
print("Plugin details:")
for metadata in list_plugin_metadata():
    print(f"\n  ID: {metadata.plugin_id}")
    print(f"  Name: {metadata.display_name}")
    print(f"  Class: {metadata.class_name}")
    print(f"  Version: {metadata.version}")
    print(f"  Author: {metadata.author}")
    print(f"  Description: {metadata.description[:60]}...")

print("\n" + "=" * 60)

# Check if Immich plugin is loaded
if "immich" in plugin_ids:
    print("✅ Immich plugin successfully discovered and loaded!")
else:
    print("❌ Immich plugin NOT found")

print("=" * 60)

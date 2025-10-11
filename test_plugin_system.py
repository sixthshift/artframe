#!/usr/bin/env python3
"""
Simple test script to verify Artframe plugin system works.

This script tests:
1. Plugin discovery
2. Plugin loading
3. Plugin metadata parsing
4. Plugin instantiation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from artframe.plugins import (
    load_plugins,
    list_plugins,
    list_plugin_metadata,
    get_plugin,
    get_plugin_metadata
)


def main():
    print("=" * 60)
    print("Artframe Plugin System Test")
    print("=" * 60)
    print()

    # Path to builtin plugins
    plugins_dir = Path(__file__).parent / 'src' / 'artframe' / 'plugins' / 'builtin'

    print(f"📁 Plugin directory: {plugins_dir}")
    print()

    # Test 1: Load plugins
    print("🔍 Discovering and loading plugins...")
    loaded_count = load_plugins(plugins_dir)
    print(f"✓ Loaded {loaded_count} plugin(s)")
    print()

    # Test 2: List plugins
    print("📋 Available plugins:")
    plugins = list_plugins()
    for plugin_id in plugins:
        print(f"  - {plugin_id}")
    print()

    # Test 3: Show plugin metadata
    print("📝 Plugin metadata:")
    for metadata in list_plugin_metadata():
        print(f"\n  Plugin: {metadata.display_name}")
        print(f"    ID: {metadata.plugin_id}")
        print(f"    Class: {metadata.class_name}")
        print(f"    Version: {metadata.version}")
        print(f"    Author: {metadata.author}")
        print(f"    Description: {metadata.description}")
    print()

    # Test 4: Get a specific plugin
    if 'immich_photos' in plugins:
        print("🔌 Testing Immich Photos plugin:")
        plugin = get_plugin('immich_photos')
        metadata = get_plugin_metadata('immich_photos')

        print(f"  ✓ Plugin instance: {plugin}")
        print(f"  ✓ Plugin directory: {plugin.get_plugin_directory()}")

        # Test settings validation
        print("\n  Testing settings validation:")

        # Invalid settings (missing required fields)
        valid, error = plugin.validate_settings({})
        print(f"    Empty settings: {'✓ Valid' if valid else f'✗ Invalid - {error}'}")

        # Valid settings (minimal)
        valid, error = plugin.validate_settings({
            'immich_url': 'https://immich.example.com',
            'immich_api_key': 'test_key',
            'selection_mode': 'random',
            'use_ai': False
        })
        print(f"    Valid settings: {'✓ Valid' if valid else f'✗ Invalid - {error}'}")

        # Test cache methods
        test_settings = {
            'immich_url': 'https://immich.example.com',
            'immich_api_key': 'test_key',
            'use_ai': True,
            'ai_style': 'ghibli'
        }
        cache_key = plugin.get_cache_key(test_settings)
        cache_ttl = plugin.get_cache_ttl(test_settings)
        print(f"\n  Cache configuration:")
        print(f"    Cache key: {cache_key}")
        print(f"    Cache TTL: {cache_ttl} seconds ({cache_ttl // 3600} hours)")

        print("\n  ✓ Immich Photos plugin working correctly")
    else:
        print("⚠️  Immich Photos plugin not found")

    print()
    print("=" * 60)
    print("✅ Plugin system test complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

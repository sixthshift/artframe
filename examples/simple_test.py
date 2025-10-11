#!/usr/bin/env python3
"""
Simple test script to verify Artframe installation and basic functionality.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
from artframe.config import ConfigManager
from artframe.display.drivers import MockDriver
from artframe.storage import StorageManager
from PIL import Image


def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")

    try:
        config_path = Path(__file__).parent.parent / "config" / "artframe.yaml"
        config_manager = ConfigManager(config_path)

        print(f"  ✅ Configuration loaded successfully")
        print(f"  📁 Cache directory: {config_manager.get_cache_config()['directory']}")
        print(f"  🖥️  Display driver: {config_manager.get_display_config()['driver']}")
        print(f"  🎨 Style provider: {config_manager.get_style_config()['provider']}")

        return True
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False


def test_mock_display():
    """Test mock display driver."""
    print("🖥️  Testing mock display...")

    try:
        config = {
            'width': 600,
            'height': 448,
            'save_images': True,
            'output_dir': '/tmp/artframe_test'
        }

        driver = MockDriver(config)
        driver.initialize()

        # Create a simple test image
        test_image = Image.new('L', (600, 448), 128)  # Gray image
        driver.display_image(test_image)

        print(f"  ✅ Mock display test successful")
        print(f"  📁 Check /tmp/artframe_test/ for saved image")

        return True
    except Exception as e:
        print(f"  ❌ Mock display test failed: {e}")
        return False


def test_storage_manager():
    """Test storage manager."""
    print("💾 Testing storage manager...")

    try:
        storage_dir = Path("/tmp/artframe_test_storage")
        storage_manager = StorageManager(storage_dir)

        stats = storage_manager.get_storage_stats()
        print(f"  ✅ Storage manager test successful")
        print(f"  📊 Storage stats: {stats.total_photos} photos, {stats.total_styled_images} styled images, {stats.total_size_mb:.2f} MB")

        return True
    except Exception as e:
        print(f"  ❌ Storage manager test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running Artframe basic tests...\n")

    # Setup logging
    logging.basicConfig(level=logging.WARNING)

    tests = [
        test_configuration,
        test_mock_display,
        test_storage_manager,
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Artframe installation looks good.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
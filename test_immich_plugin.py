"""
Test the Immich Album Sync plugin.

This script tests the plugin's ability to:
1. Connect to Immich server
2. Fetch album assets
3. Sync photos locally
4. Display photos from local cache
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from artframe.plugins.builtin.immich.immich import Immich
from PIL import Image


def test_immich_plugin():
    """Test Immich plugin functionality."""

    print("=" * 60)
    print("Immich Album Sync Plugin Test")
    print("=" * 60)

    # Plugin settings
    settings = {
        "_instance_id": "test_instance",
        "immich_url": input("Enter Immich server URL (e.g., https://immich.example.com): ").strip(),
        "immich_api_key": input("Enter Immich API key: ").strip(),
        "album_id": input("Enter album ID (or press Enter for all photos): ").strip() or None,
        "selection_mode": "random",
        "sync_interval_hours": 6,
        "max_photos": 10  # Limit to 10 for testing
    }

    # Device config (mock display)
    device_config = {
        "width": 800,
        "height": 600
    }

    print("\n" + "=" * 60)
    print("Testing Plugin")
    print("=" * 60)

    # Create plugin instance
    plugin = Immich()

    # Validate settings
    print("\n1. Validating settings...")
    is_valid, error_msg = plugin.validate_settings(settings)
    if not is_valid:
        print(f"   ❌ Validation failed: {error_msg}")
        return
    print("   ✓ Settings valid")

    # Enable plugin
    print("\n2. Enabling plugin...")
    try:
        plugin.on_enable(settings)
        print("   ✓ Plugin enabled")
    except Exception as e:
        print(f"   ❌ Failed to enable plugin: {e}")
        return

    # Generate first image (will trigger sync)
    print("\n3. Generating first image (will sync photos)...")
    try:
        image = plugin.generate_image(settings, device_config)
        print(f"   ✓ Generated image: {image.size}")

        # Save test image
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "immich_test_1.png"
        image.save(output_path)
        print(f"   ✓ Saved to: {output_path}")

    except Exception as e:
        print(f"   ❌ Failed to generate image: {e}")
        import traceback
        traceback.print_exc()
        return

    # Check sync metadata
    print("\n4. Checking sync status...")
    try:
        metadata = plugin._metadata
        synced_count = len(metadata.get("synced_assets", {}))
        last_sync = metadata.get("last_sync", "Never")
        print(f"   ✓ Synced photos: {synced_count}")
        print(f"   ✓ Last sync: {last_sync}")
        print(f"   ✓ Album ID: {metadata.get('album_id', 'All photos')}")

        # Show storage location
        print(f"   ✓ Storage: {plugin._sync_dir}")

    except Exception as e:
        print(f"   ⚠ Could not read metadata: {e}")

    # Generate another image (should use cache)
    print("\n5. Generating second image (from cache)...")
    try:
        image2 = plugin.generate_image(settings, device_config)
        print(f"   ✓ Generated image: {image2.size}")

        output_path2 = output_dir / "immich_test_2.png"
        image2.save(output_path2)
        print(f"   ✓ Saved to: {output_path2}")

    except Exception as e:
        print(f"   ❌ Failed to generate second image: {e}")

    # Test sequential mode
    print("\n6. Testing sequential selection mode...")
    settings["selection_mode"] = "sequential"
    try:
        for i in range(3):
            image = plugin.generate_image(settings, device_config)
            output_path = output_dir / f"immich_sequential_{i+1}.png"
            image.save(output_path)
            print(f"   ✓ Generated sequential image {i+1}")
    except Exception as e:
        print(f"   ❌ Sequential test failed: {e}")

    # Cleanup
    print("\n7. Cleaning up...")
    plugin.on_disable(settings)
    print("   ✓ Plugin disabled")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print(f"\nTest images saved to: {output_dir.absolute()}")
    print(f"Plugin data stored in: {plugin._sync_dir}")
    print("\nYou can now:")
    print("- Check the test_output/ directory for generated images")
    print("- Inspect the synced photos in ~/.artframe/plugins/immich/test_instance/")
    print("- Run the test again to verify caching works")


if __name__ == "__main__":
    try:
        test_immich_plugin()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

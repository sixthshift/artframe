#!/usr/bin/env python3
"""
Test script for Quote of the Day and Word of the Day plugins.

Tests:
1. Plugin loading and validation
2. Image generation
3. Settings validation
4. Cache behavior
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from artframe.plugins import load_plugins, get_plugin


def test_quote_plugin():
    """Test Quote of the Day plugin."""
    print("\n" + "=" * 60)
    print("Testing Quote of the Day Plugin")
    print("=" * 60)

    plugin = get_plugin('quote_of_the_day')
    assert plugin is not None, "Quote plugin not found"
    print("✓ Plugin loaded successfully")

    # Test settings validation
    print("\n📝 Testing settings validation:")

    # Valid settings
    settings = {
        'category': 'inspirational',
        'font_size': 'medium',
        'daily_quote': True,
        'show_author': True
    }
    valid, error = plugin.validate_settings(settings)
    assert valid, f"Valid settings marked invalid: {error}"
    print("  ✓ Valid settings accepted")

    # Invalid category
    invalid_settings = {
        'category': 'invalid_category',
        'font_size': 'medium'
    }
    valid, error = plugin.validate_settings(invalid_settings)
    assert not valid, "Invalid settings marked valid"
    print(f"  ✓ Invalid category rejected: {error}")

    # Invalid font size
    invalid_settings = {
        'category': 'inspirational',
        'font_size': 'huge'
    }
    valid, error = plugin.validate_settings(invalid_settings)
    assert not valid, "Invalid settings marked valid"
    print(f"  ✓ Invalid font size rejected: {error}")

    # Test image generation
    print("\n🖼️  Testing image generation:")
    device_config = {
        'width': 600,
        'height': 448,
        'rotation': 0,
        'color_mode': 'grayscale'
    }

    # Test each category
    for category in ['inspirational', 'wisdom', 'funny', 'technology']:
        settings = {
            'category': category,
            'font_size': 'medium',
            'daily_quote': True,
            'show_author': True,
            'text_color': '#000000',
            'background_color': '#FFFFFF'
        }

        image = plugin.generate_image(settings, device_config)
        assert image is not None, f"Failed to generate image for {category}"
        assert image.size == (600, 448), f"Wrong image size for {category}"
        print(f"  ✓ {category.capitalize()} quote generated successfully")

    # Test cache behavior
    print("\n💾 Testing cache behavior:")
    cache_key_daily = plugin.get_cache_key({'daily_quote': True, 'category': 'inspirational'})
    cache_ttl_daily = plugin.get_cache_ttl({'daily_quote': True})
    print(f"  ✓ Daily cache: {cache_key_daily} (TTL: {cache_ttl_daily}s)")

    cache_key_random = plugin.get_cache_key({'daily_quote': False, 'category': 'inspirational'})
    cache_ttl_random = plugin.get_cache_ttl({'daily_quote': False})
    print(f"  ✓ Random cache: {cache_key_random} (TTL: {cache_ttl_random}s)")

    assert cache_ttl_daily == 86400, "Daily cache should be 24 hours"
    assert cache_ttl_random == 0, "Random should not cache"

    print("\n✅ Quote of the Day plugin: ALL TESTS PASSED")


def test_word_plugin():
    """Test Word of the Day plugin."""
    print("\n" + "=" * 60)
    print("Testing Word of the Day Plugin")
    print("=" * 60)

    plugin = get_plugin('word_of_the_day')
    assert plugin is not None, "Word plugin not found"
    print("✓ Plugin loaded successfully")

    # Test settings validation
    print("\n📝 Testing settings validation:")

    # Valid settings
    settings = {
        'difficulty': 'medium',
        'font_size': 'medium',
        'daily_word': True,
        'show_pronunciation': True,
        'show_example': True
    }
    valid, error = plugin.validate_settings(settings)
    assert valid, f"Valid settings marked invalid: {error}"
    print("  ✓ Valid settings accepted")

    # Invalid difficulty
    invalid_settings = {
        'difficulty': 'impossible',
        'font_size': 'medium'
    }
    valid, error = plugin.validate_settings(invalid_settings)
    assert not valid, "Invalid settings marked valid"
    print(f"  ✓ Invalid difficulty rejected: {error}")

    # Invalid font size
    invalid_settings = {
        'difficulty': 'easy',
        'font_size': 'gigantic'
    }
    valid, error = plugin.validate_settings(invalid_settings)
    assert not valid, "Invalid settings marked valid"
    print(f"  ✓ Invalid font size rejected: {error}")

    # Test image generation
    print("\n🖼️  Testing image generation:")
    device_config = {
        'width': 600,
        'height': 448,
        'rotation': 0,
        'color_mode': 'grayscale'
    }

    # Test each difficulty
    for difficulty in ['easy', 'medium', 'hard']:
        settings = {
            'difficulty': difficulty,
            'font_size': 'medium',
            'daily_word': True,
            'show_pronunciation': True,
            'show_example': True,
            'text_color': '#000000',
            'accent_color': '#4CAF50',
            'background_color': '#FFFFFF'
        }

        image = plugin.generate_image(settings, device_config)
        assert image is not None, f"Failed to generate image for {difficulty}"
        assert image.size == (600, 448), f"Wrong image size for {difficulty}"
        print(f"  ✓ {difficulty.capitalize()} word generated successfully")

    # Test with pronunciation and example disabled
    settings = {
        'difficulty': 'medium',
        'font_size': 'medium',
        'daily_word': True,
        'show_pronunciation': False,
        'show_example': False,
        'text_color': '#000000',
        'accent_color': '#4CAF50',
        'background_color': '#FFFFFF'
    }

    image = plugin.generate_image(settings, device_config)
    assert image is not None, "Failed to generate minimal word image"
    print("  ✓ Minimal word (no pronunciation/example) generated successfully")

    # Test cache behavior
    print("\n💾 Testing cache behavior:")
    cache_key_daily = plugin.get_cache_key({'daily_word': True, 'difficulty': 'medium'})
    cache_ttl_daily = plugin.get_cache_ttl({'daily_word': True})
    print(f"  ✓ Daily cache: {cache_key_daily} (TTL: {cache_ttl_daily}s)")

    cache_key_random = plugin.get_cache_key({'daily_word': False, 'difficulty': 'medium'})
    cache_ttl_random = plugin.get_cache_ttl({'daily_word': False})
    print(f"  ✓ Random cache: {cache_key_random} (TTL: {cache_ttl_random}s)")

    assert cache_ttl_daily == 86400, "Daily cache should be 24 hours"
    assert cache_ttl_random == 0, "Random should not cache"

    print("\n✅ Word of the Day plugin: ALL TESTS PASSED")


def main():
    print("\n" + "=" * 60)
    print("🧪 New Plugins Comprehensive Test Suite")
    print("=" * 60)

    # Load plugins
    plugins_dir = Path(__file__).parent / 'src' / 'artframe' / 'plugins' / 'builtin'
    loaded = load_plugins(plugins_dir)
    print(f"\n✓ Loaded {loaded} plugins")

    # Run tests
    try:
        test_quote_plugin()
        test_word_plugin()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        print("\n✅ Quote of the Day: Working")
        print("✅ Word of the Day: Working")
        print("\n Both plugins are ready for production use! 🚀\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

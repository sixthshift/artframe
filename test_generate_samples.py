#!/usr/bin/env python3
"""
Generate sample images from all plugins.

Creates sample output images to verify visual appearance.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from artframe.plugins import load_plugins, get_plugin


def main():
    print("\n" + "=" * 60)
    print("🎨 Generating Sample Images from All Plugins")
    print("=" * 60)

    # Load plugins
    plugins_dir = Path(__file__).parent / 'src' / 'artframe' / 'plugins' / 'builtin'
    load_plugins(plugins_dir)

    # Output directory
    output_dir = Path(__file__).parent / 'sample_outputs'
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Output directory: {output_dir}")

    device_config = {
        'width': 600,
        'height': 448,
        'rotation': 0,
        'color_mode': 'grayscale'
    }

    # Test Clock
    print("\n⏰ Generating Clock samples...")
    clock = get_plugin('clock')

    for idx, (time_format, show_seconds) in enumerate([('24h', True), ('12h', False)], 1):
        settings = {
            'time_format': time_format,
            'show_seconds': show_seconds,
            'date_format': 'full',
            'font_size': 'large',
            'text_color': '#000000',
            'background_color': '#FFFFFF'
        }
        image = clock.generate_image(settings, device_config)
        output_file = output_dir / f'clock_{idx}_{time_format}.png'
        image.save(output_file)
        print(f"  ✓ Saved: {output_file.name}")

    # Test Quote of the Day
    print("\n💬 Generating Quote samples...")
    quote = get_plugin('quote_of_the_day')

    for idx, category in enumerate(['inspirational', 'wisdom', 'funny', 'technology'], 1):
        settings = {
            'category': category,
            'font_size': 'medium',
            'daily_quote': False,  # Random for variety
            'show_author': True,
            'text_color': '#000000',
            'background_color': '#FFFFFF'
        }
        image = quote.generate_image(settings, device_config)
        output_file = output_dir / f'quote_{idx}_{category}.png'
        image.save(output_file)
        print(f"  ✓ Saved: {output_file.name}")

    # Test Word of the Day
    print("\n📚 Generating Word samples...")
    word = get_plugin('word_of_the_day')

    for idx, difficulty in enumerate(['easy', 'medium', 'hard'], 1):
        settings = {
            'difficulty': difficulty,
            'font_size': 'medium',
            'daily_word': False,  # Random for variety
            'show_pronunciation': True,
            'show_example': True,
            'text_color': '#000000',
            'accent_color': '#4CAF50',
            'background_color': '#FFFFFF'
        }
        image = word.generate_image(settings, device_config)
        output_file = output_dir / f'word_{idx}_{difficulty}.png'
        image.save(output_file)
        print(f"  ✓ Saved: {output_file.name}")

    print("\n" + "=" * 60)
    print(f"✅ Generated {len(list(output_dir.glob('*.png')))} sample images!")
    print("=" * 60)
    print(f"\nView them in: {output_dir}")
    print("\nSamples generated:")
    print("  • Clock: 2 variants")
    print("  • Quote of the Day: 4 categories")
    print("  • Word of the Day: 3 difficulty levels")
    print()


if __name__ == '__main__':
    main()

"""
Color calibration profiles for e-paper displays.

Each display model can have its own calibration profile that defines
the actual RGB values its pigments produce. This helps PIL's quantization
make better color choices by matching source colors to what users will
actually see on the display.

To add calibration for a new display:
1. Add a new entry to DISPLAY_CALIBRATION with the model name as key
2. Define the RGB values that the display's pigments actually produce
3. Optionally add notes about how the values were measured/sourced
"""

from typing import TypedDict


class ColorPalette(TypedDict):
    """Type definition for a 7-color display palette."""

    black: tuple[int, int, int]
    white: tuple[int, int, int]
    yellow: tuple[int, int, int]
    red: tuple[int, int, int]
    blue: tuple[int, int, int]
    green: tuple[int, int, int]


# Default "ideal" palette - pure RGB values
# Used as fallback when no calibration exists for a display
DEFAULT_PALETTE: ColorPalette = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "yellow": (255, 255, 0),
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
}


# Calibrated palettes for specific display models
# Key: model name (matches waveshare_driver.SUPPORTED_MODELS keys)
# Value: palette with measured RGB values
DISPLAY_CALIBRATION: dict[str, ColorPalette] = {
    # Waveshare 7.3" e-Paper (E) - Spectra 6 display
    # Source: https://forums.pimoroni.com/t/what-rgb-colors-are-you-using-for-the-colors-on-the-impression-spectra-6/27942
    # These values were measured against a calibrated sRGB monitor
    "epd7in3e": {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "yellow": (240, 224, 80),  # Muted, slightly orange-tinted
        "red": (160, 32, 32),  # Much darker than pure red (almost maroon)
        "blue": (80, 128, 184),  # Shifted towards cyan, quite muted
        "green": (96, 128, 80),  # Muted olive-ish green
    },
    # Add more display calibrations here as needed:
    # "epd7in3f": { ... },  # ACeP 7-color display
    # "epd5in65f": { ... }, # 5.65" 7-color display
}


def get_calibrated_palette(model: str) -> ColorPalette | None:
    """Get the calibrated color palette for a display model.

    Args:
        model: Display model name (e.g., "epd7in3e")

    Returns:
        Calibrated palette if available, None otherwise.
    """
    return DISPLAY_CALIBRATION.get(model)


def get_palette_for_display(
    model: str,
    use_calibrated: bool = True,
    custom_overrides: dict[str, tuple[int, int, int] | list[int]] | None = None,
) -> ColorPalette:
    """Get the color palette to use for a display.

    Args:
        model: Display model name
        use_calibrated: Whether to use calibrated values (if available)
        custom_overrides: Optional per-color RGB overrides

    Returns:
        Color palette to use for quantization.
    """
    # Start with calibrated or default palette
    if use_calibrated and model in DISPLAY_CALIBRATION:
        palette = dict(DISPLAY_CALIBRATION[model])
    else:
        palette = dict(DEFAULT_PALETTE)

    # Apply custom overrides
    if custom_overrides:
        for color_name, rgb in custom_overrides.items():
            if color_name in palette:
                if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
                    palette[color_name] = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

    return palette  # type: ignore[return-value]

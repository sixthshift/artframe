"""
Display utilities for aspect ratio and orientation calculations.
"""

from typing import Dict, Tuple, Any
from fractions import Fraction


def get_display_info(width: int, height: int, rotation: int = 0) -> Dict[str, Any]:
    """
    Get display information including orientation and aspect ratio.

    Args:
        width: Display width in pixels
        height: Display height in pixels
        rotation: Display rotation in degrees (0, 90, 180, 270)

    Returns:
        Dictionary with display information:
        - effective_width: Width after rotation
        - effective_height: Height after rotation
        - orientation: 'landscape' or 'portrait'
        - aspect_ratio: Simplified ratio string (e.g., '4:3', '16:9')
        - aspect_decimal: Decimal aspect ratio
    """
    # Apply rotation to get effective dimensions
    if rotation in (90, 270):
        effective_width = height
        effective_height = width
    else:
        effective_width = width
        effective_height = height

    # Determine orientation
    orientation = "landscape" if effective_width > effective_height else "portrait"

    # Calculate aspect ratio
    aspect_decimal = effective_width / effective_height

    # Simplify to common aspect ratio
    fraction = Fraction(effective_width, effective_height)
    aspect_ratio = f"{fraction.numerator}:{fraction.denominator}"

    # Try to match common ratios for cleaner display
    common_ratios = {
        1.333: "4:3",
        1.5: "3:2",
        1.6: "16:10",
        1.777: "16:9",
        0.75: "3:4",  # Portrait versions
        0.666: "2:3",
        0.625: "10:16",
        0.562: "9:16",
    }

    # Find closest common ratio
    for ratio_value, ratio_string in common_ratios.items():
        if abs(aspect_decimal - ratio_value) < 0.01:
            aspect_ratio = ratio_string
            break

    return {
        "effective_width": effective_width,
        "effective_height": effective_height,
        "orientation": orientation,
        "aspect_ratio": aspect_ratio,
        "aspect_decimal": round(aspect_decimal, 3),
    }


def format_style_prompt(prompt: str, display_config: Dict[str, Any]) -> str:
    """
    Format a style prompt with display-specific information.

    Args:
        prompt: Style prompt with placeholders
        display_config: Display configuration including dimensions and rotation

    Returns:
        Formatted prompt with display information
    """
    width = display_config.get("width", 600)
    height = display_config.get("height", 448)
    rotation = display_config.get("rotation", 0)

    # Get display info
    info = get_display_info(width, height, rotation)

    # Replace placeholders
    formatted = prompt.format(
        width=info["effective_width"],
        height=info["effective_height"],
        orientation=info["orientation"],
        aspect_ratio=info["aspect_ratio"],
    )

    return formatted


def get_crop_params(
    source_width: int, source_height: int, target_width: int, target_height: int
) -> Tuple[int, int, int, int]:
    """
    Calculate crop parameters to fit source image to target display.

    Args:
        source_width: Source image width
        source_height: Source image height
        target_width: Target display width
        target_height: Target display height

    Returns:
        Tuple of (x, y, width, height) for cropping
    """
    source_ratio = source_width / source_height
    target_ratio = target_width / target_height

    if source_ratio > target_ratio:
        # Source is wider - crop horizontally
        new_width = int(source_height * target_ratio)
        x = (source_width - new_width) // 2
        return (x, 0, new_width, source_height)
    else:
        # Source is taller - crop vertically
        new_height = int(source_width / target_ratio)
        y = (source_height - new_height) // 2
        return (0, y, source_width, new_height)

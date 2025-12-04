"""
Base interface for display drivers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from PIL import Image


class DriverInterface(ABC):
    """Abstract base class for display drivers."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the display driver with configuration."""
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        """Validate the driver configuration. Raise ValueError if invalid."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the display hardware."""
        pass

    @abstractmethod
    def get_display_size(self) -> tuple[int, int]:
        """
        Get display dimensions.

        Returns:
            Tuple[int, int]: (width, height) in pixels
        """
        pass

    @abstractmethod
    def display_image(
        self, image: Image.Image, plugin_info: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Display an image on the screen.

        Args:
            image: PIL Image to display
            plugin_info: Optional metadata about the plugin that generated the image
        """
        pass

    @abstractmethod
    def clear_display(self) -> None:
        """Clear the display."""
        pass

    @abstractmethod
    def sleep(self) -> None:
        """Put display into low power mode."""
        pass

    @abstractmethod
    def wake(self) -> None:
        """Wake display from low power mode."""
        pass

    def optimize_image_for_display(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for the specific display characteristics.

        Args:
            image: Input PIL Image

        Returns:
            PIL Image optimized for display
        """
        display_size = self.get_display_size()

        # Resize to display dimensions
        image = image.resize(display_size, Image.Resampling.LANCZOS)

        # Convert to grayscale if not already
        if image.mode != "L":
            image = image.convert("L")

        return image

    # Optional capability methods - drivers can override these for additional features

    def get_current_image_path(self) -> Optional[Path]:
        """
        Get path to the current displayed image file, if available.

        Returns:
            Path to image file, or None if not available (e.g., hardware-only display)
        """
        return None

    def get_last_displayed_image(self) -> Optional[Image.Image]:
        """
        Get the last displayed image as a PIL Image, if available.

        Returns:
            PIL Image, or None if not available
        """
        return None

    def get_display_count(self) -> int:
        """
        Get the number of images displayed since driver initialization.

        Returns:
            Number of display operations performed
        """
        return 0

    def get_last_plugin_info(self) -> dict[str, Any]:
        """
        Get metadata about the last plugin that generated content.

        Returns:
            Dict with plugin info, or empty dict if not tracked
        """
        return {}


class DisplayError(Exception):
    """Exception raised by display drivers."""

    pass

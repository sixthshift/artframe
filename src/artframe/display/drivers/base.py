"""
Base interface for display drivers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image


class DriverInterface(ABC):
    """Abstract base class for display drivers."""

    def __init__(self, config: Dict[str, Any]):
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
    def get_display_size(self) -> Tuple[int, int]:
        """
        Get display dimensions.

        Returns:
            Tuple[int, int]: (width, height) in pixels
        """
        pass

    @abstractmethod
    def display_image(self, image: Image.Image) -> None:
        """
        Display an image on the screen.

        Args:
            image: PIL Image to display
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
        if image.mode != 'L':
            image = image.convert('L')

        return image


class DisplayError(Exception):
    """Exception raised by display drivers."""
    pass
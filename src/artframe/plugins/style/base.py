"""
Base class for style plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path


class StylePlugin(ABC):
    """Abstract base class for AI style transformation plugins."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the style plugin with configuration."""
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        """Validate the plugin configuration. Raise ValueError if invalid."""
        pass

    @abstractmethod
    def apply_style(self, image_path: Path, style: str, output_path: Path) -> bool:
        """
        Apply an artistic style to an image.

        Args:
            image_path: Path to the input image
            style: Name of the style to apply
            output_path: Path where styled image should be saved

        Returns:
            bool: True if transformation was successful

        Raises:
            StyleError: If style transformation fails
        """
        pass

    @abstractmethod
    def get_available_styles(self) -> List[str]:
        """
        Get list of available artistic styles.

        Returns:
            List[str]: Available style names
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connectivity to the AI service.

        Returns:
            bool: True if connection is successful
        """
        pass

    def estimate_processing_time(self, image_path: Path, style: str) -> int:
        """
        Estimate processing time for a style transformation.

        Args:
            image_path: Path to the input image
            style: Style to apply

        Returns:
            int: Estimated processing time in seconds
        """
        return 30  # Default estimate


class StyleError(Exception):
    """Exception raised by style plugins."""
    pass
"""
Mock display driver for development and testing.
"""

import time
from typing import Dict, Any, Tuple
from pathlib import Path
from PIL import Image

from .base import DriverInterface, DisplayError


class MockDriver(DriverInterface):
    """Mock display driver for development/testing."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize mock driver."""
        super().__init__(config)

        self.width = self.config.get('width', 600)
        self.height = self.config.get('height', 448)
        self.save_images = self.config.get('save_images', True)
        self.output_dir = Path(self.config.get('output_dir', '/tmp/artframe_mock'))

        if self.save_images:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.display_count = 0
        self.current_image = None

    def validate_config(self) -> None:
        """Validate mock driver configuration."""
        width = self.config.get('width', 600)
        height = self.config.get('height', 448)

        if not isinstance(width, int) or width <= 0:
            raise ValueError("Width must be a positive integer")

        if not isinstance(height, int) or height <= 0:
            raise ValueError("Height must be a positive integer")

    def initialize(self) -> None:
        """Initialize mock display (no-op)."""
        print(f"Mock display initialized: {self.width}x{self.height}")

    def get_display_size(self) -> Tuple[int, int]:
        """Get mock display dimensions."""
        return (self.width, self.height)

    def display_image(self, image: Image.Image) -> None:
        """Display image (save to file if configured)."""
        try:
            # Optimize for display
            processed_image = self.optimize_image_for_display(image)
            self.current_image = processed_image

            # Save image if configured
            if self.save_images:
                filename = f"display_{self.display_count:04d}.png"
                output_path = self.output_dir / filename
                processed_image.save(output_path)
                print(f"Mock display: Image saved to {output_path}")

            self.display_count += 1

            # Simulate display refresh time
            time.sleep(0.1)

            print(f"Mock display: Displayed image {self.display_count}")

        except Exception as e:
            raise DisplayError(f"Mock display error: {e}")

    def clear_display(self) -> None:
        """Clear mock display."""
        white_image = Image.new('L', (self.width, self.height), 255)
        self.display_image(white_image)
        print("Mock display: Cleared to white")

    def sleep(self) -> None:
        """Mock sleep mode."""
        print("Mock display: Entering sleep mode")

    def wake(self) -> None:
        """Mock wake from sleep."""
        print("Mock display: Waking from sleep mode")

    def get_last_displayed_image(self) -> Image.Image:
        """Get the last displayed image (for testing)."""
        return self.current_image

    def get_display_count(self) -> int:
        """Get number of images displayed (for testing)."""
        return self.display_count
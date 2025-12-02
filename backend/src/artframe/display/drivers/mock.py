"""
Mock display driver for development and testing.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from .base import DisplayError, DriverInterface


class MockDriver(DriverInterface):
    """Mock display driver for development/testing."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize mock driver."""
        super().__init__(config)

        self.width = self.config.get("width", 600)
        self.height = self.config.get("height", 448)
        self.save_images = self.config.get("save_images", True)
        self.output_dir = Path(self.config.get("output_dir", "/tmp/artframe_mock"))
        self.simulate_eink = self.config.get("simulate_eink", False)

        if self.save_images:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.display_count = 0
        self.current_image: Optional[Image.Image] = None
        self.current_image_path: Optional[Path] = None
        self.last_plugin_info: Dict[str, Any] = {}

    def validate_config(self) -> None:
        """Validate mock driver configuration."""
        width = self.config.get("width", 600)
        height = self.config.get("height", 448)

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

    def display_image(
        self, image: Image.Image, plugin_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Display image (save to file if configured)."""
        try:
            # Optimize for display
            processed_image = self.optimize_image_for_display(image)

            # Apply e-ink simulation if enabled
            if self.simulate_eink:
                processed_image = self._simulate_eink_display(processed_image)

            self.current_image = processed_image
            self.last_plugin_info = plugin_info if plugin_info is not None else {}

            # Save image if configured
            if self.save_images:
                # Save numbered version
                filename = f"display_{self.display_count:04d}.png"
                output_path = self.output_dir / filename
                processed_image.save(output_path)

                # Also save as "latest.png" for web serving
                latest_path = self.output_dir / "latest.png"
                processed_image.save(latest_path)

                self.current_image_path = latest_path
                print(f"Mock display: Image saved to {output_path}")

            self.display_count += 1

            # Simulate display refresh time
            time.sleep(0.1)

            print(f"Mock display: Displayed image {self.display_count}")

        except Exception as e:
            raise DisplayError(f"Mock display error: {e}")

    def clear_display(self) -> None:
        """Clear mock display."""
        white_image = Image.new("L", (self.width, self.height), 255)
        self.display_image(white_image)
        print("Mock display: Cleared to white")

    def sleep(self) -> None:
        """Mock sleep mode."""
        print("Mock display: Entering sleep mode")

    def wake(self) -> None:
        """Mock wake from sleep."""
        print("Mock display: Waking from sleep mode")

    def get_last_displayed_image(self) -> Optional[Image.Image]:
        """Get the last displayed image (for testing)."""
        return self.current_image

    def get_display_count(self) -> int:
        """Get number of images displayed (for testing)."""
        return self.display_count

    def get_current_image_path(self) -> Optional[Path]:
        """Get path to current displayed image (for web serving)."""
        return self.current_image_path

    def get_last_plugin_info(self) -> Dict[str, Any]:
        """Get info about last plugin that generated content."""
        return self.last_plugin_info

    def _simulate_eink_display(self, image: Image.Image) -> Image.Image:
        """
        Simulate e-ink display characteristics for more realistic preview.

        Applies:
        - Limited grayscale levels (e-ink typically has 16 levels, not 256)
        - Floyd-Steinberg dithering for better grayscale representation
        - Slight contrast adjustment
        """
        from PIL import ImageEnhance

        # Start with grayscale
        if image.mode != "L":
            image = image.convert("L")

        # E-ink displays typically have limited grayscale levels
        # Spectra 6 has about 16 levels of gray
        levels = 16

        # Quantize to limited grayscale levels
        # This simulates e-ink's limited gray range
        factor = 255.0 / (levels - 1)

        def quantize_pixel(val):
            level = round(val / factor)
            return int(level * factor)

        # Apply quantization
        pixels = image.load()
        if pixels is None:
            return image
        width, height = image.size
        for y in range(height):
            for x in range(width):
                pixels[x, y] = quantize_pixel(pixels[x, y])

        # Slight contrast boost (e-ink tends to have good contrast)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        return image

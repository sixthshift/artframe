"""
Unified Waveshare e-Paper display driver.
Supports any Waveshare display by dynamically loading the appropriate module.
"""

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from .base import DisplayError, DriverInterface


class WaveshareDriver(DriverInterface):
    """Universal driver for Waveshare e-Paper displays."""

    # Supported display models and their specifications
    SUPPORTED_MODELS = {
        "epd5in83": {"width": 600, "height": 448, "colors": 2},
        "epd7in3e": {"width": 800, "height": 480, "colors": 7},
        # Add more models as needed:
        # "epd2in13": {"width": 250, "height": 122, "colors": 2},
    }

    def __init__(self, config: Dict[str, Any]):
        """Initialize Waveshare driver with configuration."""
        super().__init__(config)

        # Add the waveshare directory to Python path for epdconfig import
        waveshare_dir = Path(__file__).parent / "waveshare"
        if str(waveshare_dir) not in sys.path:
            sys.path.insert(0, str(waveshare_dir))

        self.model = self.config.get("model", "epd7in3e")
        self.rotation = self.config.get("rotation", 0)
        self.show_metadata = self.config.get("show_metadata", True)

        # Dynamically import the appropriate Waveshare display module
        self.epd_module = self._load_display_module()
        self.epd: Optional[Any] = None
        self.initialized = False

    def validate_config(self) -> None:
        """Validate Waveshare driver configuration."""
        # Check model is supported
        if "model" not in self.config:
            raise ValueError("Display model is required (e.g., 'epd7in3e')")

        model = self.config["model"]
        if model not in self.SUPPORTED_MODELS:
            supported = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ValueError(
                f"Unsupported display model: {model}. Supported models: {supported}"
            )

        # Validate GPIO pins if provided
        if "gpio_pins" in self.config:
            gpio_pins = self.config["gpio_pins"]
            optional_pins = ["busy", "reset", "dc", "cs"]

            for pin in optional_pins:
                if pin in gpio_pins:
                    pin_value = gpio_pins[pin]
                    if not isinstance(pin_value, int) or pin_value < 0 or pin_value > 40:
                        raise ValueError(f"Invalid GPIO pin number for {pin}: {pin_value}")

        # Validate rotation
        rotation = self.config.get("rotation", 0)
        if rotation not in [0, 90, 180, 270]:
            raise ValueError(f"Invalid rotation: {rotation}. Must be 0, 90, 180, or 270")

    def _load_display_module(self):
        """Dynamically load the appropriate Waveshare display module."""
        try:
            module_name = f".waveshare.{self.model}"
            module = importlib.import_module(module_name, package="artframe.display.drivers")
            return module
        except ImportError as e:
            raise DisplayError(
                f"Failed to load Waveshare display module '{self.model}': {e}"
            )

    def initialize(self) -> None:
        """Initialize the Waveshare display."""
        try:
            # Configure GPIO pins if provided
            if "gpio_pins" in self.config:
                import epdconfig

                gpio_pins = self.config["gpio_pins"]
                if "reset" in gpio_pins:
                    epdconfig.RST_PIN = gpio_pins["reset"]
                if "dc" in gpio_pins:
                    epdconfig.DC_PIN = gpio_pins["dc"]
                if "cs" in gpio_pins:
                    epdconfig.CS_PIN = gpio_pins["cs"]
                if "busy" in gpio_pins:
                    epdconfig.BUSY_PIN = gpio_pins["busy"]

            # Create EPD instance
            self.epd = self.epd_module.EPD()

            # Initialize display
            if self.epd.init() != 0:
                raise DisplayError("Failed to initialize Waveshare display")

            self.initialized = True

        except Exception as e:
            raise DisplayError(f"Failed to initialize Waveshare display: {e}")

    def get_display_size(self) -> Tuple[int, int]:
        """Get display dimensions accounting for rotation."""
        spec = self.SUPPORTED_MODELS[self.model]
        width, height = spec["width"], spec["height"]

        if self.rotation in [90, 270]:
            return (height, width)
        else:
            return (width, height)

    def display_image(self, image: Image.Image) -> None:
        """Display an image on the Waveshare display."""
        if not self.initialized:
            self.initialize()

        if self.epd is None:
            raise DisplayError("Display not initialized")

        try:
            # Prepare image for display
            processed_image = self._prepare_image(image)

            # Convert to display buffer format
            buffer = self.epd.getbuffer(processed_image)

            # Send to display
            self.epd.display(buffer)

        except Exception as e:
            raise DisplayError(f"Failed to display image: {e}")

    def clear_display(self) -> None:
        """Clear the display to white."""
        if not self.initialized:
            self.initialize()

        if self.epd is None:
            raise DisplayError("Display not initialized")

        try:
            # Clear to white (0x11 is white for 7-color displays)
            self.epd.Clear(0x11)

        except Exception as e:
            raise DisplayError(f"Failed to clear display: {e}")

    def sleep(self) -> None:
        """Put display into deep sleep mode."""
        if not self.initialized or self.epd is None:
            return

        try:
            self.epd.sleep()
        except Exception as e:
            raise DisplayError(f"Failed to put display to sleep: {e}")

    def wake(self) -> None:
        """Wake display from sleep mode."""
        try:
            # Re-initialize display to wake it
            if self.epd is None:
                self.epd = self.epd_module.EPD()

            if self.epd.init() != 0:
                raise DisplayError("Failed to wake display")

            self.initialized = True

        except Exception as e:
            raise DisplayError(f"Failed to wake display: {e}")

    def _prepare_image(self, image: Image.Image) -> Image.Image:
        """Prepare image for display (resize and rotate)."""
        # Get target size
        display_size = self.get_display_size()

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize to display dimensions
        image = image.resize(display_size, Image.Resampling.LANCZOS)

        # Apply rotation if needed
        if self.rotation != 0:
            # PIL rotation is counterclockwise, so negate
            image = image.rotate(-self.rotation, expand=True)

        return image

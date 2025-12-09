"""
Unified Waveshare e-Paper display driver.
Supports any Waveshare display by dynamically loading the appropriate module.
"""

import importlib
import sys
from pathlib import Path
from typing import Any, Optional

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

    def __init__(self, config: dict[str, Any]):
        """Initialize Waveshare driver with configuration."""
        super().__init__(config)

        # Add waveshare directory to path so vendor EPD modules can find epdconfig
        # (the EPD files are copied from Waveshare's repo and use `import epdconfig`)
        waveshare_dir = Path(__file__).parent / "waveshare"
        if str(waveshare_dir) not in sys.path:
            sys.path.insert(0, str(waveshare_dir))

        self.model = self.config.get("model", "epd7in3e")
        self.rotation = self.config.get("rotation", 0)
        self.show_metadata = self.config.get("show_metadata", True)

        # Optional preview/tracking capabilities (same as mock driver)
        self.save_images = self.config.get("save_images", False)
        self.output_dir = Path(self.config.get("output_dir", "/tmp/artframe_preview"))
        if self.save_images:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.display_count = 0
        self.current_image: Optional[Image.Image] = None
        self.current_image_path: Optional[Path] = None
        self.last_plugin_info: dict[str, Any] = {}

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
            raise ValueError(f"Unsupported display model: {model}. Supported models: {supported}")

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
            msg = f"Failed to load Waveshare display module '{self.model}': {e}"
            raise DisplayError(msg) from e

    def initialize(self) -> None:
        """Initialize the Waveshare display."""
        try:
            print("[DEBUG] initialize() starting...")
            print(f"[DEBUG] self.config = {self.config}")
            print(f"[DEBUG] self.model = {self.model}")

            # Configure GPIO pins if provided (mypy can't see epdconfig's dynamic attrs)
            if "gpio_pins" in self.config:
                print("[DEBUG] gpio_pins found in config, importing epdconfig...")
                # Import epdconfig using the same module name as the EPD files use
                # (they do `import epdconfig` after we add waveshare dir to sys.path)
                # Using `from .waveshare import epdconfig` creates a DIFFERENT module
                # in Python's cache, causing GPIO to be claimed twice!
                import epdconfig  # type: ignore[import-not-found]

                print("[DEBUG] epdconfig imported successfully")
                gpio_pins = self.config["gpio_pins"]
                print(f"[DEBUG] gpio_pins = {gpio_pins}")

                if "reset" in gpio_pins:
                    print(f"[DEBUG] Setting RST_PIN = {gpio_pins['reset']}")
                    epdconfig.RST_PIN = gpio_pins["reset"]  # type: ignore[attr-defined]
                if "dc" in gpio_pins:
                    print(f"[DEBUG] Setting DC_PIN = {gpio_pins['dc']}")
                    epdconfig.DC_PIN = gpio_pins["dc"]  # type: ignore[attr-defined]
                if "cs" in gpio_pins:
                    print(f"[DEBUG] Setting CS_PIN = {gpio_pins['cs']}")
                    epdconfig.CS_PIN = gpio_pins["cs"]  # type: ignore[attr-defined]
                if "busy" in gpio_pins:
                    print(f"[DEBUG] Setting BUSY_PIN = {gpio_pins['busy']}")
                    epdconfig.BUSY_PIN = gpio_pins["busy"]  # type: ignore[attr-defined]

                print("[DEBUG] GPIO pins configured")
            else:
                print("[DEBUG] No gpio_pins in config, skipping pin configuration")

            # Create EPD instance
            print(f"[DEBUG] Creating EPD instance from {self.epd_module}...")
            self.epd = self.epd_module.EPD()
            print(f"[DEBUG] EPD instance created: {self.epd}")

            # Initialize display
            print("[DEBUG] Calling self.epd.init()...")
            init_result = self.epd.init()
            print(f"[DEBUG] self.epd.init() returned: {init_result}")

            if init_result != 0:
                raise DisplayError("Failed to initialize Waveshare display")

            self.initialized = True
            print("[DEBUG] initialize() completed successfully")

        except Exception as e:
            print(f"[DEBUG] initialize() FAILED with exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise DisplayError(f"Failed to initialize Waveshare display: {e}") from e

    def get_display_size(self) -> tuple[int, int]:
        """Get display dimensions accounting for rotation."""
        spec = self.SUPPORTED_MODELS[self.model]
        width, height = spec["width"], spec["height"]

        if self.rotation in [90, 270]:
            return (height, width)
        else:
            return (width, height)

    def display_image(
        self, image: Image.Image, plugin_info: Optional[dict[str, Any]] = None
    ) -> None:
        """Display an image on the Waveshare display."""
        if not self.initialized:
            self.initialize()

        if self.epd is None:
            raise DisplayError("Display not initialized")

        display_started = False
        try:
            # Prepare image for display
            processed_image = self._prepare_image(image)

            # Track state
            self.current_image = processed_image
            self.last_plugin_info = plugin_info if plugin_info is not None else {}
            self.display_count += 1

            # Save preview image if configured
            if self.save_images:
                filename = f"display_{self.display_count:04d}.png"
                output_path = self.output_dir / filename
                processed_image.save(output_path)

                latest_path = self.output_dir / "latest.png"
                processed_image.save(latest_path)
                self.current_image_path = latest_path

            # Convert to display buffer format
            buffer = self.epd.getbuffer(processed_image)

            # Send to display - mark as started so we ensure sleep on any failure
            display_started = True
            self.epd.display(buffer)

        except Exception as e:
            raise DisplayError(f"Failed to display image: {e}") from e
        finally:
            # CRITICAL: Always put display to sleep after refresh attempt to prevent damage
            # E-ink displays can be permanently damaged if left powered on
            # See: https://www.waveshare.com/wiki/7.3inch_e-Paper_HAT_(E)_Manual
            if display_started and self.epd is not None:
                try:
                    self.epd.sleep()
                except Exception:
                    pass  # Best effort - don't mask original exception
                self.initialized = False  # Will need re-init on next display

    def clear_display(self) -> None:
        """Clear the display to white."""
        if not self.initialized:
            self.initialize()

        if self.epd is None:
            raise DisplayError("Display not initialized")

        clear_started = False
        try:
            # Clear to white (0x11 is white for 7-color displays)
            clear_started = True
            self.epd.Clear(0x11)

        except Exception as e:
            raise DisplayError(f"Failed to clear display: {e}") from e
        finally:
            # CRITICAL: Always put display to sleep after clear attempt
            if clear_started and self.epd is not None:
                try:
                    self.epd.sleep()
                except Exception:
                    pass  # Best effort
                self.initialized = False

    def sleep(self) -> None:
        """Put display into deep sleep mode."""
        if not self.initialized or self.epd is None:
            return

        try:
            self.epd.sleep()
            self.initialized = False
        except Exception as e:
            raise DisplayError(f"Failed to put display to sleep: {e}") from e

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
            raise DisplayError(f"Failed to wake display: {e}") from e

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

    # Interface method implementations

    def get_current_image_path(self) -> Optional[Path]:
        """Get path to current displayed image (if save_images is enabled)."""
        return self.current_image_path

    def get_last_displayed_image(self) -> Optional[Image.Image]:
        """Get the last displayed image."""
        return self.current_image

    def get_display_count(self) -> int:
        """Get number of images displayed."""
        return self.display_count

    def get_last_plugin_info(self) -> dict[str, Any]:
        """Get info about last plugin that generated content."""
        return self.last_plugin_info

    def run_hardware_test(self) -> dict[str, Any]:
        """Run hardware test pattern to verify display connectivity.

        Draws text and shapes in multiple colors to prove the hardware works.
        Based on official Waveshare epd_7in3e_test.py example.

        Returns:
            dict with test results including success status and any error message.
        """
        from PIL import Image, ImageDraw, ImageFont

        result = {
            "success": False,
            "message": "",
            "model": self.model,
            "display_size": self.get_display_size(),
        }

        try:
            # Initialize if needed
            if not self.initialized:
                self.initialize()

            if self.epd is None:
                raise DisplayError("Display not initialized")

            # Get display dimensions
            width, height = self.get_display_size()

            # Create test image with white background
            image = Image.new("RGB", (width, height), (255, 255, 255))
            draw = ImageDraw.Draw(image)

            # Try to load fonts, fall back to default
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
            try:
                font_large = ImageFont.truetype(f"{font_path}-Bold.ttf", 36)
                font_medium = ImageFont.truetype(f"{font_path}.ttf", 24)
                font_small = ImageFont.truetype(f"{font_path}.ttf", 18)
            except OSError:
                font_large = ImageFont.load_default()
                font_medium = font_large
                font_small = font_large

            # Define colors for 7-color display
            black = (0, 0, 0)
            colors = {
                "Black": black,
                "Red": (255, 0, 0),
                "Yellow": (255, 255, 0),
                "Blue": (0, 0, 255),
                "Green": (0, 255, 0),
            }

            # Draw title
            draw.text((20, 10), "ArtFrame Hardware Test", font=font_large, fill=black)
            model_str = f"Model: {self.model} ({width}x{height})"
            draw.text((20, 55), model_str, font=font_medium, fill=black)

            # Draw color test blocks with labels
            block_y = 100
            block_width = 120
            block_height = 60
            x_offset = 20

            for i, (name, color) in enumerate(colors.items()):
                x = x_offset + (i % 3) * (block_width + 20)
                y = block_y + (i // 3) * (block_height + 30)

                # Draw colored rectangle
                rect = [x, y, x + block_width, y + block_height]
                draw.rectangle(rect, fill=color, outline=black)
                # Draw label below
                draw.text((x, y + block_height + 5), name, font=font_small, fill=black)

            # Draw geometric shapes section
            shapes_y = 280
            draw.text((20, shapes_y), "Shapes Test:", font=font_medium, fill=black)

            # Circle
            circle_box = [30, shapes_y + 35, 100, shapes_y + 105]
            draw.ellipse(circle_box, fill=(255, 0, 0), outline=black)

            # Rectangle
            rect_box = [130, shapes_y + 35, 200, shapes_y + 105]
            draw.rectangle(rect_box, fill=(0, 255, 0), outline=black)

            # Triangle (polygon)
            triangle = [
                (265, shapes_y + 35),
                (230, shapes_y + 105),
                (300, shapes_y + 105),
            ]
            draw.polygon(triangle, fill=(0, 0, 255), outline=black)

            # Draw lines of different colors
            line_y = shapes_y + 130
            draw.text((20, line_y), "Lines:", font=font_medium, fill=black)
            for i, (_name, color) in enumerate(colors.items()):
                y = line_y + 30 + i * 15
                draw.line([(20, y), (width - 20, y)], fill=color, width=3)

            # Draw success message
            pos = (width - 250, height - 40)
            draw.text(pos, "Test Complete!", font=font_medium, fill=(0, 128, 0))

            # Display the test image
            buffer = self.epd.getbuffer(image)
            self.epd.display(buffer)

            # Save preview if enabled
            if self.save_images:
                test_path = self.output_dir / "hardware_test.png"
                image.save(test_path)
                latest_path = self.output_dir / "latest.png"
                image.save(latest_path)
                self.current_image_path = latest_path

            result["success"] = True
            result["message"] = "Hardware test pattern displayed successfully"

        except Exception as e:
            result["success"] = False
            result["message"] = f"Hardware test failed: {e}"
        finally:
            # Always put display to sleep
            if self.epd is not None:
                try:
                    self.epd.sleep()
                except Exception:
                    pass
                self.initialized = False

        return result

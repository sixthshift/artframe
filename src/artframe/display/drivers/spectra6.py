"""
Spectra 6 e-ink display driver.
"""

import time
from typing import Dict, Any, Tuple
from PIL import Image, ImageEnhance

from .base import DriverInterface, DisplayError

try:
    import spidev
    import RPi.GPIO as GPIO

    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class Spectra6Driver(DriverInterface):
    """Driver for Spectra 6 e-ink display."""

    # Display specifications
    DISPLAY_WIDTH = 600
    DISPLAY_HEIGHT = 448

    # SPI settings
    SPI_BUS = 0
    SPI_DEVICE = 0
    SPI_SPEED = 4000000

    def __init__(self, config: Dict[str, Any]):
        """Initialize Spectra 6 driver."""
        super().__init__(config)

        if not HAS_GPIO:
            raise DisplayError("RPi.GPIO and spidev are required for Spectra6Driver")

        self.gpio_pins = self.config["gpio_pins"]
        self.rotation = self.config.get("rotation", 0)
        self.show_metadata = self.config.get("show_metadata", True)

        self.spi = None
        self.initialized = False

    def validate_config(self) -> None:
        """Validate Spectra6 configuration."""
        if "gpio_pins" not in self.config:
            raise ValueError("gpio_pins configuration is required")

        gpio_pins = self.config["gpio_pins"]
        required_pins = ["busy", "reset", "dc", "cs"]

        for pin in required_pins:
            if pin not in gpio_pins:
                raise ValueError(f"GPIO pin '{pin}' not configured")

            pin_value = gpio_pins[pin]
            if not isinstance(pin_value, int) or pin_value < 0 or pin_value > 40:
                raise ValueError(f"Invalid GPIO pin number for {pin}: {pin_value}")

        # Validate rotation
        rotation = self.config.get("rotation", 0)
        if rotation not in [0, 90, 180, 270]:
            raise ValueError(f"Invalid rotation: {rotation}. Must be 0, 90, 180, or 270")

    def initialize(self) -> None:
        """Initialize the Spectra 6 display."""
        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Configure pins
            GPIO.setup(self.gpio_pins["reset"], GPIO.OUT)
            GPIO.setup(self.gpio_pins["dc"], GPIO.OUT)
            GPIO.setup(self.gpio_pins["cs"], GPIO.OUT)
            GPIO.setup(self.gpio_pins["busy"], GPIO.IN)

            # Setup SPI
            self.spi = spidev.SpiDev()
            self.spi.open(self.SPI_BUS, self.SPI_DEVICE)
            self.spi.max_speed_hz = self.SPI_SPEED
            self.spi.mode = 0

            # Reset and initialize display
            self._hardware_reset()
            self._init_display()

            self.initialized = True

        except Exception as e:
            raise DisplayError(f"Failed to initialize Spectra 6 display: {e}")

    def get_display_size(self) -> Tuple[int, int]:
        """Get display dimensions accounting for rotation."""
        if self.rotation in [90, 270]:
            return (self.DISPLAY_HEIGHT, self.DISPLAY_WIDTH)
        else:
            return (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)

    def display_image(self, image: Image.Image) -> None:
        """Display an image on the Spectra 6."""
        if not self.initialized:
            self.initialize()

        try:
            # Optimize image for e-ink display
            processed_image = self._prepare_image_for_eink(image)

            # Apply rotation if needed
            if self.rotation != 0:
                processed_image = processed_image.rotate(-self.rotation, expand=True)

            # Convert to display format
            image_data = self._convert_to_display_format(processed_image)

            # Send to display
            self._send_image_data(image_data)
            self._refresh_display()

        except Exception as e:
            raise DisplayError(f"Failed to display image: {e}")

    def clear_display(self) -> None:
        """Clear the display to white."""
        if not self.initialized:
            self.initialize()

        try:
            # Create white image
            white_image = Image.new("1", (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), 1)
            image_data = self._convert_to_display_format(white_image)

            self._send_image_data(image_data)
            self._refresh_display()

        except Exception as e:
            raise DisplayError(f"Failed to clear display: {e}")

    def sleep(self) -> None:
        """Put display into deep sleep mode."""
        if not self.initialized:
            return

        try:
            self._send_command(0x02)  # Power off command
            self._wait_for_idle()

            self._send_command(0x07)  # Deep sleep
            self._send_data([0xA5])  # Deep sleep check code

        except Exception as e:
            raise DisplayError(f"Failed to put display to sleep: {e}")

    def wake(self) -> None:
        """Wake display from sleep mode."""
        try:
            self._hardware_reset()
            self._init_display()

        except Exception as e:
            raise DisplayError(f"Failed to wake display: {e}")

    def _prepare_image_for_eink(self, image: Image.Image) -> Image.Image:
        """Prepare image specifically for e-ink display characteristics."""
        # Resize to display dimensions
        display_size = self.get_display_size()
        image = image.resize(display_size, Image.Resampling.LANCZOS)

        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Enhance contrast for e-ink
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Apply dithering for better grayscale representation
        image = image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)

        return image

    def _convert_to_display_format(self, image: Image.Image) -> bytes:
        """Convert PIL image to Spectra 6 display format."""
        # Convert to bytes array
        image_bytes = bytearray()

        for y in range(image.height):
            for x in range(0, image.width, 8):
                byte_value = 0
                for bit in range(8):
                    if x + bit < image.width:
                        pixel = image.getpixel((x + bit, y))
                        if pixel == 0:  # Black pixel
                            byte_value |= 1 << (7 - bit)
                image_bytes.append(byte_value)

        return bytes(image_bytes)

    def _hardware_reset(self) -> None:
        """Perform hardware reset of the display."""
        GPIO.output(self.gpio_pins["reset"], GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(self.gpio_pins["reset"], GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.gpio_pins["reset"], GPIO.HIGH)
        time.sleep(0.2)

    def _init_display(self) -> None:
        """Initialize display with proper settings."""
        # Power setting
        self._send_command(0x01)
        self._send_data([0x07, 0x07, 0x3F, 0x3F])

        # Power on
        self._send_command(0x04)
        time.sleep(0.1)
        self._wait_for_idle()

        # Panel setting
        self._send_command(0x00)
        self._send_data([0x1F])

        # Resolution setting
        self._send_command(0x61)
        self._send_data(
            [
                self.DISPLAY_WIDTH >> 8,
                self.DISPLAY_WIDTH & 0xFF,
                self.DISPLAY_HEIGHT >> 8,
                self.DISPLAY_HEIGHT & 0xFF,
            ]
        )

        # VCOM and data interval setting
        self._send_command(0x50)
        self._send_data([0x10, 0x07])

    def _send_image_data(self, image_data: bytes) -> None:
        """Send image data to display."""
        self._send_command(0x13)  # Data start transmission

        # Send data in chunks
        chunk_size = 4096
        for i in range(0, len(image_data), chunk_size):
            chunk = image_data[i : i + chunk_size]
            self._send_data(chunk)

    def _refresh_display(self) -> None:
        """Refresh the display to show new image."""
        self._send_command(0x12)  # Display refresh
        time.sleep(0.1)
        self._wait_for_idle()

    def _send_command(self, command: int) -> None:
        """Send command to display."""
        GPIO.output(self.gpio_pins["cs"], GPIO.LOW)
        GPIO.output(self.gpio_pins["dc"], GPIO.LOW)
        self.spi.writebytes([command])
        GPIO.output(self.gpio_pins["cs"], GPIO.HIGH)

    def _send_data(self, data) -> None:
        """Send data to display."""
        GPIO.output(self.gpio_pins["cs"], GPIO.LOW)
        GPIO.output(self.gpio_pins["dc"], GPIO.HIGH)

        if isinstance(data, (list, bytes, bytearray)):
            self.spi.writebytes(data)
        else:
            self.spi.writebytes([data])

        GPIO.output(self.gpio_pins["cs"], GPIO.HIGH)

    def _wait_for_idle(self) -> None:
        """Wait for display to be ready."""
        while GPIO.input(self.gpio_pins["busy"]) == 0:
            time.sleep(0.01)

    def __del__(self):
        """Cleanup GPIO and SPI on destruction."""
        try:
            if self.spi:
                self.spi.close()
            if HAS_GPIO:
                GPIO.cleanup()
        except Exception:
            pass

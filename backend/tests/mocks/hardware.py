"""
Mocks for hardware interfaces.

Provides mock implementations of GPIO, SPI, and e-ink display hardware
for testing on systems without actual hardware.
"""

from typing import Any, Optional
from unittest.mock import MagicMock

from PIL import Image


class MockGPIO:
    """
    Mock implementation of RPi.GPIO module.

    Simulates GPIO operations for testing on non-Raspberry Pi systems.
    """

    # Mode constants
    BCM = "BCM"
    BOARD = "BOARD"

    # Direction constants
    OUT = "OUT"
    IN = "IN"

    # Level constants
    HIGH = 1
    LOW = 0

    # Pull-up/down constants
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    PUD_OFF = "PUD_OFF"

    # Edge detection
    RISING = "RISING"
    FALLING = "FALLING"
    BOTH = "BOTH"

    def __init__(self):
        self._mode: Optional[str] = None
        self._pins: dict[int, dict[str, Any]] = {}
        self._warnings = True

    def setmode(self, mode: str) -> None:
        """Set GPIO mode (BCM or BOARD)."""
        self._mode = mode

    def getmode(self) -> Optional[str]:
        """Get current GPIO mode."""
        return self._mode

    def setwarnings(self, flag: bool) -> None:
        """Enable or disable warnings."""
        self._warnings = flag

    def setup(
        self,
        pin: int,
        direction: str,
        initial: int = LOW,
        pull_up_down: str = PUD_OFF,
    ) -> None:
        """Set up a GPIO pin."""
        self._pins[pin] = {
            "direction": direction,
            "value": initial,
            "pull_up_down": pull_up_down,
        }

    def output(self, pin: int, value: int) -> None:
        """Set output value of a pin."""
        if pin in self._pins:
            self._pins[pin]["value"] = value

    def input(self, pin: int) -> int:
        """Read input value of a pin."""
        if pin in self._pins:
            return self._pins[pin]["value"]
        return self.LOW

    def cleanup(self, pin: Optional[int] = None) -> None:
        """Clean up GPIO resources."""
        if pin is None:
            self._pins.clear()
            self._mode = None
        elif pin in self._pins:
            del self._pins[pin]

    def get_pin_state(self, pin: int) -> Optional[dict[str, Any]]:
        """Get the current state of a pin (for testing)."""
        return self._pins.get(pin)

    def get_all_pins(self) -> dict[int, dict[str, Any]]:
        """Get state of all configured pins (for testing)."""
        return self._pins.copy()


class MockSPI:
    """
    Mock implementation of SPI device.

    Simulates SPI communication for testing display drivers.
    """

    def __init__(self, bus: int = 0, device: int = 0):
        self.bus = bus
        self.device = device
        self.max_speed_hz = 4000000
        self.mode = 0
        self.bits_per_word = 8
        self._opened = False
        self._write_buffer: list[bytes] = []
        self._read_response: list[int] = [0]

    def open(self, bus: int, device: int) -> None:
        """Open SPI device."""
        self.bus = bus
        self.device = device
        self._opened = True

    def close(self) -> None:
        """Close SPI device."""
        self._opened = False

    def writebytes(self, data: list[int]) -> None:
        """Write bytes to SPI."""
        if not self._opened:
            raise IOError("SPI device not opened")
        self._write_buffer.append(bytes(data))

    def writebytes2(self, data: list[int]) -> None:
        """Write bytes to SPI (alternative method)."""
        self.writebytes(data)

    def readbytes(self, count: int) -> list[int]:
        """Read bytes from SPI."""
        if not self._opened:
            raise IOError("SPI device not opened")
        return self._read_response[:count]

    def xfer(self, data: list[int]) -> list[int]:
        """Transfer data over SPI (write and read)."""
        self.writebytes(data)
        return self._read_response[: len(data)]

    def xfer2(self, data: list[int]) -> list[int]:
        """Transfer data over SPI (alternative method)."""
        return self.xfer(data)

    def set_read_response(self, response: list[int]) -> None:
        """Set the response that will be returned by read operations."""
        self._read_response = response

    def get_write_buffer(self) -> list[bytes]:
        """Get all data written to SPI (for testing)."""
        return self._write_buffer

    def clear_write_buffer(self) -> None:
        """Clear the write buffer."""
        self._write_buffer = []


class MockWaveshareEPD:
    """
    Mock implementation of Waveshare e-ink display.

    Simulates e-ink display operations for testing without hardware.
    """

    def __init__(self, width: int = 800, height: int = 480):
        self.width = width
        self.height = height
        self._initialized = False
        self._sleeping = False
        self._last_image: Optional[Image.Image] = None
        self._display_count = 0
        self._clear_count = 0

    def init(self) -> int:
        """Initialize the display."""
        self._initialized = True
        self._sleeping = False
        return 0  # Success

    def Clear(self) -> None:
        """Clear the display."""
        if not self._initialized:
            raise RuntimeError("Display not initialized")
        self._clear_count += 1
        self._last_image = None

    def display(self, image_buffer: Any) -> None:
        """Display an image buffer."""
        if not self._initialized:
            raise RuntimeError("Display not initialized")
        if self._sleeping:
            raise RuntimeError("Display is sleeping")
        self._display_count += 1

    def displayImage(self, image: Image.Image) -> None:
        """Display a PIL Image."""
        if not self._initialized:
            raise RuntimeError("Display not initialized")
        if self._sleeping:
            raise RuntimeError("Display is sleeping")

        # Store the image for testing
        self._last_image = image.copy()
        self._display_count += 1

    def getbuffer(self, image: Image.Image) -> bytes:
        """Convert PIL Image to display buffer."""
        # Resize if needed
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))

        # Convert to grayscale and get bytes
        gray = image.convert("L")
        return bytes(gray.tobytes())

    def sleep(self) -> None:
        """Put display to sleep."""
        self._sleeping = True

    def wake(self) -> None:
        """Wake display from sleep."""
        if self._sleeping:
            self._sleeping = False
            # Re-init typically needed after wake
            self.init()

    def Dev_exit(self) -> None:
        """Clean up and exit."""
        self._initialized = False
        self._sleeping = False

    # Test helper methods
    def get_last_image(self) -> Optional[Image.Image]:
        """Get the last displayed image (for testing)."""
        return self._last_image

    def get_display_count(self) -> int:
        """Get number of times display was called."""
        return self._display_count

    def get_clear_count(self) -> int:
        """Get number of times clear was called."""
        return self._clear_count

    def is_initialized(self) -> bool:
        """Check if display is initialized."""
        return self._initialized

    def is_sleeping(self) -> bool:
        """Check if display is sleeping."""
        return self._sleeping

    def reset_counters(self) -> None:
        """Reset display and clear counters."""
        self._display_count = 0
        self._clear_count = 0


def create_mock_gpio_module() -> MagicMock:
    """
    Create a mock module that can replace RPi.GPIO.

    Usage:
        with patch.dict('sys.modules', {'RPi': MagicMock(), 'RPi.GPIO': create_mock_gpio_module()}):
            # Your code that imports RPi.GPIO
    """
    mock_gpio = MockGPIO()
    mock = MagicMock()

    mock.BCM = MockGPIO.BCM
    mock.BOARD = MockGPIO.BOARD
    mock.OUT = MockGPIO.OUT
    mock.IN = MockGPIO.IN
    mock.HIGH = MockGPIO.HIGH
    mock.LOW = MockGPIO.LOW
    mock.PUD_UP = MockGPIO.PUD_UP
    mock.PUD_DOWN = MockGPIO.PUD_DOWN

    mock.setmode = mock_gpio.setmode
    mock.getmode = mock_gpio.getmode
    mock.setwarnings = mock_gpio.setwarnings
    mock.setup = mock_gpio.setup
    mock.output = mock_gpio.output
    mock.input = mock_gpio.input
    mock.cleanup = mock_gpio.cleanup

    return mock


def create_mock_spidev_module() -> MagicMock:
    """
    Create a mock module that can replace spidev.

    Usage:
        with patch.dict('sys.modules', {'spidev': create_mock_spidev_module()}):
            # Your code that imports spidev
    """
    mock = MagicMock()
    mock.SpiDev.return_value = MockSPI()
    return mock

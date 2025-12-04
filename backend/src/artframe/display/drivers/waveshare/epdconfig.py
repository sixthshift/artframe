"""
Hardware abstraction for e-Paper displays.
Based on Waveshare epdconfig.py
"""

import logging
import os
import time

logger = logging.getLogger(__name__)


class RaspberryPi:
    """Raspberry Pi hardware implementation."""

    # Pin Definitions
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18

    def __init__(self):
        import spidev

        self.SPI = spidev.SpiDev()

    def digital_write(self, pin, value):
        import gpiozero

        if value:
            gpiozero.LED(pin).on()
        else:
            gpiozero.LED(pin).off()

    def digital_read(self, pin):
        import gpiozero

        button = gpiozero.Button(pin)
        return button.value

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        self.SPI.writebytes2(data)

    def module_init(self):
        import spidev

        try:
            self.SPI = spidev.SpiDev()
            self.SPI.open(0, 0)
            self.SPI.max_speed_hz = 4000000
            self.SPI.mode = 0b00
            return 0
        except Exception as e:
            logger.error(f"Failed to initialize SPI: {e}")
            return -1

    def module_exit(self):
        import gpiozero

        self.SPI.close()
        gpiozero.Device.pin_factory.reset()

        logger.debug("spi end")
        logger.debug("gpio cleanup...")


class JetsonNano:
    """Jetson Nano hardware implementation."""

    # Pin Definitions
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18

    def __init__(self):
        import ctypes

        find_dirs = [
            os.path.dirname(os.path.realpath(__file__)),
            "/usr/local/lib",
            "/usr/lib",
        ]
        self.SPI = None
        for find_dir in find_dirs:
            so_filename = os.path.join(find_dir, "sysfs_software_spi.so")
            if os.path.exists(so_filename):
                self.SPI = ctypes.cdll.LoadLibrary(so_filename)
                break
        if self.SPI is None:
            raise RuntimeError("Cannot find sysfs_software_spi.so")

    def digital_write(self, pin, value):
        import Jetson.GPIO as GPIO

        GPIO.output(pin, value)

    def digital_read(self, pin):
        import Jetson.GPIO as GPIO

        return GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.SYSFS_software_spi_transfer(data[0])

    def spi_writebyte2(self, data):
        for i in range(len(data)):
            self.SPI.SYSFS_software_spi_transfer(data[i])

    def module_init(self):
        import Jetson.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.RST_PIN, GPIO.OUT)
        GPIO.setup(self.DC_PIN, GPIO.OUT)
        GPIO.setup(self.CS_PIN, GPIO.OUT)
        GPIO.setup(self.PWR_PIN, GPIO.OUT)
        GPIO.setup(self.BUSY_PIN, GPIO.IN)
        self.SPI.SYSFS_software_spi_begin()
        return 0

    def module_exit(self):
        import Jetson.GPIO as GPIO

        self.SPI.SYSFS_software_spi_end()
        GPIO.output(self.RST_PIN, 0)
        GPIO.output(self.DC_PIN, 0)
        GPIO.output(self.PWR_PIN, 0)

        GPIO.cleanup([self.RST_PIN, self.DC_PIN, self.CS_PIN, self.PWR_PIN, self.BUSY_PIN])


class SunriseX3:
    """Sunrise X3 hardware implementation."""

    # Pin Definitions
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18
    Flag = 0

    def __init__(self):
        import spidev

        self.SPI = spidev.SpiDev()

    def digital_write(self, pin, value):
        import Hobot.GPIO as GPIO

        GPIO.output(pin, value)

    def digital_read(self, pin):
        import Hobot.GPIO as GPIO

        return GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.xfer3(data)

    def spi_writebyte2(self, data):
        self.SPI.xfer3(data)

    def module_init(self):
        import Hobot.GPIO as GPIO
        import spidev

        if self.Flag == 0:
            self.Flag = 1
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.RST_PIN, GPIO.OUT)
            GPIO.setup(self.DC_PIN, GPIO.OUT)
            GPIO.setup(self.CS_PIN, GPIO.OUT)
            GPIO.setup(self.PWR_PIN, GPIO.OUT)
            GPIO.setup(self.BUSY_PIN, GPIO.IN)

            self.SPI = spidev.SpiDev()
            self.SPI.open(2, 0)
            self.SPI.max_speed_hz = 4000000
            self.SPI.mode = 0b00
            return 0
        else:
            return 0

    def module_exit(self):
        import Hobot.GPIO as GPIO

        GPIO.output(self.RST_PIN, 0)
        GPIO.output(self.DC_PIN, 0)
        GPIO.output(self.PWR_PIN, 0)

        GPIO.cleanup([self.RST_PIN, self.DC_PIN, self.CS_PIN, self.PWR_PIN, self.BUSY_PIN])
        self.SPI.close()


# Platform detection and initialization
if os.path.exists("/sys/bus/platform/drivers/gpio-x3"):
    implementation = SunriseX3()
else:
    try:
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read()
        if "Raspberry" in cpuinfo:
            implementation = RaspberryPi()
        else:
            implementation = JetsonNano()
    except Exception:
        implementation = RaspberryPi()

# Export implementation methods to module level
for name in dir(implementation):
    if not name.startswith("_"):
        globals()[name] = getattr(implementation, name)

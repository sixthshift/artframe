"""
Waveshare 7.3inch e-Paper display (E) driver
800x480 resolution, 7-color display
Based on Waveshare library - V1.0 (2022-10-20)

MIT License
"""

import logging
from PIL import Image

# Import epdconfig from parent directory
import sys
import os

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pic")
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib")
if os.path.exists(libdir):
    sys.path.append(libdir)

logger = logging.getLogger(__name__)


class EPD:
    """7.3inch e-Paper display (E) class"""

    # Display resolution
    width = 800
    height = 480

    # Color definitions (RGB values for 7-color palette)
    BLACK = 0x000000  # 000
    WHITE = 0xFFFFFF  # 001
    YELLOW = 0x00FFFF  # 010
    RED = 0x0000FF  # 011
    BLUE = 0xFF0000  # 100
    GREEN = 0x00FF00  # 101
    ORANGE = 0x0080FF  # 110

    def __init__(self):
        self.reset_pin = 17
        self.dc_pin = 25
        self.busy_pin = 24
        self.cs_pin = 8
        self.width = EPD.width
        self.height = EPD.height

    def reset(self):
        """Hardware reset"""
        import epdconfig

        epdconfig.digital_write(epdconfig.RST_PIN, 1)
        epdconfig.delay_ms(20)
        epdconfig.digital_write(epdconfig.RST_PIN, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(epdconfig.RST_PIN, 1)
        epdconfig.delay_ms(20)

    def send_command(self, command):
        """Send command to display"""
        import epdconfig

        epdconfig.digital_write(epdconfig.DC_PIN, 0)
        epdconfig.digital_write(epdconfig.CS_PIN, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(epdconfig.CS_PIN, 1)

    def send_data(self, data):
        """Send single byte of data"""
        import epdconfig

        epdconfig.digital_write(epdconfig.DC_PIN, 1)
        epdconfig.digital_write(epdconfig.CS_PIN, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(epdconfig.CS_PIN, 1)

    def send_data2(self, data):
        """Send data array"""
        import epdconfig

        epdconfig.digital_write(epdconfig.DC_PIN, 1)
        epdconfig.digital_write(epdconfig.CS_PIN, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(epdconfig.CS_PIN, 1)

    def ReadBusyH(self):
        """Wait until display is ready (busy pin high)"""
        import epdconfig

        logger.debug("e-Paper busy")
        while epdconfig.digital_read(epdconfig.BUSY_PIN) == 0:
            epdconfig.delay_ms(5)
        logger.debug("e-Paper busy release")

    def TurnOnDisplay(self):
        """Turn on display and refresh"""
        self.send_command(0x04)  # Power ON
        self.ReadBusyH()

        self.send_command(0x12)  # Display Refresh
        self.send_data(0x00)
        self.ReadBusyH()

        self.send_command(0x02)  # Power OFF
        self.send_data(0x00)
        self.ReadBusyH()

    def init(self):
        """Initialize display"""
        import epdconfig

        if epdconfig.module_init() != 0:
            return -1

        self.reset()

        self.send_command(0x01)  # Power setting
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_data(0x3F)
        self.send_data(0x3F)

        self.send_command(0x04)  # Power on
        epdconfig.delay_ms(100)
        self.ReadBusyH()

        self.send_command(0x00)  # Panel setting
        self.send_data(0x0F)

        self.send_command(0x61)  # Resolution setting
        self.send_data(0x03)
        self.send_data(0x20)
        self.send_data(0x01)
        self.send_data(0xE0)

        self.send_command(0x15)
        self.send_data(0x00)

        self.send_command(0x50)  # Vcom and data interval setting
        self.send_data(0x10)
        self.send_data(0x07)

        self.send_command(0x60)  # TCON setting
        self.send_data(0x22)

        return 0

    def getbuffer(self, image):
        """
        Convert PIL image to display buffer format
        Images should be RGB mode
        """
        buf = [0x00] * int(self.width * self.height / 2)
        image_monocolor = image.convert("RGB")
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if imwidth == self.width and imheight == self.height:
            for y in range(imheight):
                for x in range(imwidth):
                    # Get color value from pixel
                    pixel = pixels[x, y]
                    pixel_value = (pixel[0] << 16) | (pixel[1] << 8) | pixel[2]

                    # Convert RGB to 7-color palette
                    color = self._get_closest_color(pixel_value)

                    # Pack 2 pixels per byte (4 bits each)
                    addr = int((x + y * self.width) / 2)
                    if (x % 2) == 0:
                        buf[addr] = (buf[addr] & 0x0F) | ((color << 4) & 0xF0)
                    else:
                        buf[addr] = (buf[addr] & 0xF0) | (color & 0x0F)
        elif imwidth == self.height and imheight == self.width:
            # Image is rotated
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1

                    pixel = pixels[x, y]
                    pixel_value = (pixel[0] << 16) | (pixel[1] << 8) | pixel[2]
                    color = self._get_closest_color(pixel_value)

                    addr = int((newx + newy * self.width) / 2)
                    if (newx % 2) == 0:
                        buf[addr] = (buf[addr] & 0x0F) | ((color << 4) & 0xF0)
                    else:
                        buf[addr] = (buf[addr] & 0xF0) | (color & 0x0F)
        return buf

    def _get_closest_color(self, rgb_value):
        """Map RGB value to closest 7-color palette value"""
        # Extract RGB components
        r = (rgb_value >> 16) & 0xFF
        g = (rgb_value >> 8) & 0xFF
        b = rgb_value & 0xFF

        # Convert to grayscale for intensity check
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)

        # Simple color mapping based on dominant channel
        if gray < 32:
            return 0  # Black
        elif gray > 224:
            return 1  # White
        elif r > 200 and g > 200 and b < 100:
            return 2  # Yellow
        elif r > 200 and g < 100 and b < 100:
            return 3  # Red
        elif r < 100 and g < 100 and b > 200:
            return 4  # Blue
        elif r < 100 and g > 200 and b < 100:
            return 5  # Green
        elif r > 150 and g > 100 and b < 100:
            return 6  # Orange
        else:
            # Default to grayscale
            if gray < 128:
                return 0  # Black
            else:
                return 1  # White

    def display(self, image):
        """Display image buffer on screen"""
        self.send_command(0x13)
        for i in range(0, int(self.width * self.height / 2)):
            self.send_data(image[i])

        self.TurnOnDisplay()

    def Clear(self, color=0x11):
        """Clear display to specified color"""
        self.send_command(0x13)
        for i in range(0, int(self.width * self.height / 2)):
            self.send_data(color)

        self.TurnOnDisplay()

    def sleep(self):
        """Put display in sleep mode"""
        import epdconfig

        self.send_command(0x02)  # Power off
        self.send_data(0x00)
        self.ReadBusyH()

        self.send_command(0x07)  # Deep sleep
        self.send_data(0xA5)

        epdconfig.delay_ms(2000)
        epdconfig.module_exit()

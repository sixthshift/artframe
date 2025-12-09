"""
Waveshare 7.3inch e-Paper display (E) driver
800x480 resolution, 7-color display
Based on official Waveshare library from GitHub

MIT License
"""

import logging

logger = logging.getLogger(__name__)

# Display resolution
EPD_WIDTH = 800
EPD_HEIGHT = 480


class EPD:
    """7.3inch e-Paper display (E) class"""

    def __init__(self):
        import epdconfig

        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.BLACK = 0x000000  # 0000 BGR
        self.WHITE = 0xFFFFFF  # 0001
        self.YELLOW = 0x00FFFF  # 0010
        self.RED = 0x0000FF  # 0011
        self.BLUE = 0xFF0000  # 0101
        self.GREEN = 0x00FF00  # 0110

    def reset(self):
        """Hardware reset"""
        import epdconfig

        print("[DEBUG EPD] reset() starting...")
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)
        print("[DEBUG EPD] reset() completed")

    def send_command(self, command):
        """Send command to display"""
        import epdconfig

        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        """Send single byte of data"""
        import epdconfig

        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data2(self, data):
        """Send data array"""
        import epdconfig

        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)

    def ReadBusyH(self):
        """Wait until display is ready (busy pin high)"""
        import epdconfig

        print(f"[DEBUG EPD] ReadBusyH() - waiting for busy_pin {self.busy_pin} to go HIGH...")
        logger.debug("e-Paper busy H")
        timeout_count = 0
        while epdconfig.digital_read(self.busy_pin) == 0:  # 0: busy, 1: idle
            epdconfig.delay_ms(5)
            timeout_count += 1
            if timeout_count % 200 == 0:  # Every ~1 second
                print(f"[DEBUG EPD] Still waiting... ({timeout_count * 5}ms elapsed, pin still LOW)")
            if timeout_count > 6000:  # 30 second timeout
                print("[DEBUG EPD] TIMEOUT! Busy pin never went high after 30s")
                break
        print(f"[DEBUG EPD] ReadBusyH() done after {timeout_count * 5}ms")
        logger.debug("e-Paper busy H release")

    def TurnOnDisplay(self):
        """Turn on display and refresh"""
        print("[DEBUG EPD] TurnOnDisplay() starting...")
        self.send_command(0x04)  # POWER_ON
        self.ReadBusyH()

        self.send_command(0x12)  # DISPLAY_REFRESH
        self.send_data(0x00)
        self.ReadBusyH()

        self.send_command(0x02)  # POWER_OFF
        self.send_data(0x00)
        self.ReadBusyH()
        print("[DEBUG EPD] TurnOnDisplay() completed")

    def init(self):
        """Initialize display - official Waveshare sequence"""
        import epdconfig

        print("[DEBUG EPD] init() starting...")

        print("[DEBUG EPD] Calling epdconfig.module_init()...")
        if epdconfig.module_init() != 0:
            print("[DEBUG EPD] module_init() FAILED!")
            return -1
        print("[DEBUG EPD] module_init() succeeded")

        # EPD hardware init start
        self.reset()

        print("[DEBUG EPD] Waiting for busy after reset...")
        self.ReadBusyH()
        epdconfig.delay_ms(30)

        print("[DEBUG EPD] Sending init commands...")

        self.send_command(0xAA)
        self.send_data(0x49)
        self.send_data(0x55)
        self.send_data(0x20)
        self.send_data(0x08)
        self.send_data(0x09)
        self.send_data(0x18)

        self.send_command(0x01)
        self.send_data(0x3F)

        self.send_command(0x00)
        self.send_data(0x5F)
        self.send_data(0x69)

        self.send_command(0x03)
        self.send_data(0x00)
        self.send_data(0x54)
        self.send_data(0x00)
        self.send_data(0x44)

        self.send_command(0x05)
        self.send_data(0x40)
        self.send_data(0x1F)
        self.send_data(0x1F)
        self.send_data(0x2C)

        self.send_command(0x06)
        self.send_data(0x6F)
        self.send_data(0x1F)
        self.send_data(0x17)
        self.send_data(0x49)

        self.send_command(0x08)
        self.send_data(0x6F)
        self.send_data(0x1F)
        self.send_data(0x1F)
        self.send_data(0x22)

        self.send_command(0x30)
        self.send_data(0x03)

        self.send_command(0x50)
        self.send_data(0x3F)

        self.send_command(0x60)
        self.send_data(0x02)
        self.send_data(0x00)

        self.send_command(0x61)
        self.send_data(0x03)
        self.send_data(0x20)
        self.send_data(0x01)
        self.send_data(0xE0)

        self.send_command(0x84)
        self.send_data(0x01)

        self.send_command(0xE3)
        self.send_data(0x2F)

        print("[DEBUG EPD] Sending power on command (0x04)...")
        self.send_command(0x04)
        self.ReadBusyH()

        print("[DEBUG EPD] init() completed successfully")
        return 0

    def getbuffer(self, image):
        """Convert PIL image to display buffer using 7-color palette"""
        from PIL import Image

        # Create a palette with the 7 colors supported by the panel
        pal_image = Image.new("P", (1, 1))
        pal_image.putpalette(
            (0, 0, 0, 255, 255, 255, 255, 255, 0, 255, 0, 0, 0, 0, 0, 0, 0, 255, 0, 255, 0)
            + (0, 0, 0) * 249
        )

        # Check if we need to rotate the image
        imwidth, imheight = image.size
        if imwidth == self.width and imheight == self.height:
            image_temp = image
        elif imwidth == self.height and imheight == self.width:
            image_temp = image.rotate(90, expand=True)
        else:
            logger.warning(
                "Invalid image dimensions: %d x %d, expected %d x %d"
                % (imwidth, imheight, self.width, self.height)
            )
            image_temp = image

        # Convert the source image to the 7 colors, dithering if needed
        image_7color = image_temp.convert("RGB").quantize(palette=pal_image)
        buf_7color = bytearray(image_7color.tobytes("raw"))

        # PIL does not support 4 bit color, so pack the 4 bits of color
        # into a single byte to transfer to the panel
        buf = [0x00] * int(self.width * self.height / 2)
        idx = 0
        for i in range(0, len(buf_7color), 2):
            buf[idx] = (buf_7color[i] << 4) + buf_7color[i + 1]
            idx += 1

        return buf

    def display(self, image):
        """Display image buffer on screen"""
        print("[DEBUG EPD] display() starting...")
        self.send_command(0x10)
        self.send_data2(image)
        self.TurnOnDisplay()
        print("[DEBUG EPD] display() completed")

    def Clear(self, color=0x11):
        """Clear display to specified color"""
        print(f"[DEBUG EPD] Clear(color={hex(color)}) starting...")
        self.send_command(0x10)
        self.send_data2([color] * int(self.height) * int(self.width / 2))
        self.TurnOnDisplay()
        print("[DEBUG EPD] Clear() completed")

    def sleep(self):
        """Put display in sleep mode"""
        import epdconfig

        print("[DEBUG EPD] sleep() starting...")
        self.send_command(0x07)  # DEEP_SLEEP
        self.send_data(0xA5)

        epdconfig.delay_ms(2000)
        epdconfig.module_exit()
        print("[DEBUG EPD] sleep() completed")

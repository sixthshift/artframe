"""
Clock plugin for Artframe.

Displays current time and date with customizable formats.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from artframe.plugins.base_plugin import BasePlugin


class Clock(BasePlugin):
    """
    Display current time and date.

    A simple plugin that shows the current time and date
    with various formatting options.
    """

    def __init__(self):
        """Initialize Clock plugin."""
        super().__init__()

    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate plugin settings.

        Args:
            settings: Plugin settings dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate time format
        time_format = settings.get("time_format", "24h")
        if time_format not in ["12h", "24h"]:
            return False, "Time format must be '12h' or '24h'"

        # Validate date format
        date_format = settings.get("date_format", "full")
        if date_format not in ["full", "short", "none"]:
            return False, "Date format must be 'full', 'short', or 'none'"

        # Validate font size
        font_size = settings.get("font_size", "large")
        if font_size not in ["small", "medium", "large", "xlarge"]:
            return False, "Font size must be 'small', 'medium', 'large', or 'xlarge'"

        # Validate timezone if provided
        timezone = settings.get("timezone")
        if timezone:
            try:
                ZoneInfo(timezone)
            except Exception:
                return False, f"Invalid timezone: '{timezone}'"

        return True, ""

    def generate_image(
        self, settings: Dict[str, Any], device_config: Dict[str, Any]
    ) -> Image.Image:
        """
        Generate clock display image.

        Args:
            settings: Plugin instance settings
            device_config: Display device configuration

        Returns:
            PIL.Image: Generated clock image

        Raises:
            RuntimeError: If image generation fails
        """
        try:
            width = device_config["width"]
            height = device_config["height"]

            # Get settings with defaults
            time_format = settings.get("time_format", "24h")
            date_format = settings.get("date_format", "full")
            font_size = settings.get("font_size", "large")
            background_color = settings.get("background_color", "#FFFFFF")
            text_color = settings.get("text_color", "#000000")
            # Use plugin timezone if set, otherwise fall back to system timezone
            timezone = settings.get("timezone") or device_config.get("timezone", "UTC")

            # Create image
            image = Image.new("RGB", (width, height), background_color)
            draw = ImageDraw.Draw(image)

            # Get current time in configured timezone
            try:
                tz = ZoneInfo(timezone)
                now = datetime.now(tz)
            except Exception:
                self.logger.warning(f"Invalid timezone '{timezone}', falling back to UTC")
                now = datetime.now(ZoneInfo("UTC"))

            # Format time string (never show seconds - rendering is expensive)
            if time_format == "12h":
                time_str = now.strftime("%I:%M %p")
            else:  # 24h
                time_str = now.strftime("%H:%M")

            # Format date string
            if date_format == "full":
                date_str = now.strftime("%A, %B %d, %Y")
            elif date_format == "short":
                date_str = now.strftime("%m/%d/%Y")
            else:  # none
                date_str = None

            # Get fonts
            time_font = self._get_font(font_size, "time")
            date_font = self._get_font(font_size, "date")

            # Calculate positions (centered)
            time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
            time_width = time_bbox[2] - time_bbox[0]
            time_height = time_bbox[3] - time_bbox[1]

            if date_str:
                date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
                date_width = date_bbox[2] - date_bbox[0]
                date_height = date_bbox[3] - date_bbox[1]

                # Center both vertically with spacing
                total_height = time_height + date_height + 20
                time_y = (height - total_height) // 2
                date_y = time_y + time_height + 20
            else:
                # Center time only
                time_y = (height - time_height) // 2
                date_width = 0
                date_y = 0

            time_x = (width - time_width) // 2

            # Draw time
            draw.text((time_x, time_y), time_str, fill=text_color, font=time_font)

            # Draw date if enabled
            if date_str:
                date_x = (width - date_width) // 2
                draw.text((date_x, date_y), date_str, fill=text_color, font=date_font)

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate clock image: {e}", exc_info=True)
            return self._create_error_image(str(e), device_config)

    def _get_font(self, size: str, text_type: str):
        """
        Get font for rendering.

        Args:
            size: Font size category ('small', 'medium', 'large', 'xlarge')
            text_type: Type of text ('time' or 'date')

        Returns:
            PIL font object (Union[FreeTypeFont, ImageFont])
        """
        # Font size mappings
        size_map = {
            "small": {"time": 48, "date": 24},
            "medium": {"time": 72, "date": 32},
            "large": {"time": 96, "date": 40},
            "xlarge": {"time": 144, "date": 48},
        }

        font_size = size_map.get(size, size_map["large"])[text_type]

        # Try to load a nice font, fall back to default if not available
        try:
            # Try common system fonts
            for font_name in [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            ]:
                try:
                    return ImageFont.truetype(font_name, font_size)
                except Exception:
                    continue

            # If no system fonts work, use default
            return ImageFont.load_default()

        except Exception as e:
            self.logger.warning(f"Failed to load custom font, using default: {e}")
            return ImageFont.load_default()

    def _create_error_image(self, error_message: str, device_config: Dict[str, Any]) -> Image.Image:
        """Create error image with message."""
        width = device_config["width"]
        height = device_config["height"]

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        text = f"Clock Error:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    def get_cache_key(self, settings: Dict[str, Any]) -> str:
        """
        Generate cache key for clock content.

        Cache per minute so the clock updates every minute.
        """
        timezone = settings.get("timezone")
        if timezone:
            try:
                tz = ZoneInfo(timezone)
                now = datetime.now(tz)
            except Exception:
                now = datetime.now()
        else:
            now = datetime.now()

        tz_suffix = f"_{timezone}" if timezone else ""
        return f"clock_{now.strftime('%Y%m%d_%H%M')}{tz_suffix}"

    def get_cache_ttl(self, settings: Dict[str, Any]) -> int:
        """
        Get cache time-to-live in seconds.

        Always returns 60 seconds (1 minute) as rendering is expensive.
        """
        return 60

    def run_active(
        self,
        display_controller,
        settings: Dict[str, Any],
        device_config: Dict[str, Any],
        stop_event,
        plugin_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Run the clock's own refresh loop.

        The clock manages its own updates - refreshing every minute
        (or every second if show_seconds is enabled).
        """
        refresh_interval = self.get_cache_ttl(settings)
        self.logger.info(f"Clock starting with {refresh_interval}s refresh interval")

        while not stop_event.is_set():
            try:
                # Generate and display the clock
                image = self.generate_image(settings, device_config)
                if image:
                    display_controller.display_image(image, plugin_info)
                    self.logger.debug("Clock display updated")
            except Exception as e:
                self.logger.error(f"Failed to update clock display: {e}")

            # Wait for the refresh interval or until stopped
            stop_event.wait(timeout=refresh_interval)

        self.logger.info("Clock stopped")

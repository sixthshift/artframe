"""
Quote of the Day plugin for Artframe.

Displays inspirational and thought-provoking quotes.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from PIL import Image, ImageDraw, ImageFont

from artframe.plugins.base_plugin import BasePlugin

# Load quotes from JSON file
_QUOTES_FILE = Path(__file__).parent / "quotes.json"
_QUOTES: list[dict[str, Any]] = []
_QUOTES_BY_CATEGORY: dict[str, list[dict[str, Any]]] = {}


def _load_quotes() -> list[dict[str, Any]]:
    """Load quotes database from JSON file."""
    global _QUOTES, _QUOTES_BY_CATEGORY
    if not _QUOTES:
        try:
            with open(_QUOTES_FILE, "r", encoding="utf-8") as f:
                _QUOTES = json.load(f)
            # Build category index
            for quote in _QUOTES:
                cat = quote.get("category", "inspirational")
                if cat not in _QUOTES_BY_CATEGORY:
                    _QUOTES_BY_CATEGORY[cat] = []
                _QUOTES_BY_CATEGORY[cat].append(quote)
        except Exception:
            _QUOTES = []
            _QUOTES_BY_CATEGORY = {}
    return _QUOTES


def _get_categories() -> list[str]:
    """Get available quote categories."""
    _load_quotes()
    return list(_QUOTES_BY_CATEGORY.keys())


class QuoteOfTheDay(BasePlugin):
    """
    Display inspirational quotes.

    Shows a random quote based on category, with proper text wrapping
    and attribution.
    """

    def __init__(self):
        """Initialize Quote of the Day plugin."""
        super().__init__()

    def validate_settings(self, settings: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate plugin settings.

        Args:
            settings: Plugin settings dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate category
        category = settings.get("category", "inspirational")
        valid_categories = _get_categories() + ["random"]
        if category not in valid_categories:
            return (
                False,
                f"Category must be one of: {', '.join(valid_categories)}",
            )

        # Validate font size
        font_size = settings.get("font_size", "medium")
        if font_size not in ["small", "medium", "large"]:
            return False, "Font size must be 'small', 'medium', or 'large'"

        # Validate refresh interval
        refresh_interval = settings.get("refresh_interval_minutes", 60)
        if not isinstance(refresh_interval, (int, float)) or refresh_interval < 1:
            return False, "Refresh interval must be at least 1 minute"

        return True, ""

    def generate_image(
        self, settings: dict[str, Any], device_config: dict[str, Any]
    ) -> Image.Image:
        """
        Generate quote display image.

        Args:
            settings: Plugin instance settings
            device_config: Display device configuration

        Returns:
            PIL.Image: Generated quote image

        Raises:
            RuntimeError: If image generation fails
        """
        try:
            width = device_config["width"]
            height = device_config["height"]

            # Get settings with defaults
            category = settings.get("category", "inspirational")
            font_size = settings.get("font_size", "medium")
            background_color = settings.get("background_color", "#FFFFFF")
            text_color = settings.get("text_color", "#000000")
            show_author = settings.get("show_author", True)
            daily_quote = settings.get("daily_quote", True)

            # Create image
            image = Image.new("RGB", (width, height), background_color)
            draw = ImageDraw.Draw(image)

            # Select quote
            quote_text, author = self._select_quote(category, daily_quote)

            # Get fonts
            quote_font = self._get_font(font_size, "quote")
            author_font = self._get_font(font_size, "author")

            # Wrap text to fit width
            margin = 40
            max_width = width - (2 * margin)

            wrapped_quote = self._wrap_text(quote_text, quote_font, max_width, draw)

            # Calculate positions
            quote_height = len(wrapped_quote) * self._get_line_height(quote_font)

            author_text = f"— {author}" if show_author else ""
            author_height = self._get_line_height(author_font) if show_author else 0

            total_height = quote_height + (20 if show_author else 0) + author_height

            # Center vertically
            y_start = (height - total_height) // 2

            # Draw quote
            y = y_start
            for line in wrapped_quote:
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                draw.text((x, y), line, fill=text_color, font=quote_font)
                y += self._get_line_height(quote_font)

            # Draw author
            if show_author:
                y += 20  # Space between quote and author
                bbox = draw.textbbox((0, 0), author_text, font=author_font)
                author_width = bbox[2] - bbox[0]
                x = (width - author_width) // 2
                draw.text((x, y), author_text, fill=text_color, font=author_font)

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate quote image: {e}", exc_info=True)
            return self._create_error_image(str(e), device_config)

    def _select_quote(self, category: str, daily: bool) -> tuple[str, str]:
        """
        Select a quote from the database.

        Args:
            category: Quote category
            daily: If True, same quote for the whole day

        Returns:
            Tuple of (quote_text, author)
        """
        _load_quotes()

        if daily:
            # Use day of year as seed for consistency throughout the day
            day_of_year = datetime.now().timetuple().tm_yday
            random.seed(day_of_year)

            # If random category, pick one deterministically for the day
            if category == "random":
                category = random.choice(list(_QUOTES_BY_CATEGORY.keys()))

            quotes = _QUOTES_BY_CATEGORY.get(category, [])

            if not quotes:
                random.seed()
                return (
                    "The only way to do great work is to love what you do.",
                    "Steve Jobs",
                )

            quote_data = random.choice(quotes)
            random.seed()  # Reset seed
        else:
            # Truly random - pick random category if needed
            if category == "random":
                category = random.choice(list(_QUOTES_BY_CATEGORY.keys()))

            quotes = _QUOTES_BY_CATEGORY.get(category, [])

            if not quotes:
                return (
                    "The only way to do great work is to love what you do.",
                    "Steve Jobs",
                )

            quote_data = random.choice(quotes)

        return (quote_data["quote"], quote_data["author"])

    def _wrap_text(
        self,
        text: str,
        font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
        max_width: int,
        draw: ImageDraw.ImageDraw,
    ) -> list[str]:
        """
        Wrap text to fit within max_width.

        Args:
            text: Text to wrap
            font: Font to use
            max_width: Maximum width in pixels
            draw: ImageDraw instance

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line: list[str] = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _get_line_height(self, font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]) -> int:
        """Get the line height for a font."""
        try:
            # FreeTypeFont has .size attribute, ImageFont doesn't
            if hasattr(font, "size"):
                return int(font.size + 10)  # Font size + spacing
            return 30
        except Exception:
            return 30  # Default fallback

    def _get_font(
        self, size: str, text_type: str
    ) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
        """
        Get font for rendering.

        Args:
            size: Font size category ('small', 'medium', 'large')
            text_type: Type of text ('quote' or 'author')

        Returns:
            PIL font object
        """
        # Font size mappings
        size_map = {
            "small": {"quote": 20, "author": 16},
            "medium": {"quote": 28, "author": 20},
            "large": {"quote": 36, "author": 24},
        }

        font_size = size_map.get(size, size_map["medium"])[text_type]

        # Try to load a nice font, fall back to default if not available
        try:
            # Try common system fonts
            for font_name in [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",  # Linux
                "C:\\Windows\\Fonts\\georgia.ttf",  # Windows
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

    def _create_error_image(self, error_message: str, device_config: dict[str, Any]) -> Image.Image:
        """Create error image with message."""
        width = device_config["width"]
        height = device_config["height"]

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        text = f"Quote Error:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    def get_refresh_interval(self, settings: dict[str, Any]) -> int:
        """
        Get refresh interval in seconds.

        Uses refresh_interval_minutes from settings (default 60 minutes).
        """
        refresh_minutes = settings.get("refresh_interval_minutes", 60)
        return int(refresh_minutes * 60)

    def run_active(
        self,
        display_controller,
        settings: dict[str, Any],
        device_config: dict[str, Any],
        stop_event,
        plugin_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Run the quote display with daily refresh.

        Refreshes every 24 hours to show the next day's quote.
        If daily_quote is False, refreshes every hour with a new random quote.
        """
        refresh_interval = self.get_refresh_interval(settings)

        self.logger.info(f"Quote of the Day starting with {refresh_interval}s refresh interval")

        while not stop_event.is_set():
            try:
                image = self.generate_image(settings, device_config)
                if image:
                    display_controller.display_image(image, plugin_info)
                    self.logger.debug("Quote of the Day display updated")
            except Exception as e:
                self.logger.error(f"Failed to update quote display: {e}")

            stop_event.wait(timeout=refresh_interval)

        self.logger.info("Quote of the Day stopped")

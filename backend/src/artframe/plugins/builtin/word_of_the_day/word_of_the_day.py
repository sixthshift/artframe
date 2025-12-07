"""
Word of the Day plugin for Artframe.

Displays vocabulary words with definitions and examples.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from PIL import Image, ImageDraw, ImageFont

from artframe.plugins.base_plugin import BasePlugin

# Load vocabulary from JSON file
_VOCABULARY_FILE = Path(__file__).parent / "vocabulary.json"
_VOCABULARY: list[dict[str, Any]] = []


def _load_vocabulary() -> list[dict[str, Any]]:
    """Load vocabulary database from JSON file."""
    global _VOCABULARY
    if not _VOCABULARY:
        try:
            with open(_VOCABULARY_FILE, "r", encoding="utf-8") as f:
                _VOCABULARY = json.load(f)
        except Exception:
            _VOCABULARY = []
    return _VOCABULARY


class WordOfTheDay(BasePlugin):
    """
    Display vocabulary words with definitions.

    Educational plugin that shows a word, pronunciation, definition,
    and example sentence to help expand vocabulary.
    """

    def __init__(self):
        """Initialize Word of the Day plugin."""
        super().__init__()

    def validate_settings(self, settings: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate plugin settings.

        Args:
            settings: Plugin settings dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate font size
        font_size = settings.get("font_size", "medium")
        if font_size not in ["small", "medium", "large"]:
            return False, "Font size must be 'small', 'medium', or 'large'"

        return True, ""

    def generate_image(
        self, settings: dict[str, Any], device_config: dict[str, Any]
    ) -> Image.Image:
        """
        Generate word display image.

        Args:
            settings: Plugin instance settings
            device_config: Display device configuration

        Returns:
            PIL.Image: Generated word image

        Raises:
            RuntimeError: If image generation fails
        """
        try:
            width = device_config["width"]
            height = device_config["height"]

            # Get settings with defaults
            font_size = settings.get("font_size", "medium")
            background_color = settings.get("background_color", "#FFFFFF")
            text_color = settings.get("text_color", "#000000")
            accent_color = settings.get("accent_color", "#4CAF50")
            show_example = settings.get("show_example", True)
            show_synonyms = settings.get("show_synonyms", True)
            daily_word = settings.get("daily_word", True)

            # Create image
            image = Image.new("RGB", (width, height), background_color)
            draw = ImageDraw.Draw(image)

            # Select word
            word_data = self._select_word(daily_word)
            word = word_data["word"]
            pos = word_data["part_of_speech"]
            definition = word_data["definition"]
            example = word_data.get("example")
            synonyms = word_data.get("synonyms", [])

            # Get fonts
            header_font = self._get_font(font_size, "header")
            word_font = self._get_font(font_size, "word")
            body_font = self._get_font(font_size, "body")

            # Layout
            margin = 30
            y = margin

            # Header
            header_text = "Word of the Day"
            draw.text((margin, y), header_text, fill=accent_color, font=header_font)
            y += self._get_line_height(header_font) + 15

            # Separator line
            draw.line([(margin, y), (width - margin, y)], fill=accent_color, width=2)
            y += 20

            # Word (large and bold)
            draw.text((margin, y), word.upper(), fill=text_color, font=word_font)
            y += self._get_line_height(word_font) + 5

            # Part of speech (italic style via color)
            draw.text((margin, y), pos, fill=accent_color, font=body_font)
            y += self._get_line_height(body_font) + 15

            # Definition
            max_width = width - (2 * margin)
            wrapped_definition = self._wrap_text(definition, body_font, max_width, draw)

            for line in wrapped_definition:
                draw.text((margin, y), line, fill=text_color, font=body_font)
                y += self._get_line_height(body_font)

            # Example sentence
            if show_example and example:
                y += 15
                draw.text((margin, y), "Example:", fill=accent_color, font=body_font)
                y += self._get_line_height(body_font) + 5

                # Wrap and draw example (in quotes)
                example_text = f'"{example}"'
                wrapped_example = self._wrap_text(example_text, body_font, max_width, draw)

                for line in wrapped_example:
                    draw.text((margin, y), line, fill=text_color, font=body_font)
                    y += self._get_line_height(body_font)

            # Synonyms
            if show_synonyms and synonyms:
                y += 15
                synonyms_text = "Synonyms: " + ", ".join(synonyms)
                wrapped_synonyms = self._wrap_text(synonyms_text, body_font, max_width, draw)

                for line in wrapped_synonyms:
                    draw.text((margin, y), line, fill=accent_color, font=body_font)
                    y += self._get_line_height(body_font)

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate word image: {e}", exc_info=True)
            return self._create_error_image(str(e), device_config)

    def _select_word(self, daily: bool) -> dict[str, Any]:
        """
        Select a word from the vocabulary database.

        Args:
            daily: If True, same word for the whole day

        Returns:
            Dictionary with word, part_of_speech, definition, example, synonyms
        """
        words = _load_vocabulary()

        if not words:
            # Fallback if vocabulary file is missing
            return {
                "word": "Vocabulary",
                "part_of_speech": "noun",
                "definition": "A list or collection of words and phrases",
                "example": "Building your vocabulary is important for communication.",
                "synonyms": ["lexicon", "dictionary", "glossary"],
            }

        if daily:
            # Use day of year as seed for consistency throughout the day
            day_of_year = datetime.now().timetuple().tm_yday
            random.seed(day_of_year)
            word = random.choice(words)
            random.seed()  # Reset seed
        else:
            # Truly random
            word = random.choice(words)

        return word

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
                return int(font.size + 8)
            return 25
        except Exception:
            return 25  # Default fallback

    def _get_font(
        self, size: str, text_type: str
    ) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
        """
        Get font for rendering.

        Args:
            size: Font size category ('small', 'medium', 'large')
            text_type: Type of text ('header', 'word', 'body')

        Returns:
            PIL font object
        """
        # Font size mappings
        size_map = {
            "small": {"header": 16, "word": 32, "body": 14},
            "medium": {"header": 20, "word": 40, "body": 16},
            "large": {"header": 24, "word": 48, "body": 18},
        }

        font_size = size_map.get(size, size_map["medium"])[text_type]

        # Try to load a nice font
        try:
            for font_name in [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            ]:
                try:
                    return ImageFont.truetype(font_name, font_size)
                except Exception:
                    continue

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

        text = f"Word Error:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    def get_refresh_interval(self, settings: dict[str, Any]) -> int:
        """
        Get refresh interval in seconds.

        If daily_word is True, refresh every 24 hours.
        Otherwise, refresh every hour to show new random words.
        """
        daily_word = settings.get("daily_word", True)
        return 86400 if daily_word else 3600  # 24 hours or 1 hour

    def run_active(
        self,
        display_controller,
        settings: dict[str, Any],
        device_config: dict[str, Any],
        stop_event,
        plugin_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Run the word display with daily refresh.

        Refreshes every 24 hours to show the next day's word.
        If daily_word is False, refreshes every hour with a new random word.
        """
        refresh_interval = self.get_refresh_interval(settings)

        self.logger.info(f"Word of the Day starting with {refresh_interval}s refresh interval")

        while not stop_event.is_set():
            try:
                image = self.generate_image(settings, device_config)
                if image:
                    display_controller.display_image(image, plugin_info)
                    self.logger.debug("Word of the Day display updated")
            except Exception as e:
                self.logger.error(f"Failed to update word display: {e}")

            stop_event.wait(timeout=refresh_interval)

        self.logger.info("Word of the Day stopped")

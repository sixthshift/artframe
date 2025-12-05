"""
Word of the Day plugin for Artframe.

Displays vocabulary words with definitions, pronunciation, and examples.
"""

import random
from datetime import datetime
from typing import Any, Optional, Union

from PIL import Image, ImageDraw, ImageFont

from artframe.plugins.base_plugin import BasePlugin

# Embedded vocabulary database
# Format: (word, pronunciation, part_of_speech, definition, example)
VOCABULARY_DATABASE = {
    "easy": [
        (
            "Eloquent",
            "EL-uh-kwent",
            "adjective",
            "Fluent or persuasive in speaking or writing",
            "She gave an eloquent speech that moved everyone in the audience.",
        ),
        (
            "Benevolent",
            "buh-NEV-uh-lent",
            "adjective",
            "Well-meaning and kindly",
            "The benevolent old man donated millions to charity.",
        ),
        (
            "Diligent",
            "DIL-i-jent",
            "adjective",
            "Having or showing care in one's work or duties",
            "She was a diligent student who always completed her homework.",
        ),
        (
            "Humble",
            "HUM-bul",
            "adjective",
            "Having or showing a modest estimate of one's importance",
            "Despite his success, he remained humble and approachable.",
        ),
        (
            "Serene",
            "suh-REEN",
            "adjective",
            "Calm, peaceful, and untroubled",
            "The lake was serene in the early morning light.",
        ),
        (
            "Vivid",
            "VIV-id",
            "adjective",
            "Producing powerful feelings or strong images in the mind",
            "She had vivid memories of her childhood home.",
        ),
        (
            "Candid",
            "KAN-did",
            "adjective",
            "Truthful and straightforward; frank",
            "I appreciate your candid feedback on my work.",
        ),
        (
            "Novel",
            "NOV-ul",
            "adjective",
            "New or unusual in an interesting way",
            "The company introduced a novel approach to customer service.",
        ),
        (
            "Zealous",
            "ZEL-us",
            "adjective",
            "Having or showing zeal; fervent",
            "He was zealous in his pursuit of excellence.",
        ),
        (
            "Lucid",
            "LOO-sid",
            "adjective",
            "Expressed clearly; easy to understand",
            "Her lucid explanation made the complex topic simple.",
        ),
    ],
    "medium": [
        (
            "Serendipity",
            "ser-en-DIP-i-tee",
            "noun",
            "The occurrence of events by chance in a happy way",
            "It was pure serendipity that we met at the coffee shop.",
        ),
        (
            "Ephemeral",
            "ih-FEM-er-ul",
            "adjective",
            "Lasting for a very short time",
            "The beauty of cherry blossoms is ephemeral, lasting only a few weeks.",
        ),
        (
            "Juxtapose",
            "JUK-stuh-poze",
            "verb",
            "To place close together for contrasting effect",
            "The artist juxtaposed light and dark colors in the painting.",
        ),
        (
            "Pragmatic",
            "prag-MAT-ik",
            "adjective",
            "Dealing with things sensibly and realistically",
            "She took a pragmatic approach to solving the budget crisis.",
        ),
        (
            "Ubiquitous",
            "yoo-BIK-wi-tus",
            "adjective",
            "Present, appearing, or found everywhere",
            "Smartphones have become ubiquitous in modern society.",
        ),
        (
            "Ameliorate",
            "uh-MEEL-yuh-rayt",
            "verb",
            "To make something bad or unsatisfactory better",
            "The new policy helped ameliorate working conditions.",
        ),
        (
            "Plethora",
            "PLETH-er-uh",
            "noun",
            "An excess or overabundance of something",
            "The buffet offered a plethora of delicious dishes.",
        ),
        (
            "Conundrum",
            "kuh-NUN-drum",
            "noun",
            "A confusing and difficult problem or question",
            "Climate change presents a serious conundrum for policymakers.",
        ),
        (
            "Penchant",
            "PEN-chunt",
            "noun",
            "A strong or habitual liking for something",
            "She has a penchant for collecting vintage books.",
        ),
        (
            "Fortuitous",
            "for-TOO-i-tus",
            "adjective",
            "Happening by chance, especially in a lucky way",
            "Our fortuitous meeting led to a lifelong friendship.",
        ),
    ],
    "hard": [
        (
            "Obfuscate",
            "OB-fuh-skayt",
            "verb",
            "To deliberately make something unclear or difficult to understand",
            "The politician tried to obfuscate the issue with technical jargon.",
        ),
        (
            "Perspicacious",
            "pur-spi-KAY-shus",
            "adjective",
            "Having a ready insight into things; shrewd",
            "Her perspicacious analysis revealed the hidden problems.",
        ),
        (
            "Sanguine",
            "SANG-gwin",
            "adjective",
            "Optimistic or positive, especially in difficult situations",
            "Despite setbacks, she remained sanguine about the project's success.",
        ),
        (
            "Recalcitrant",
            "ri-KAL-si-trunt",
            "adjective",
            "Having an obstinately uncooperative attitude",
            "The recalcitrant committee member refused to compromise.",
        ),
        (
            "Erudite",
            "ER-yoo-dite",
            "adjective",
            "Having or showing great knowledge or learning",
            "The erudite professor could discuss any topic with ease.",
        ),
        (
            "Ineffable",
            "in-EF-uh-bul",
            "adjective",
            "Too great or extreme to be expressed in words",
            "The beauty of the sunset was ineffable.",
        ),
        (
            "Vicarious",
            "vy-KAIR-ee-us",
            "adjective",
            "Experienced in the imagination through another person",
            "She lived vicariously through her children's adventures.",
        ),
        (
            "Ebullient",
            "ih-BUL-yent",
            "adjective",
            "Cheerful and full of energy",
            "His ebullient personality made him popular at parties.",
        ),
        (
            "Magnanimous",
            "mag-NAN-uh-mus",
            "adjective",
            "Generous or forgiving, especially toward a rival",
            "The champion was magnanimous in victory, praising his opponent.",
        ),
        (
            "Sagacious",
            "suh-GAY-shus",
            "adjective",
            "Having or showing keen mental discernment and good judgment",
            "The CEO's sagacious decisions saved the company from bankruptcy.",
        ),
    ],
}


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
        # Validate difficulty
        difficulty = settings.get("difficulty", "medium")
        if difficulty not in ["easy", "medium", "hard", "random"]:
            return False, "Difficulty must be 'easy', 'medium', 'hard', or 'random'"

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
            difficulty = settings.get("difficulty", "medium")
            font_size = settings.get("font_size", "medium")
            background_color = settings.get("background_color", "#FFFFFF")
            text_color = settings.get("text_color", "#000000")
            accent_color = settings.get("accent_color", "#4CAF50")
            show_pronunciation = settings.get("show_pronunciation", True)
            show_example = settings.get("show_example", True)
            daily_word = settings.get("daily_word", True)

            # Create image
            image = Image.new("RGB", (width, height), background_color)
            draw = ImageDraw.Draw(image)

            # Select word
            word, pronunciation, pos, definition, example = self._select_word(
                difficulty, daily_word
            )

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

            # Pronunciation
            if show_pronunciation:
                pronunciation_text = f"/{pronunciation}/"
                draw.text((margin, y), pronunciation_text, fill=accent_color, font=body_font)
                y += self._get_line_height(body_font) + 5

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

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate word image: {e}", exc_info=True)
            return self._create_error_image(str(e), device_config)

    def _select_word(self, difficulty: str, daily: bool) -> tuple[str, str, str, str, str]:
        """
        Select a word from the database.

        Args:
            difficulty: Word difficulty level
            daily: If True, same word for the whole day

        Returns:
            Tuple of (word, pronunciation, part_of_speech, definition, example)
        """
        # If random difficulty, pick a random difficulty first
        if difficulty == "random":
            difficulty = random.choice(list(VOCABULARY_DATABASE.keys()))

        words = VOCABULARY_DATABASE[difficulty]

        if daily:
            # Use day of year as seed for consistency throughout the day
            day_of_year = datetime.now().timetuple().tm_yday
            random.seed(day_of_year + hash(difficulty))
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

    def get_cache_key(self, settings: dict[str, Any]) -> str:
        """
        Generate cache key for word content.

        If daily_word is True, cache per day.
        Otherwise, generate unique key each time.
        """
        daily_word = settings.get("daily_word", True)
        difficulty = settings.get("difficulty", "medium")

        if daily_word:
            # Cache per day
            today = datetime.now().strftime("%Y%m%d")
            return f"word_{difficulty}_{today}"
        else:
            # Don't cache (new word each time)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"word_{difficulty}_{now}"

    def get_cache_ttl(self, settings: dict[str, Any]) -> int:
        """
        Get cache time-to-live in seconds.

        If daily_word is True, cache for 24 hours.
        Otherwise, don't cache.
        """
        daily_word = settings.get("daily_word", True)
        return 86400 if daily_word else 0  # 24 hours or 0

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
        # Use cache_ttl as refresh interval, minimum 1 hour
        refresh_interval = self.get_cache_ttl(settings)
        if refresh_interval <= 0:
            refresh_interval = 3600  # 1 hour default for random words

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

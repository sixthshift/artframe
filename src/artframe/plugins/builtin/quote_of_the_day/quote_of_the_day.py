"""
Quote of the Day plugin for Artframe.

Displays inspirational and thought-provoking quotes.
"""

import random
from datetime import datetime
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap

from artframe.plugins.base_plugin import BasePlugin


# Embedded quotes database
QUOTES_DATABASE = {
    "inspirational": [
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
        (
            "The future belongs to those who believe in the beauty of their dreams.",
            "Eleanor Roosevelt",
        ),
        ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
        ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
        ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
        ("The only impossible journey is the one you never begin.", "Tony Robbins"),
        ("Life is what happens when you're busy making other plans.", "John Lennon"),
        (
            "The best time to plant a tree was 20 years ago. The second best time is now.",
            "Chinese Proverb",
        ),
        ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
    ],
    "wisdom": [
        ("The only true wisdom is in knowing you know nothing.", "Socrates"),
        ("The unexamined life is not worth living.", "Socrates"),
        ("I think, therefore I am.", "René Descartes"),
        (
            "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.",
            "Ralph Waldo Emerson",
        ),
        ("The only way out is through.", "Robert Frost"),
        (
            "We are what we repeatedly do. Excellence, then, is not an act, but a habit.",
            "Aristotle",
        ),
        ("The mind is everything. What you think you become.", "Buddha"),
        (
            "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe.",
            "Albert Einstein",
        ),
        ("Be kind, for everyone you meet is fighting a hard battle.", "Plato"),
        (
            "In the midst of winter, I found there was, within me, an invincible summer.",
            "Albert Camus",
        ),
    ],
    "funny": [
        ("I'm not superstitious, but I am a little stitious.", "Michael Scott"),
        ("The road to success is dotted with many tempting parking spaces.", "Will Rogers"),
        (
            "I find television very educating. Every time somebody turns on the set, I go into the other room and read a book.",
            "Groucho Marx",
        ),
        (
            "By working faithfully eight hours a day you may eventually get to be boss and work twelve hours a day.",
            "Robert Frost",
        ),
        (
            "The difference between genius and stupidity is that genius has its limits.",
            "Albert Einstein",
        ),
        (
            "If you think you are too small to make a difference, try sleeping with a mosquito.",
            "Dalai Lama",
        ),
        (
            "The trouble with having an open mind, of course, is that people will insist on coming along and trying to put things in it.",
            "Terry Pratchett",
        ),
        (
            "Age is an issue of mind over matter. If you don't mind, it doesn't matter.",
            "Mark Twain",
        ),
        ("Life is hard. After all, it kills you.", "Katharine Hepburn"),
        (
            "Always remember that you are absolutely unique. Just like everyone else.",
            "Margaret Mead",
        ),
    ],
    "technology": [
        (
            "Any sufficiently advanced technology is indistinguishable from magic.",
            "Arthur C. Clarke",
        ),
        (
            "The advance of technology is based on making it fit in so that you don't really even notice it, so it's part of everyday life.",
            "Bill Gates",
        ),
        ("Technology is best when it brings people together.", "Matt Mullenweg"),
        ("The great myth of our times is that technology is communication.", "Libby Larsen"),
        (
            "It has become appallingly obvious that our technology has exceeded our humanity.",
            "Albert Einstein",
        ),
        ("The real problem is not whether machines think but whether men do.", "B.F. Skinner"),
        (
            "We are stuck with technology when what we really want is just stuff that works.",
            "Douglas Adams",
        ),
        ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
        (
            "First we thought the PC was a calculator. Then we found out how to turn numbers into letters with ASCII — and we thought it was a typewriter.",
            "Steve Jobs",
        ),
        (
            "The Internet is becoming the town square for the global village of tomorrow.",
            "Bill Gates",
        ),
    ],
}


class QuoteOfTheDay(BasePlugin):
    """
    Display inspirational quotes.

    Shows a random quote based on category, with proper text wrapping
    and attribution.
    """

    def __init__(self):
        """Initialize Quote of the Day plugin."""
        super().__init__()

    def validate_settings(self, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate plugin settings.

        Args:
            settings: Plugin settings dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate category
        category = settings.get("category", "inspirational")
        if category not in ["inspirational", "wisdom", "funny", "technology", "random"]:
            return (
                False,
                "Category must be 'inspirational', 'wisdom', 'funny', 'technology', or 'random'",
            )

        # Validate font size
        font_size = settings.get("font_size", "medium")
        if font_size not in ["small", "medium", "large"]:
            return False, "Font size must be 'small', 'medium', or 'large'"

        return True, ""

    def generate_image(
        self, settings: Dict[str, Any], device_config: Dict[str, Any]
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

    def _select_quote(self, category: str, daily: bool) -> Tuple[str, str]:
        """
        Select a quote from the database.

        Args:
            category: Quote category
            daily: If True, same quote for the whole day

        Returns:
            Tuple of (quote_text, author)
        """
        # If random category, pick a random category first
        if category == "random":
            category = random.choice(list(QUOTES_DATABASE.keys()))

        quotes = QUOTES_DATABASE[category]

        if daily:
            # Use day of year as seed for consistency throughout the day
            day_of_year = datetime.now().timetuple().tm_yday
            random.seed(day_of_year + hash(category))
            quote = random.choice(quotes)
            random.seed()  # Reset seed
        else:
            # Truly random
            quote = random.choice(quotes)

        return quote

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw
    ) -> List[str]:
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
        current_line = []

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

    def _get_line_height(self, font: ImageFont.FreeTypeFont) -> int:
        """Get the line height for a font."""
        try:
            return font.size + 10  # Font size + spacing
        except:
            return 30  # Default fallback

    def _get_font(self, size: str, text_type: str) -> ImageFont.FreeTypeFont:
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
                except:
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
        except:
            font = None

        text = f"Quote Error:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    def get_cache_key(self, settings: Dict[str, Any]) -> str:
        """
        Generate cache key for quote content.

        If daily_quote is True, cache per day.
        Otherwise, generate unique key each time (no caching).
        """
        daily_quote = settings.get("daily_quote", True)
        category = settings.get("category", "inspirational")

        if daily_quote:
            # Cache per day
            today = datetime.now().strftime("%Y%m%d")
            return f"quote_{category}_{today}"
        else:
            # Don't cache (new quote each time)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"quote_{category}_{now}"

    def get_cache_ttl(self, settings: Dict[str, Any]) -> int:
        """
        Get cache time-to-live in seconds.

        If daily_quote is True, cache for 24 hours.
        Otherwise, cache for 0 seconds (regenerate each time).
        """
        daily_quote = settings.get("daily_quote", True)
        return 86400 if daily_quote else 0  # 24 hours or 0

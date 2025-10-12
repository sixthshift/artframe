"""
Display controller for managing e-ink display operations.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

from .drivers import DriverInterface
from ..models import StyledImage, DisplayState


class DisplayController:
    """Controls display operations and manages display state."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize display controller.

        Args:
            config: Display configuration
        """
        self.config = config
        self.driver = self._create_driver()
        self.state = DisplayState(
            current_image_id=None,
            last_refresh=None,
            next_scheduled=None,
            error_count=0,
            status="idle",
        )

    def _create_driver(self) -> DriverInterface:
        """Create appropriate display driver based on configuration."""
        driver_name = self.config.get("driver", "mock")
        driver_config = self.config.get("config", {})

        if driver_name == "spectra6":
            from .drivers import Spectra6Driver

            return Spectra6Driver(driver_config)
        elif driver_name == "mock":
            from .drivers import MockDriver

            return MockDriver(driver_config)
        else:
            raise ValueError(f"Unknown display driver: {driver_name}")

    def initialize(self) -> None:
        """Initialize the display hardware."""
        try:
            self.driver.initialize()
            self.state.status = "ready"
            self.state.error_count = 0
        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            raise DisplayError(f"Failed to initialize display: {e}")

    def display_styled_image(self, styled_image: StyledImage, show_metadata: bool = True) -> None:
        """
        Display a styled image with optional metadata overlay.

        Args:
            styled_image: StyledImage to display
            show_metadata: Whether to show metadata overlay
        """
        try:
            self.state.status = "updating"

            # Load image
            image = Image.open(styled_image.styled_path)

            # Add metadata overlay if requested
            if show_metadata and self.config.get("show_metadata", True):
                image = self._add_metadata_overlay(image, styled_image)

            # Display image
            self.driver.display_image(image)

            # Update state
            self.state.current_image_id = styled_image.original_photo_id
            self.state.last_refresh = datetime.now()
            self.state.status = "idle"
            self.state.error_count = 0

        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            raise DisplayError(f"Failed to display image: {e}")

    def display_image_file(self, image_path: Path, title: Optional[str] = None) -> None:
        """
        Display an image file directly.

        Args:
            image_path: Path to image file
            title: Optional title to display
        """
        try:
            self.state.status = "updating"

            # Load image
            image = Image.open(image_path)

            # Add title overlay if provided
            if title:
                image = self._add_title_overlay(image, title)

            # Display image
            self.driver.display_image(image)

            # Update state
            self.state.current_image_id = str(image_path)
            self.state.last_refresh = datetime.now()
            self.state.status = "idle"
            self.state.error_count = 0

        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            raise DisplayError(f"Failed to display image file: {e}")

    def clear_display(self) -> None:
        """Clear the display."""
        try:
            self.state.status = "updating"
            self.driver.clear_display()

            self.state.current_image_id = None
            self.state.last_refresh = datetime.now()
            self.state.status = "idle"
            self.state.error_count = 0

        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            raise DisplayError(f"Failed to clear display: {e}")

    def show_error_message(self, message: str) -> None:
        """
        Display an error message on the screen.

        Args:
            message: Error message to display
        """
        try:
            display_size = self.driver.get_display_size()
            image = Image.new("L", display_size, 255)  # White background
            draw = ImageDraw.Draw(image)

            # Try to use a default font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Calculate text position
            text_bbox = draw.textbbox((0, 0), message, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = (display_size[0] - text_width) // 2
            y = (display_size[1] - text_height) // 2

            # Draw text
            draw.text((x, y), message, fill=0, font=font)

            self.driver.display_image(image)

        except Exception as e:
            # If we can't even display an error message, just clear the display
            try:
                self.driver.clear_display()
            except Exception:
                pass

    def sleep(self) -> None:
        """Put display into low power mode."""
        try:
            self.driver.sleep()
            self.state.status = "sleeping"
        except Exception as e:
            raise DisplayError(f"Failed to put display to sleep: {e}")

    def wake(self) -> None:
        """Wake display from low power mode."""
        try:
            self.driver.wake()
            self.state.status = "idle"
        except Exception as e:
            raise DisplayError(f"Failed to wake display: {e}")

    def get_display_size(self) -> tuple[int, int]:
        """Get display dimensions."""
        return self.driver.get_display_size()

    def get_state(self) -> DisplayState:
        """Get current display state."""
        return self.state

    def _add_metadata_overlay(self, image: Image.Image, styled_image: StyledImage) -> Image.Image:
        """Add metadata overlay to image."""
        try:
            # Create a copy to avoid modifying original
            overlay_image = image.copy()
            draw = ImageDraw.Draw(overlay_image)

            # Try to use a small font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Prepare metadata text
            date_str = styled_image.created_at.strftime("%Y-%m-%d")
            style_str = styled_image.style_name.title()
            metadata_text = f"{date_str} • {style_str}"

            # Calculate position (bottom right)
            text_bbox = draw.textbbox((0, 0), metadata_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = image.width - text_width - 10
            y = image.height - text_height - 10

            # Draw semi-transparent background
            padding = 5
            bg_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding,
            ]
            draw.rectangle(bg_coords, fill=255, outline=0)

            # Draw text
            draw.text((x, y), metadata_text, fill=0, font=font)

            return overlay_image

        except Exception:
            # If overlay fails, return original image
            return image

    def _add_title_overlay(self, image: Image.Image, title: str) -> Image.Image:
        """Add title overlay to image."""
        try:
            overlay_image = image.copy()
            draw = ImageDraw.Draw(overlay_image)

            # Try to use a larger font for title
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
                )
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Calculate position (top center)
            text_bbox = draw.textbbox((0, 0), title, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = (image.width - text_width) // 2
            y = 10

            # Draw background
            padding = 8
            bg_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding,
            ]
            draw.rectangle(bg_coords, fill=255, outline=0)

            # Draw text
            draw.text((x, y), title, fill=0, font=font)

            return overlay_image

        except Exception:
            return image


class DisplayError(Exception):
    """Exception raised by display operations."""

    pass

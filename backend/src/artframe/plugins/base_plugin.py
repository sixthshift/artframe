"""
Base plugin class for Artframe content plugins.

All plugins must inherit from BasePlugin and implement generate_image().
Inspired by InkyPi's plugin system with Artframe enhancements.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image


class BasePlugin(ABC):
    """
    Abstract base class for all Artframe plugins.

    Plugins generate content images for display on e-ink screens.
    Each plugin implements generate_image() which receives settings
    and device configuration, and returns a PIL Image.

    Example:
        class MyPlugin(BasePlugin):
            def generate_image(self, settings, device_config):
                width = device_config['width']
                height = device_config['height']

                image = Image.new('RGB', (width, height), 'white')
                # ... generate content ...
                return image
    """

    def __init__(self):
        """Initialize plugin with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._plugin_dir = None

    @abstractmethod
    def generate_image(
        self, settings: Dict[str, Any], device_config: Dict[str, Any]
    ) -> Image.Image:
        """
        Generate content image for display.

        This is the main method that must be implemented by all plugins.
        It receives the plugin's settings and device configuration,
        and must return a PIL Image ready for display.

        Args:
            settings: Dictionary of plugin instance settings
                Example: {
                    'api_key': 'abc123',
                    'refresh_interval': 30,
                    'primary_color': '#000000'
                }

            device_config: Dictionary of display device configuration
                Example: {
                    'width': 600,
                    'height': 448,
                    'rotation': 0,
                    'color_mode': 'grayscale'
                }

        Returns:
            PIL.Image: Generated image optimized for the display

        Raises:
            RuntimeError: If image generation fails
            ValueError: If settings are invalid
        """
        raise NotImplementedError("Plugins must implement generate_image()")

    def get_plugin_directory(self) -> Path:
        """
        Get the plugin's directory path.

        Useful for accessing plugin assets like templates, fonts, or images.

        Returns:
            Path: Absolute path to plugin directory
        """
        if self._plugin_dir is None:
            # Get the directory of the plugin's Python file
            import inspect

            plugin_file = Path(inspect.getfile(self.__class__))
            self._plugin_dir = plugin_file.parent

        return self._plugin_dir

    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate plugin settings.

        Override this method to add custom validation logic.
        Default implementation always returns True.

        Args:
            settings: Settings dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if settings are valid
            - error_message: Empty string if valid, error description if invalid

        Example:
            def validate_settings(self, settings):
                if not settings.get('api_key'):
                    return False, "API key is required"
                if settings.get('refresh_interval', 0) < 1:
                    return False, "Refresh interval must be at least 1 minute"
                return True, ""
        """
        return True, ""

    def get_cache_key(self, settings: Dict[str, Any]) -> Optional[str]:
        """
        Generate cache key for this content.

        Override to enable intelligent caching. Return None to disable caching.

        Args:
            settings: Plugin instance settings

        Returns:
            str: Unique cache key, or None to disable caching

        Example:
            def get_cache_key(self, settings):
                # Cache per location and date
                location = settings.get('location', 'default')
                date = datetime.now().strftime('%Y-%m-%d')
                return f"weather_{location}_{date}"
        """
        return None  # No caching by default

    def get_cache_ttl(self, settings: Dict[str, Any]) -> int:
        """
        Get cache time-to-live in seconds.

        Override to specify how long cached content remains valid.

        Args:
            settings: Plugin instance settings

        Returns:
            int: Seconds before cache expires (0 = no caching)

        Example:
            def get_cache_ttl(self, settings):
                return 1800  # Cache for 30 minutes
        """
        return 0  # No caching by default

    def on_enable(self, settings: Dict[str, Any]) -> None:
        """
        Called when plugin instance is enabled.

        Override to perform one-time setup like:
        - Initialize API connections
        - Validate credentials
        - Create temporary directories

        Args:
            settings: Plugin instance settings

        Example:
            def on_enable(self, settings):
                self.api_client = APIClient(settings['api_key'])
                self.api_client.connect()
        """
        pass

    def on_disable(self, settings: Dict[str, Any]) -> None:
        """
        Called when plugin instance is disabled.

        Override to perform cleanup like:
        - Close API connections
        - Delete temporary files
        - Save state

        Args:
            settings: Plugin instance settings

        Example:
            def on_disable(self, settings):
                if hasattr(self, 'api_client'):
                    self.api_client.disconnect()
        """
        pass

    def run_active(
        self,
        display_controller,
        settings: Dict[str, Any],
        device_config: Dict[str, Any],
        stop_event,
    ) -> None:
        """
        Run while this plugin is the active content source.

        Override to manage your own refresh loop. The scheduler will call
        this when your plugin becomes active and expects it to keep running
        until stop_event is set.

        Default implementation: generates image once and waits for stop.
        Plugins that need periodic updates (like Clock) should override this.

        Args:
            display_controller: DisplayController to push images to
            settings: Plugin instance settings
            device_config: Display device configuration
            stop_event: threading.Event - set when plugin should stop

        Example (Clock plugin):
            def run_active(self, display_controller, settings, device_config, stop_event):
                while not stop_event.is_set():
                    image = self.generate_image(settings, device_config)
                    display_controller.display_image(image)
                    # Wait 60 seconds or until stopped
                    stop_event.wait(timeout=60)
        """
        # Default: generate once and wait
        try:
            image = self.generate_image(settings, device_config)
            if image:
                display_controller.display_image(image)
        except Exception as e:
            self.logger.error(f"Failed to generate/display image: {e}")

        # Wait until stopped
        stop_event.wait()

    def on_settings_change(
        self, old_settings: Dict[str, Any], new_settings: Dict[str, Any]
    ) -> None:
        """
        Called when instance settings are updated.

        Override to handle settings changes without full restart.

        Args:
            old_settings: Previous settings
            new_settings: Updated settings

        Example:
            def on_settings_change(self, old_settings, new_settings):
                if old_settings.get('api_key') != new_settings.get('api_key'):
                    # API key changed, reconnect
                    self.api_client.reconnect(new_settings['api_key'])
        """
        pass

    def get_asset_path(self, filename: str) -> Path:
        """
        Get path to a plugin asset file.

        Convenience method for accessing plugin resources.

        Args:
            filename: Asset filename (e.g., 'logo.png', 'template.html')

        Returns:
            Path: Absolute path to asset file

        Example:
            logo_path = self.get_asset_path('logo.png')
            with Image.open(logo_path) as logo:
                image.paste(logo, (10, 10))
        """
        return self.get_plugin_directory() / filename

    def __repr__(self) -> str:
        """String representation of plugin."""
        return f"<{self.__class__.__name__}>"

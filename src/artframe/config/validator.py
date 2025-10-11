"""
Configuration validator for Artframe.
"""

from typing import Dict, Any, List
from pathlib import Path


class ConfigValidator:
    """Validates Artframe configuration."""

    REQUIRED_KEYS = [
        'artframe.source.provider',
        'artframe.style.provider',
        'artframe.display.driver',
        'artframe.storage.directory'
    ]

    VALID_SOURCE_PROVIDERS = ['immich', 'none']
    VALID_STYLE_PROVIDERS = ['nanobanana', 'none']
    VALID_DISPLAY_DRIVERS = ['spectra6', 'mock']

    def validate(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration dictionary.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        self._validate_structure(config)
        self._validate_source_config(config)
        self._validate_style_config(config)
        self._validate_display_config(config)
        self._validate_storage_config(config)
        self._validate_schedule_config(config)

    def _validate_structure(self, config: Dict[str, Any]) -> None:
        """Validate basic configuration structure."""
        if 'artframe' not in config:
            raise ValueError("Configuration must have 'artframe' root key")

        artframe_config = config['artframe']

        # Check required sections exist
        required_sections = ['source', 'style', 'display', 'storage']
        for section in required_sections:
            if section not in artframe_config:
                raise ValueError(f"Required section 'artframe.{section}' missing")

    def _validate_source_config(self, config: Dict[str, Any]) -> None:
        """Validate source configuration."""
        source_config = config['artframe']['source']

        if 'provider' not in source_config:
            raise ValueError("Source provider must be specified")

        provider = source_config['provider']
        if provider not in self.VALID_SOURCE_PROVIDERS:
            raise ValueError(f"Invalid source provider '{provider}'. Valid options: {self.VALID_SOURCE_PROVIDERS}")

        if 'config' not in source_config:
            raise ValueError("Source config section is required")

        # Provider-specific validation
        if provider == 'immich':
            self._validate_immich_config(source_config['config'])

    def _validate_immich_config(self, config: Dict[str, Any]) -> None:
        """Validate Immich-specific configuration."""
        required_keys = ['server_url']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Immich config missing required key: {key}")

        # Validate URL format
        server_url = config['server_url']
        if server_url and not server_url.startswith(('http://', 'https://')):
            raise ValueError("Immich server_url must start with http:// or https://")

    def _validate_style_config(self, config: Dict[str, Any]) -> None:
        """Validate style configuration."""
        style_config = config['artframe']['style']

        if 'provider' not in style_config:
            raise ValueError("Style provider must be specified")

        provider = style_config['provider']
        if provider not in self.VALID_STYLE_PROVIDERS:
            raise ValueError(f"Invalid style provider '{provider}'. Valid options: {self.VALID_STYLE_PROVIDERS}")

        if 'config' not in style_config:
            raise ValueError("Style config section is required")

        # Provider-specific validation
        if provider == 'nanobanana':
            self._validate_nanobanana_config(style_config['config'])

    def _validate_nanobanana_config(self, config: Dict[str, Any]) -> None:
        """Validate NanoBanana-specific configuration."""
        required_keys = ['api_url', 'styles']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"NanoBanana config missing required key: {key}")

        # Validate styles list
        styles = config['styles']
        if not isinstance(styles, list) or not styles:
            raise ValueError("NanoBanana styles must be a non-empty list")

        # Validate each style entry
        for i, style in enumerate(styles):
            # Support both old format (string) and new format (dict with name and prompt)
            if isinstance(style, str):
                # Old format - just a style name
                continue
            elif isinstance(style, dict):
                # New format - object with name and prompt
                if 'name' not in style:
                    raise ValueError(f"Style {i} missing 'name' field")
                if 'prompt' not in style:
                    raise ValueError(f"Style {i} missing 'prompt' field")
                if not isinstance(style['name'], str) or not style['name'].strip():
                    raise ValueError(f"Style {i} has invalid name")
                if not isinstance(style['prompt'], str) or not style['prompt'].strip():
                    raise ValueError(f"Style {i} has invalid prompt")
            else:
                raise ValueError(f"Invalid style format at index {i}. Must be string or object with name/prompt")

        # Validate rotation strategy
        if 'rotation' in config:
            valid_rotations = ['daily', 'random', 'sequential']
            if config['rotation'] not in valid_rotations:
                raise ValueError(f"Invalid rotation strategy. Valid options: {valid_rotations}")

    def _validate_display_config(self, config: Dict[str, Any]) -> None:
        """Validate display configuration."""
        display_config = config['artframe']['display']

        if 'driver' not in display_config:
            raise ValueError("Display driver must be specified")

        driver = display_config['driver']
        if driver not in self.VALID_DISPLAY_DRIVERS:
            raise ValueError(f"Invalid display driver '{driver}'. Valid options: {self.VALID_DISPLAY_DRIVERS}")

        if 'config' not in display_config:
            raise ValueError("Display config section is required")

        # Driver-specific validation
        if driver == 'spectra6':
            self._validate_spectra6_config(display_config['config'])

    def _validate_spectra6_config(self, config: Dict[str, Any]) -> None:
        """Validate Spectra6-specific configuration."""
        if 'gpio_pins' in config:
            gpio_config = config['gpio_pins']
            required_pins = ['busy', 'reset', 'dc', 'cs']
            for pin in required_pins:
                if pin not in gpio_config:
                    raise ValueError(f"Spectra6 GPIO config missing pin: {pin}")

                pin_value = gpio_config[pin]
                if not isinstance(pin_value, int) or pin_value < 0 or pin_value > 40:
                    raise ValueError(f"Invalid GPIO pin number for {pin}: {pin_value}")

        if 'rotation' in config:
            valid_rotations = [0, 90, 180, 270]
            if config['rotation'] not in valid_rotations:
                raise ValueError(f"Invalid display rotation. Valid options: {valid_rotations}")

    def _validate_storage_config(self, config: Dict[str, Any]) -> None:
        """Validate storage configuration."""
        storage_config = config['artframe']['storage']

        if 'directory' not in storage_config:
            raise ValueError("Storage directory must be specified")

    def _validate_schedule_config(self, config: Dict[str, Any]) -> None:
        """Validate schedule configuration."""
        if 'schedule' not in config['artframe']:
            return  # Schedule is optional

        schedule_config = config['artframe']['schedule']

        if 'update_time' in schedule_config:
            time_str = schedule_config['update_time']
            if not self._is_valid_time_format(time_str):
                raise ValueError(f"Invalid update_time format: {time_str}. Use HH:MM format")

    def _is_valid_time_format(self, time_str: str) -> bool:
        """Check if time string is in HH:MM format."""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False

            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False
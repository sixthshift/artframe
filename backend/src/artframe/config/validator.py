"""
Configuration validator for Artframe.

Validates system-level configuration only. Plugin-specific settings
are validated by the plugins themselves.
"""

from typing import Any


class ConfigValidator:
    """Validates Artframe system configuration."""

    VALID_DISPLAY_DRIVERS = ["waveshare", "mock"]
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    VALID_ROTATIONS = [0, 90, 180, 270]

    def validate(self, config: dict[str, Any]) -> None:
        """
        Validate system configuration.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid
        """
        errors: list[str] = []

        # Root structure
        if "artframe" not in config:
            raise ValueError("Configuration must have 'artframe' root key")

        artframe = config["artframe"]

        # Validate each section
        errors.extend(self._validate_display(artframe))
        errors.extend(self._validate_storage(artframe))
        errors.extend(self._validate_logging(artframe))
        errors.extend(self._validate_web(artframe))
        errors.extend(self._validate_scheduler(artframe))

        if errors:
            raise ValueError("Invalid configuration:\n  - " + "\n  - ".join(errors))

    def _validate_display(self, artframe: dict[str, Any]) -> list[str]:
        """Validate display configuration."""
        errors = []

        if "display" not in artframe:
            return ["Required section 'display' is missing"]

        display = artframe["display"]

        # Driver is required
        if "driver" not in display:
            errors.append("display.driver is required")
        elif display["driver"] not in self.VALID_DISPLAY_DRIVERS:
            errors.append(f"display.driver must be one of: {self.VALID_DISPLAY_DRIVERS}")

        # Config section is required
        if "config" not in display:
            errors.append("display.config is required")
        else:
            config = display["config"]

            # Width and height
            if "width" in config:
                if not isinstance(config["width"], int) or config["width"] <= 0:
                    errors.append("display.config.width must be a positive integer")

            if "height" in config:
                if not isinstance(config["height"], int) or config["height"] <= 0:
                    errors.append("display.config.height must be a positive integer")

            # Rotation
            if "rotation" in config:
                if config["rotation"] not in self.VALID_ROTATIONS:
                    errors.append(f"display.config.rotation must be one of: {self.VALID_ROTATIONS}")

            # GPIO pins (for waveshare)
            if "gpio_pins" in config:
                errors.extend(self._validate_gpio_pins(config["gpio_pins"]))

        return errors

    def _validate_gpio_pins(self, gpio_pins: dict[str, Any]) -> list[str]:
        """Validate GPIO pin configuration."""
        errors = []
        required_pins = ["busy", "reset", "dc", "cs"]

        for pin_name in required_pins:
            if pin_name not in gpio_pins:
                errors.append(f"display.config.gpio_pins.{pin_name} is required")
            else:
                pin_value = gpio_pins[pin_name]
                if not isinstance(pin_value, int) or pin_value < 0 or pin_value > 40:
                    errors.append(f"display.config.gpio_pins.{pin_name} must be 0-40")

        return errors

    def _validate_storage(self, artframe: dict[str, Any]) -> list[str]:
        """Validate storage configuration."""
        errors = []

        if "storage" not in artframe:
            return ["Required section 'storage' is missing"]

        storage = artframe["storage"]

        # data_dir is required
        if "data_dir" not in storage:
            errors.append("storage.data_dir is required")
        elif not isinstance(storage["data_dir"], str) or not storage["data_dir"].strip():
            errors.append("storage.data_dir must be a non-empty string")

        # cache_dir is optional but must be valid if present
        if "cache_dir" in storage:
            if not isinstance(storage["cache_dir"], str) or not storage["cache_dir"].strip():
                errors.append("storage.cache_dir must be a non-empty string")

        # cache_max_mb
        if "cache_max_mb" in storage:
            if not isinstance(storage["cache_max_mb"], int) or storage["cache_max_mb"] <= 0:
                errors.append("storage.cache_max_mb must be a positive integer")

        # cache_retention_days
        if "cache_retention_days" in storage:
            if (
                not isinstance(storage["cache_retention_days"], int)
                or storage["cache_retention_days"] <= 0
            ):
                errors.append("storage.cache_retention_days must be a positive integer")

        return errors

    def _validate_logging(self, artframe: dict[str, Any]) -> list[str]:
        """Validate logging configuration (optional section)."""
        errors = []

        if "logging" not in artframe:
            return []  # Logging is optional

        logging_config = artframe["logging"]

        # Level
        if "level" in logging_config:
            if logging_config["level"] not in self.VALID_LOG_LEVELS:
                errors.append(f"logging.level must be one of: {self.VALID_LOG_LEVELS}")

        # Dir
        if "dir" in logging_config:
            if not isinstance(logging_config["dir"], str) or not logging_config["dir"].strip():
                errors.append("logging.dir must be a non-empty string")

        # max_size_mb
        if "max_size_mb" in logging_config:
            if (
                not isinstance(logging_config["max_size_mb"], int)
                or logging_config["max_size_mb"] <= 0
            ):
                errors.append("logging.max_size_mb must be a positive integer")

        # backup_count
        if "backup_count" in logging_config:
            if (
                not isinstance(logging_config["backup_count"], int)
                or logging_config["backup_count"] < 0
            ):
                errors.append("logging.backup_count must be a non-negative integer")

        return errors

    def _validate_web(self, artframe: dict[str, Any]) -> list[str]:
        """Validate web server configuration (optional section)."""
        errors = []

        if "web" not in artframe:
            return []  # Web config is optional

        web = artframe["web"]

        # Port
        if "port" in web:
            port = web["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("web.port must be an integer between 1 and 65535")

        # Debug
        if "debug" in web:
            if not isinstance(web["debug"], bool):
                errors.append("web.debug must be a boolean")

        return errors

    def _validate_scheduler(self, artframe: dict[str, Any]) -> list[str]:
        """Validate scheduler configuration (optional section)."""
        errors = []

        if "scheduler" not in artframe:
            return []  # Scheduler config is optional

        scheduler = artframe["scheduler"]

        # Timezone
        if "timezone" in scheduler:
            if not isinstance(scheduler["timezone"], str) or not scheduler["timezone"].strip():
                errors.append("scheduler.timezone must be a non-empty string")

        return errors

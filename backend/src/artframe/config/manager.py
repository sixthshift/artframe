"""
Configuration manager for Artframe.
"""

import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, cast

import yaml

from .validator import ConfigValidator


class ConfigManager:
    """Manages configuration loading, validation, and access."""

    # Default paths (used when not specified in config)
    DEFAULT_DATA_DIR = "~/.artframe/data"
    DEFAULT_CACHE_DIR = "~/.artframe/cache"
    DEFAULT_LOG_DIR = "~/.artframe/logs"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file. Defaults to config/artframe-laptop.yaml
        """
        self.config_path = config_path or Path("config/artframe-laptop.yaml")
        self._config: Dict[str, Any] = {}
        self._observers: List[Callable[[str, Any], None]] = []
        self.validator = ConfigValidator()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f)

            # Expand environment variables
            self._config = self._expand_env_vars(self._config)

            # Validate configuration
            self.validator.validate(self._config)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def _expand_env_vars(self, config: Any) -> Any:
        """Recursively expand environment variables in configuration."""
        if isinstance(config, dict):
            return {key: self._expand_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            def replace_env_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            return re.sub(r"\$\{([^}]+)\}", replace_env_var, config)
        else:
            return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., 'artframe.display.driver')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    # ================================================================
    # Section getters - return raw config sections
    # ================================================================

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration section."""
        return cast(Dict[str, Any], self.get("artframe.display", {}))

    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration section."""
        return cast(Dict[str, Any], self.get("artframe.storage", {}))

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration section."""
        return cast(Dict[str, Any], self.get("artframe.logging", {}))

    def get_web_config(self) -> Dict[str, Any]:
        """Get web server configuration section."""
        return cast(Dict[str, Any], self.get("artframe.web", {}))

    def get_scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler configuration section."""
        return cast(Dict[str, Any], self.get("artframe.scheduler", {}))

    # ================================================================
    # Path getters - return expanded Path objects
    # ================================================================

    def get_data_dir(self) -> Path:
        """Get data directory path (expanded)."""
        storage = self.get_storage_config()
        data_dir = storage.get("data_dir", self.DEFAULT_DATA_DIR)
        return Path(data_dir).expanduser()

    def get_cache_dir(self) -> Path:
        """Get cache directory path (expanded)."""
        storage = self.get_storage_config()
        cache_dir = storage.get("cache_dir", self.DEFAULT_CACHE_DIR)
        return Path(cache_dir).expanduser()

    def get_log_dir(self) -> Path:
        """Get log directory path (expanded)."""
        logging_config = self.get_logging_config()
        log_dir = logging_config.get("dir", self.DEFAULT_LOG_DIR)
        return Path(log_dir).expanduser()

    # ================================================================
    # Convenience getters
    # ================================================================

    def get_display_driver(self) -> str:
        """Get display driver name."""
        return self.get_display_config().get("driver", "mock")

    def get_display_dimensions(self) -> tuple:
        """Get display dimensions as (width, height) tuple."""
        config = self.get_display_config().get("config", {})
        return (config.get("width", 800), config.get("height", 480))

    def get_timezone(self) -> str:
        """Get scheduler timezone."""
        return self.get_scheduler_config().get("timezone", "UTC")

    def get_log_level(self) -> str:
        """Get logging level."""
        return self.get_logging_config().get("level", "INFO")

    def get_web_port(self) -> int:
        """Get web server port."""
        return self.get_web_config().get("port", 8000)

    def get_web_host(self) -> str:
        """Get web server host."""
        return self.get_web_config().get("host", "0.0.0.0")

    # ================================================================
    # Observer pattern for config changes
    # ================================================================

    def add_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Add configuration change observer."""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Remove configuration change observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def reload(self) -> None:
        """Reload configuration from file."""
        old_config = self._config.copy()
        self._load_config()
        self._notify_changes(old_config, self._config)

    def revert_to_file(self) -> None:
        """Revert in-memory configuration to what's saved on disk."""
        self._load_config()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update in-memory configuration (validates but does not save to file).

        Args:
            new_config: New configuration dictionary to merge

        Raises:
            ValueError: If new configuration is invalid
        """
        # Merge new config with existing
        merged = self._deep_merge(self._config.copy(), new_config)

        # Validate merged config
        self.validator.validate(merged)

        # Apply changes
        old_config = self._config.copy()
        self._config = merged
        self._notify_changes(old_config, self._config)

    def save_to_file(self, backup: bool = True) -> None:
        """
        Save current in-memory configuration to file.

        Args:
            backup: If True, create a backup of existing file before saving

        Raises:
            IOError: If file cannot be written
        """
        import shutil
        from datetime import datetime

        if backup and self.config_path.exists():
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_suffix(f".{timestamp}.bak")
            shutil.copy2(self.config_path, backup_path)

        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _notify_changes(
        self, old_config: Dict[str, Any], new_config: Dict[str, Any], prefix: str = ""
    ) -> None:
        """Recursively notify observers of configuration changes."""
        for key, value in new_config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if key not in old_config:
                for observer in self._observers:
                    observer(full_key, value)
            elif old_config[key] != value:
                if isinstance(value, dict) and isinstance(old_config[key], dict):
                    self._notify_changes(old_config[key], value, full_key)
                else:
                    for observer in self._observers:
                        observer(full_key, value)

    @property
    def config(self) -> Dict[str, Any]:
        """Get read-only copy of current configuration."""
        return self._config.copy()

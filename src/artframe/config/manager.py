"""
Configuration manager for Artframe.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from .validator import ConfigValidator


class ConfigManager:
    """Manages configuration loading, validation, and change notifications."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file. Defaults to config/artframe.yaml
        """
        self.config_path = config_path or Path("config/artframe.yaml")
        self._config: Dict[str, Any] = {}
        self._observers: List[Callable[[str, Any], None]] = []
        self.validator = ConfigValidator()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)

            # Validate configuration
            self.validator.validate(self._config)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")


    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., 'artframe.source.provider')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_source_config(self) -> Dict[str, Any]:
        """Get source plugin configuration."""
        return self.get('artframe.source', {})

    def get_style_config(self) -> Dict[str, Any]:
        """Get style plugin configuration."""
        return self.get('artframe.style', {})

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration."""
        return self.get('artframe.display', {})

    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return self.get('artframe.storage', {})

    def get_schedule_config(self) -> Dict[str, Any]:
        """Get schedule configuration."""
        return self.get('artframe.schedule', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('artframe.logging', {})

    def add_observer(self, callback: Callable[[str, Any], None]) -> None:
        """
        Add configuration change observer.

        Args:
            callback: Function called when config changes (key, new_value)
        """
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Remove configuration change observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def reload(self) -> None:
        """Reload configuration from file."""
        old_config = self._config.copy()
        self._load_config()

        # Notify observers of changes
        self._notify_changes(old_config, self._config)

    def _notify_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any], prefix: str = "") -> None:
        """Recursively notify observers of configuration changes."""
        for key, value in new_config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if key not in old_config:
                # New key
                for observer in self._observers:
                    observer(full_key, value)
            elif old_config[key] != value:
                if isinstance(value, dict) and isinstance(old_config[key], dict):
                    # Recursive check for nested dictionaries
                    self._notify_changes(old_config[key], value, full_key)
                else:
                    # Value changed
                    for observer in self._observers:
                        observer(full_key, value)

    def validate_current_config(self) -> bool:
        """
        Validate current configuration.

        Returns:
            bool: True if configuration is valid
        """
        try:
            self.validator.validate(self._config)
            return True
        except ValueError:
            return False

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update in-memory configuration.

        Args:
            new_config: New configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate before updating
        self.validator.validate(new_config)

        # Update in-memory config
        old_config = self._config.copy()
        self._config = new_config

        # Notify observers
        self._notify_changes(old_config, self._config)

    def save_to_file(self, backup: bool = True) -> None:
        """
        Save current in-memory configuration to YAML file.

        Args:
            backup: If True, create backup of existing file

        Raises:
            IOError: If file cannot be written
        """
        # Create backup if requested
        if backup and self.config_path.exists():
            backup_path = self.config_path.with_suffix('.yaml.backup')
            import shutil
            shutil.copy2(self.config_path, backup_path)

        # Write to file
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise IOError(f"Failed to save configuration: {e}")

    def revert_to_file(self) -> None:
        """Revert in-memory config to what's on disk."""
        self._load_config()

    @property
    def config(self) -> Dict[str, Any]:
        """Get read-only copy of current configuration."""
        return self._config.copy()


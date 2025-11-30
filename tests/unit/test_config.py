"""
Unit tests for configuration management.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.artframe.config import ConfigManager, ConfigValidator


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_valid_config(self, sample_config):
        """Test validation of valid configuration."""
        validator = ConfigValidator()
        validator.validate(sample_config)  # Should not raise

    def test_missing_artframe_section(self):
        """Test validation fails when artframe section is missing."""
        validator = ConfigValidator()
        config = {"other": "value"}

        with pytest.raises(ValueError, match="must have 'artframe' root key"):
            validator.validate(config)

    def test_missing_display_section(self):
        """Test validation fails when display section is missing."""
        validator = ConfigValidator()
        config = {"artframe": {"storage": {"data_dir": "/tmp"}}}

        with pytest.raises(ValueError, match="display.*missing"):
            validator.validate(config)

    def test_missing_storage_section(self):
        """Test validation fails when storage section is missing."""
        validator = ConfigValidator()
        config = {"artframe": {"display": {"driver": "mock", "config": {}}}}

        with pytest.raises(ValueError, match="storage.*missing"):
            validator.validate(config)

    def test_missing_data_dir(self):
        """Test validation fails when data_dir is missing."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {"driver": "mock", "config": {}},
                "storage": {"cache_dir": "/tmp"},  # Missing data_dir
            }
        }

        with pytest.raises(ValueError, match="data_dir is required"):
            validator.validate(config)

    def test_invalid_display_driver(self):
        """Test validation fails with invalid display driver."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {"driver": "invalid", "config": {}},
                "storage": {"data_dir": "/tmp"},
            }
        }

        with pytest.raises(ValueError, match="display.driver must be one of"):
            validator.validate(config)

    def test_valid_display_drivers(self):
        """Test all valid display drivers are accepted."""
        validator = ConfigValidator()
        for driver in ["mock", "waveshare"]:
            config = {
                "artframe": {
                    "display": {"driver": driver, "config": {}},
                    "storage": {"data_dir": "/tmp"},
                }
            }
            validator.validate(config)  # Should not raise

    def test_invalid_rotation(self):
        """Test validation fails with invalid rotation."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {"driver": "mock", "config": {"rotation": 45}},
                "storage": {"data_dir": "/tmp"},
            }
        }

        with pytest.raises(ValueError, match="rotation must be one of"):
            validator.validate(config)

    def test_invalid_gpio_pin(self):
        """Test validation fails with invalid GPIO pin."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {
                    "driver": "waveshare",
                    "config": {"gpio_pins": {"busy": 100, "reset": 17, "dc": 25, "cs": 8}},
                },
                "storage": {"data_dir": "/tmp"},
            }
        }

        with pytest.raises(ValueError, match="gpio_pins.busy must be 0-40"):
            validator.validate(config)

    def test_invalid_log_level(self):
        """Test validation fails with invalid log level."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {"driver": "mock", "config": {}},
                "storage": {"data_dir": "/tmp"},
                "logging": {"level": "INVALID"},
            }
        }

        with pytest.raises(ValueError, match="logging.level must be one of"):
            validator.validate(config)

    def test_invalid_port(self):
        """Test validation fails with invalid port."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {"driver": "mock", "config": {}},
                "storage": {"data_dir": "/tmp"},
                "web": {"port": 99999},
            }
        }

        with pytest.raises(ValueError, match="port must be an integer between 1 and 65535"):
            validator.validate(config)

    def test_minimal_valid_config(self):
        """Test minimal valid configuration."""
        validator = ConfigValidator()
        config = {
            "artframe": {
                "display": {"driver": "mock", "config": {}},
                "storage": {"data_dir": "/tmp"},
            }
        }
        validator.validate(config)  # Should not raise


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_valid_config(self, test_config_file):
        """Test loading valid configuration file."""
        config_manager = ConfigManager(test_config_file)

        assert config_manager.get_display_driver() == "mock"
        assert config_manager.get("artframe.storage.data_dir") == "/tmp/test_data"

    def test_config_file_not_found(self, temp_dir):
        """Test error when configuration file doesn't exist."""
        non_existent_file = temp_dir / "non_existent.yaml"

        with pytest.raises(FileNotFoundError):
            ConfigManager(non_existent_file)

    def test_environment_variable_expansion(self, temp_dir):
        """Test environment variable expansion in configuration."""
        config_data = {
            "artframe": {
                "display": {"driver": "mock", "config": {}},
                "storage": {"data_dir": "${TEST_DATA_DIR}"},
            }
        }

        config_file = temp_dir / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch.dict("os.environ", {"TEST_DATA_DIR": "/expanded/path"}):
            config_manager = ConfigManager(config_file)
            assert config_manager.get("artframe.storage.data_dir") == "/expanded/path"

    def test_get_with_default(self, test_config_file):
        """Test get method with default value."""
        config_manager = ConfigManager(test_config_file)

        # Existing key
        assert config_manager.get("artframe.display.driver") == "mock"

        # Non-existing key with default
        assert config_manager.get("artframe.non.existent", "default") == "default"

        # Non-existing key without default
        assert config_manager.get("artframe.non.existent") is None

    def test_get_data_dir(self, test_config_file):
        """Test getting data directory path."""
        config_manager = ConfigManager(test_config_file)
        data_dir = config_manager.get_data_dir()

        assert isinstance(data_dir, Path)
        assert str(data_dir) == "/tmp/test_data"

    def test_get_cache_dir(self, test_config_file):
        """Test getting cache directory path."""
        config_manager = ConfigManager(test_config_file)
        cache_dir = config_manager.get_cache_dir()

        assert isinstance(cache_dir, Path)
        assert str(cache_dir) == "/tmp/test_cache"

    def test_get_display_dimensions(self, test_config_file):
        """Test getting display dimensions."""
        config_manager = ConfigManager(test_config_file)
        width, height = config_manager.get_display_dimensions()

        assert width == 800
        assert height == 480

    def test_get_timezone(self, test_config_file):
        """Test getting timezone."""
        config_manager = ConfigManager(test_config_file)
        assert config_manager.get_timezone() == "UTC"

    def test_config_validation_on_load(self, temp_dir):
        """Test that configuration is validated on load."""
        invalid_config = {"invalid": "config"}

        config_file = temp_dir / "invalid_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        with pytest.raises(ValueError):
            ConfigManager(config_file)

    def test_observer_pattern(self, test_config_file):
        """Test configuration change observer pattern."""
        config_manager = ConfigManager(test_config_file)

        observed_changes = []

        def observer(key, value):
            observed_changes.append((key, value))

        config_manager.add_observer(observer)

        # Simulate config change notification
        config_manager._notify_changes(
            {"artframe": {"display": {"driver": "mock"}}},
            {"artframe": {"display": {"driver": "waveshare"}}},
        )

        assert len(observed_changes) > 0
        assert ("artframe.display.driver", "waveshare") in observed_changes

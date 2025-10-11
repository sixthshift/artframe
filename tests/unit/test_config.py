"""
Unit tests for configuration management.
"""

import pytest
from unittest.mock import patch, mock_open
import yaml

from src.artframe.config import ConfigManager, ConfigValidator


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_valid_config(self, sample_config):
        """Test validation of valid configuration."""
        validator = ConfigValidator()
        # Should not raise exception
        validator.validate(sample_config)

    def test_missing_artframe_section(self):
        """Test validation fails when artframe section is missing."""
        validator = ConfigValidator()
        config = {'other': 'value'}

        with pytest.raises(ValueError, match="Configuration must have 'artframe' root key"):
            validator.validate(config)

    def test_missing_required_sections(self):
        """Test validation fails when required sections are missing."""
        validator = ConfigValidator()
        config = {'artframe': {'source': {}}}  # Missing style, display, cache

        with pytest.raises(ValueError, match="Required section 'artframe.style' missing"):
            validator.validate(config)

    def test_invalid_source_provider(self):
        """Test validation fails with invalid source provider."""
        validator = ConfigValidator()
        config = {
            'artframe': {
                'source': {'provider': 'invalid'},
                'style': {'provider': 'nanobanana', 'config': {}},
                'display': {'driver': 'mock', 'config': {}},
                'cache': {'directory': '/tmp'}
            }
        }

        with pytest.raises(ValueError, match="Invalid source provider 'invalid'"):
            validator.validate(config)

    def test_invalid_immich_config(self):
        """Test validation fails with invalid Immich configuration."""
        validator = ConfigValidator()
        config = {
            'artframe': {
                'source': {
                    'provider': 'immich',
                    'config': {}  # Missing required keys
                },
                'style': {'provider': 'nanobanana', 'config': {'api_url': 'http://test', 'api_key': 'key', 'styles': ['test']}},
                'display': {'driver': 'mock', 'config': {}},
                'cache': {'directory': '/tmp'}
            }
        }

        with pytest.raises(ValueError, match="Immich config missing required key"):
            validator.validate(config)

    def test_invalid_url_format(self):
        """Test validation fails with invalid URL format."""
        validator = ConfigValidator()
        config = {
            'artframe': {
                'source': {
                    'provider': 'immich',
                    'config': {
                        'server_url': 'invalid-url',  # Invalid URL
                        'api_key': 'test'
                    }
                },
                'style': {'provider': 'nanobanana', 'config': {'api_url': 'http://test', 'api_key': 'key', 'styles': ['test']}},
                'display': {'driver': 'mock', 'config': {}},
                'cache': {'directory': '/tmp'}
            }
        }

        with pytest.raises(ValueError, match="server_url must start with http"):
            validator.validate(config)


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_valid_config(self, test_config_file):
        """Test loading valid configuration file."""
        config_manager = ConfigManager(test_config_file)

        assert config_manager.get('artframe.source.provider') == 'immich'
        assert config_manager.get('artframe.display.driver') == 'mock'

    def test_config_file_not_found(self, temp_dir):
        """Test error when configuration file doesn't exist."""
        non_existent_file = temp_dir / "non_existent.yaml"

        with pytest.raises(FileNotFoundError):
            ConfigManager(non_existent_file)

    def test_environment_variable_expansion(self, temp_dir):
        """Test environment variable expansion in configuration."""
        config_data = {
            'artframe': {
                'source': {
                    'provider': 'immich',
                    'config': {
                        'server_url': 'http://localhost',
                        'api_key': '${TEST_API_KEY}'
                    }
                },
                'style': {'provider': 'nanobanana', 'config': {'api_url': 'http://test', 'api_key': 'key', 'styles': ['test']}},
                'display': {'driver': 'mock', 'config': {}},
                'cache': {'directory': '/tmp'}
            }
        }

        config_file = temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        with patch.dict('os.environ', {'TEST_API_KEY': 'expanded_key'}):
            config_manager = ConfigManager(config_file)
            assert config_manager.get('artframe.source.config.api_key') == 'expanded_key'

    def test_get_with_default(self, test_config_file):
        """Test get method with default value."""
        config_manager = ConfigManager(test_config_file)

        # Existing key
        assert config_manager.get('artframe.source.provider') == 'immich'

        # Non-existing key with default
        assert config_manager.get('artframe.non.existent', 'default') == 'default'

        # Non-existing key without default
        assert config_manager.get('artframe.non.existent') is None

    def test_get_source_config(self, test_config_file):
        """Test getting source configuration."""
        config_manager = ConfigManager(test_config_file)
        source_config = config_manager.get_source_config()

        assert source_config['provider'] == 'immich'
        assert 'config' in source_config

    def test_get_style_config(self, test_config_file):
        """Test getting style configuration."""
        config_manager = ConfigManager(test_config_file)
        style_config = config_manager.get_style_config()

        assert style_config['provider'] == 'nanobanana'
        assert 'config' in style_config

    def test_config_validation_on_load(self, temp_dir):
        """Test that configuration is validated on load."""
        invalid_config = {'invalid': 'config'}

        config_file = temp_dir / "invalid_config.yaml"
        with open(config_file, 'w') as f:
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

        # Simulate config reload with changes
        with patch.object(config_manager, '_load_config') as mock_load:
            # Mock a configuration change
            new_config = config_manager._config.copy()
            new_config['artframe']['source']['provider'] = 'new_provider'

            mock_load.return_value = None
            config_manager._config = new_config

            # Manually trigger change notification for testing
            config_manager._notify_changes(
                {'artframe': {'source': {'provider': 'immich'}}},
                {'artframe': {'source': {'provider': 'new_provider'}}}
            )

        # Check that observer was called
        assert len(observed_changes) > 0
        assert ('artframe.source.provider', 'new_provider') in observed_changes
"""
Unit tests for display management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from src.artframe.display.controller import DisplayController
from src.artframe.display.drivers import MockDriver, DriverInterface


class TestMockDriver:
    """Tests for MockDriver."""

    def test_initialization(self):
        """Test mock driver initialization."""
        config = {
            'width': 600,
            'height': 448,
            'save_images': True,
            'output_dir': '/tmp/test_mock'
        }

        driver = MockDriver(config)
        assert driver.width == 600
        assert driver.height == 448
        assert driver.save_images is True

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = {'width': 600, 'height': 448}
        driver = MockDriver(config)
        # Should not raise exception

    def test_validate_config_invalid_width(self):
        """Test validation fails with invalid width."""
        config = {'width': 'invalid', 'height': 448}
        with pytest.raises(ValueError, match="Width must be a positive integer"):
            MockDriver(config)

    def test_validate_config_invalid_height(self):
        """Test validation fails with invalid height."""
        config = {'width': 600, 'height': -1}
        with pytest.raises(ValueError, match="Height must be a positive integer"):
            MockDriver(config)

    def test_get_display_size(self):
        """Test getting display size."""
        config = {'width': 800, 'height': 600}
        driver = MockDriver(config)
        size = driver.get_display_size()
        assert size == (800, 600)

    def test_display_image(self, temp_dir):
        """Test displaying an image."""
        config = {
            'width': 600,
            'height': 448,
            'save_images': True,
            'output_dir': str(temp_dir)
        }

        driver = MockDriver(config)
        driver.initialize()

        # Create test image
        test_image = Image.new('RGB', (600, 448), color='red')

        # Display image
        driver.display_image(test_image)

        assert driver.get_display_count() == 1
        assert driver.get_last_displayed_image() is not None

        # Check if image was saved
        saved_files = list(temp_dir.glob("display_*.png"))
        assert len(saved_files) == 1

    def test_clear_display(self):
        """Test clearing display."""
        config = {'width': 600, 'height': 448, 'save_images': False}
        driver = MockDriver(config)

        driver.clear_display()
        assert driver.get_display_count() == 1

    def test_sleep_wake(self):
        """Test sleep and wake operations."""
        config = {'width': 600, 'height': 448}
        driver = MockDriver(config)

        # These should not raise exceptions
        driver.sleep()
        driver.wake()


class TestDriverInterface:
    """Tests for DriverInterface base class."""

    def test_optimize_image_for_display(self):
        """Test image optimization."""
        # Create concrete implementation for testing
        class TestDriver(DriverInterface):
            def validate_config(self):
                pass

            def initialize(self):
                pass

            def get_display_size(self):
                return (600, 448)

            def display_image(self, image):
                pass

            def clear_display(self):
                pass

            def sleep(self):
                pass

            def wake(self):
                pass

        driver = TestDriver({})

        # Create test image larger than display
        test_image = Image.new('RGB', (1200, 896), color='blue')

        # Optimize image
        optimized = driver.optimize_image_for_display(test_image)

        assert optimized.size == (600, 448)
        assert optimized.mode == 'L'  # Should be grayscale


class TestDisplayController:
    """Tests for DisplayController."""

    @pytest.fixture
    def mock_display_config(self):
        """Mock display configuration."""
        return {
            'driver': 'mock',
            'config': {
                'width': 600,
                'height': 448,
                'save_images': False
            },
            'show_metadata': True
        }

    def test_initialization(self, mock_display_config):
        """Test display controller initialization."""
        controller = DisplayController(mock_display_config)
        assert controller.config == mock_display_config
        assert isinstance(controller.driver, MockDriver)
        assert controller.state.status == "idle"

    def test_initialize(self, mock_display_config):
        """Test display initialization."""
        controller = DisplayController(mock_display_config)
        controller.initialize()

        assert controller.state.status == "ready"
        assert controller.state.error_count == 0

    def test_display_styled_image(self, mock_display_config, sample_styled_image):
        """Test displaying a styled image."""
        controller = DisplayController(mock_display_config)
        controller.initialize()

        controller.display_styled_image(sample_styled_image)

        assert controller.state.current_image_id == sample_styled_image.original_photo_id
        assert controller.state.last_refresh is not None
        assert controller.state.status == "idle"

    def test_display_image_file(self, mock_display_config, sample_photo):
        """Test displaying an image file."""
        controller = DisplayController(mock_display_config)
        controller.initialize()

        controller.display_image_file(sample_photo.original_path, "Test Title")

        assert controller.state.current_image_id == str(sample_photo.original_path)
        assert controller.state.last_refresh is not None

    def test_clear_display(self, mock_display_config):
        """Test clearing display."""
        controller = DisplayController(mock_display_config)
        controller.initialize()

        controller.clear_display()

        assert controller.state.current_image_id is None
        assert controller.state.last_refresh is not None
        assert controller.state.status == "idle"

    def test_error_handling(self, mock_display_config, temp_dir):
        """Test error handling in display operations."""
        controller = DisplayController(mock_display_config)

        # Mock driver to raise exception
        controller.driver.display_image = Mock(side_effect=Exception("Test error"))

        # Create dummy styled image
        from pathlib import Path
        from datetime import datetime
        from src.artframe.models import StyledImage
        from PIL import Image

        # Create a dummy image file
        img = Image.new('RGB', (100, 100), color='blue')
        img_path = temp_dir / "test_styled.jpg"
        img.save(img_path)

        styled_image = StyledImage(
            original_photo_id="test_photo",
            style_name="test_style",
            styled_path=img_path,
            created_at=datetime.now(),
            metadata={'dimensions': (100, 100)}
        )

        # Should handle error gracefully
        with pytest.raises(Exception):  # DisplayError should be raised
            controller.display_styled_image(styled_image)

        assert controller.state.status == "error"
        assert controller.state.error_count > 0

    def test_show_error_message(self, mock_display_config):
        """Test showing error message on display."""
        controller = DisplayController(mock_display_config)
        controller.initialize()

        # Should not raise exception
        controller.show_error_message("Test error message")

    def test_sleep_wake(self, mock_display_config):
        """Test sleep and wake operations."""
        controller = DisplayController(mock_display_config)
        controller.initialize()

        controller.sleep()
        assert controller.state.status == "sleeping"

        controller.wake()
        assert controller.state.status == "idle"

    def test_get_display_size(self, mock_display_config):
        """Test getting display size."""
        controller = DisplayController(mock_display_config)
        size = controller.get_display_size()
        assert size == (600, 448)

    def test_get_state(self, mock_display_config):
        """Test getting display state."""
        controller = DisplayController(mock_display_config)
        state = controller.get_state()

        assert state.current_image_id is None
        assert state.status == "idle"
        assert state.error_count == 0

    def test_create_unknown_driver(self):
        """Test error when creating unknown driver."""
        config = {
            'driver': 'unknown_driver',
            'config': {}
        }

        with pytest.raises(ValueError, match="Unknown display driver"):
            DisplayController(config)

    @patch('src.artframe.display.controller.ImageFont.truetype')
    def test_metadata_overlay(self, mock_font, mock_display_config, sample_styled_image):
        """Test adding metadata overlay to image."""
        # Mock font loading
        mock_font.return_value = Mock()

        controller = DisplayController(mock_display_config)
        controller.initialize()

        # This should not raise exception even if font loading fails
        controller.display_styled_image(sample_styled_image, show_metadata=True)

    def test_metadata_overlay_disabled(self, sample_styled_image):
        """Test displaying without metadata overlay."""
        config = {
            'driver': 'mock',
            'config': {'width': 600, 'height': 448},
            'show_metadata': False
        }

        controller = DisplayController(config)
        controller.initialize()

        controller.display_styled_image(sample_styled_image, show_metadata=False)

        assert controller.state.current_image_id == sample_styled_image.original_photo_id
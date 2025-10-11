"""
Main controller for Artframe system.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config import ConfigManager
from .plugins.source import SourcePlugin, ImmichSource, NoneSource
from .plugins.style import StylePlugin, NanoBananaStyle, NoneStyle
from .storage import StorageManager
from .display import DisplayController
from .utils import StyleSelector, Scheduler
from .models import Photo, StyledImage, StorageStats
from .logging import Logger


class ArtframeController:
    """Main controller that orchestrates the daily photo frame workflow."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Artframe controller.

        Args:
            config_path: Path to configuration file
        """
        self.logger = Logger(__name__)

        # Initialize configuration
        self.config_manager = ConfigManager(config_path)

        # Initialize components
        self.source_plugin = self._create_source_plugin()
        self.style_plugin = self._create_style_plugin()
        self.storage_manager = self._create_storage_manager()
        self.display_controller = self._create_display_controller()

        # Initialize utilities
        self.style_selector = self._create_style_selector()
        self.scheduler = self._create_scheduler()

        # Track state
        self.running = False
        self.last_update = None

    def _create_source_plugin(self) -> SourcePlugin:
        """Create and configure source plugin with fallback to none."""
        source_config = self.config_manager.get_source_config()
        provider = source_config.get('provider', 'none')

        try:
            if provider == 'immich':
                plugin = ImmichSource(source_config.get('config', {}))
            elif provider == 'none':
                plugin = NoneSource(source_config.get('config', {}))
            else:
                self.logger._logger.warning(f"Unknown source provider: {provider}, falling back to none")
                plugin = NoneSource({})

            # Test the plugin to ensure it works
            if not plugin.validate_config():
                raise Exception("Plugin configuration validation failed")

            return plugin

        except Exception as e:
            self.logger._logger.error(f"Failed to create source plugin '{provider}': {e}")
            self.logger._logger.info("Falling back to NoneSource plugin")
            return NoneSource({})

    def _create_style_plugin(self) -> StylePlugin:
        """Create and configure style plugin with fallback to none."""
        style_config = self.config_manager.get_style_config()
        provider = style_config.get('provider', 'none')

        try:
            if provider == 'nanobanana':
                plugin = NanoBananaStyle(style_config.get('config', {}))
            elif provider == 'none':
                plugin = NoneStyle(style_config.get('config', {}))
            else:
                self.logger._logger.warning(f"Unknown style provider: {provider}, falling back to none")
                plugin = NoneStyle({})

            # Test the plugin to ensure it works
            if not plugin.validate_config():
                raise Exception("Plugin configuration validation failed")

            return plugin

        except Exception as e:
            self.logger._logger.error(f"Failed to create style plugin '{provider}': {e}")
            self.logger._logger.info("Falling back to NoneStyle plugin")
            return NoneStyle({})

    def _create_storage_manager(self) -> StorageManager:
        """Create and configure storage manager."""
        storage_config = self.config_manager.get_storage_config()

        return StorageManager(
            storage_dir=Path(storage_config.get('directory', '/var/lib/artframe'))
        )

    def _create_display_controller(self) -> DisplayController:
        """Create and configure display controller."""
        display_config = self.config_manager.get_display_config()
        return DisplayController(display_config)

    def _create_style_selector(self) -> StyleSelector:
        """Create and configure style selector."""
        style_config = self.config_manager.get_style_config()
        config = style_config.get('config', {})

        styles = config.get('styles', ['ghibli'])
        rotation = config.get('rotation', 'daily')

        return StyleSelector(styles, rotation)

    def _create_scheduler(self) -> Scheduler:
        """Create and configure scheduler."""
        schedule_config = self.config_manager.get_schedule_config()

        update_time = schedule_config.get('update_time', '06:00')
        timezone = schedule_config.get('timezone')

        return Scheduler(update_time, timezone)

    def initialize(self, skip_connection_test: bool = False) -> None:
        """
        Initialize all components.

        Args:
            skip_connection_test: If True, skip connection tests (useful for dev/testing)
        """
        self.logger.log_initialization_start()

        try:
            # Test connections (skip if requested)
            if not skip_connection_test:
                if not self.source_plugin.test_connection():
                    raise RuntimeError("Failed to connect to photo source")

                if not self.style_plugin.test_connection():
                    raise RuntimeError("Failed to connect to style service")

            # Initialize display
            self.display_controller.initialize()

            self.logger.log_initialization_success()

        except Exception as e:
            self.logger.log_initialization_error(e)
            raise

    def run_daily_update(self) -> bool:
        """
        Run the daily photo update workflow.

        Returns:
            bool: True if update was successful
        """
        self.logger.log_update_start()

        try:
            # Step 1: Fetch new photo
            photo = self.source_plugin.fetch_photo()
            self.logger.log_photo_fetched(photo.id)

            # Store photo locally
            self.storage_manager.store_photo(photo)

            # Step 2: Select style
            selected_style = self.style_selector.select_style()
            self.logger.log_style_selected(selected_style)

            # Step 3: Check if styled version already exists
            styled_image = self.storage_manager.get_styled_image(photo.id, selected_style)

            if styled_image is None:
                # Step 4: Apply style transformation
                self.logger.log_style_applying(photo.id, selected_style)

                styled_image = self._create_styled_image(photo, selected_style)

                # Store styled image locally
                self.storage_manager.store_styled_image(styled_image)

            else:
                self.logger.log_cached_image_used(f"{styled_image.original_photo_id}_{styled_image.style_name}")

            # Step 5: Display the styled image
            self.display_controller.display_styled_image(styled_image)

            # Step 6: Record style selection
            self.style_selector.record_selection(selected_style)

            # Step 7: Update complete

            self.last_update = datetime.now()

            # Mark scheduler as refreshed (for e-ink safety tracking)
            self.scheduler.mark_refreshed()

            self.logger.log_update_success()

            return True

        except Exception as e:
            self.logger.log_update_error(e)
            self._handle_update_error(str(e))
            return False

    def _create_styled_image(self, photo: Photo, style: str) -> StyledImage:
        """Create a styled image from photo and style."""
        # Generate unique ID for styled image
        styled_id = str(uuid.uuid4())

        # Create temporary output path
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        output_path = temp_dir / f"{styled_id}_{style}.jpg"

        # Apply style transformation
        success = self.style_plugin.apply_style(photo.original_path, style, output_path)

        if not success:
            raise RuntimeError(f"Style transformation failed for {photo.id} with style {style}")

        # Get image dimensions
        from PIL import Image
        with Image.open(output_path) as img:
            dimensions = img.size

        return StyledImage(
            original_photo_id=photo.id,
            style_name=style,
            styled_path=output_path,
            created_at=datetime.now(),
            metadata={'dimensions': dimensions, 'file_size': output_path.stat().st_size}
        )


    def _handle_update_error(self, error_message: str) -> None:
        """Handle update errors by showing error on display."""
        try:
            self.display_controller.show_error_message(f"Update Error: {error_message}")
        except Exception as e:
            self.logger.log_display_error_failed(e)

    def run_scheduled_loop(self) -> None:
        """Run the main scheduled loop."""
        self.logger.log_scheduled_loop_start()
        self.running = True

        try:
            while self.running:
                if self.scheduler.is_update_time():
                    self.run_daily_update()

                    # Sleep for a bit to avoid multiple updates in the same minute
                    time.sleep(60)

                else:
                    # Sleep for a short while before checking again
                    time.sleep(30)

        except KeyboardInterrupt:
            self.logger.log_interrupt_received()
            self.running = False

        except Exception as e:
            self.logger.log_scheduled_loop_error(e)
            self.running = False

    def stop(self) -> None:
        """Stop the scheduled loop."""
        self.logger.log_controller_stopping()
        self.running = False

    def manual_refresh(self) -> bool:
        """Trigger an immediate photo update."""
        self.logger.log_manual_refresh_triggered()
        return self.run_daily_update()

    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        storage_stats = self.storage_manager.get_storage_stats()
        display_state = self.display_controller.get_state()

        return {
            "running": self.running,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "next_scheduled": self.scheduler.get_next_update_time().isoformat(),
            "storage_stats": {
                "total_photos": storage_stats.total_photos,
                "total_styled_images": storage_stats.total_styled_images,
                "total_size_mb": round(storage_stats.total_size_mb, 2),
                "storage_directory": storage_stats.storage_directory
            },
            "display_state": {
                "status": display_state.status,
                "current_image_id": display_state.current_image_id,
                "last_refresh": display_state.last_refresh.isoformat() if display_state.last_refresh else None,
                "error_count": display_state.error_count
            }
        }

    def test_connections(self) -> Dict[str, bool]:
        """Test all external connections."""
        return {
            "source": self.source_plugin.test_connection(),
            "style": self.style_plugin.test_connection()
        }
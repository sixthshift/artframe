"""
Main controller for Artframe system.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config import ConfigManager
from .storage import StorageManager
from .display import DisplayController
from .utils import Scheduler
from .models import StorageStats
from .logging import Logger
from .playlists import PlaylistManager, PlaylistExecutor
from .plugins import InstanceManager


class ArtframeController:
    """
    Main controller that orchestrates the Artframe system.

    Simplified controller for the new plugin architecture.
    Plugin execution is now handled by InstanceManager and playlists.
    """

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
        self.storage_manager = self._create_storage_manager()
        self.display_controller = self._create_display_controller()
        self.scheduler = self._create_scheduler()

        # Initialize plugin and playlist management
        storage_dir = Path.home() / '.artframe' / 'data'
        self.instance_manager = InstanceManager(storage_dir)
        self.playlist_manager = PlaylistManager(storage_dir)

        # Create playlist executor
        device_config = self._get_device_config()
        self.playlist_executor = PlaylistExecutor(
            self.playlist_manager,
            self.instance_manager,
            device_config
        )

        # Track state
        self.running = False
        self.last_update = None

    def _create_storage_manager(self) -> StorageManager:
        """Create and configure storage manager."""
        # Get cache config
        cache_config = self.config_manager.config.get('artframe', {}).get('cache', {})

        storage_dir = cache_config.get('cache_directory', '~/.artframe/cache')

        # Expand user home directory
        storage_dir = Path(storage_dir).expanduser()

        return StorageManager(storage_dir=storage_dir)

    def _create_display_controller(self) -> DisplayController:
        """Create and configure display controller."""
        display_config = self.config_manager.get_display_config()
        return DisplayController(display_config)

    def _create_scheduler(self) -> Scheduler:
        """Create and configure scheduler."""
        scheduler_config = self.config_manager.config.get('artframe', {}).get('scheduler', {})

        # For now, use a simple daily update time
        # TODO: Replace with playlist-based scheduling
        update_time = scheduler_config.get('update_time', '06:00')
        timezone = scheduler_config.get('timezone', 'UTC')

        return Scheduler(update_time, timezone)

    def _get_device_config(self) -> Dict[str, Any]:
        """Get device configuration for image generation."""
        display_config = self.config_manager.get_display_config()

        return {
            'width': display_config.get('width', 600),
            'height': display_config.get('height', 448),
            'rotation': display_config.get('rotation', 0),
            'color_mode': 'grayscale'  # E-ink displays are typically grayscale
        }

    def initialize(self, skip_connection_test: bool = False) -> None:
        """
        Initialize all components.

        Args:
            skip_connection_test: If True, skip connection tests (useful for dev/testing)
        """
        self.logger.log_initialization_start()

        try:
            # Initialize display
            self.display_controller.initialize()

            self.logger.log_initialization_success()

        except Exception as e:
            self.logger.log_initialization_error(e)
            raise

    def manual_refresh(self) -> bool:
        """
        Trigger an immediate refresh.

        Note: This is a placeholder. Actual plugin execution
        will be handled by playlists and InstanceManager.

        Returns:
            bool: True if refresh was successful
        """
        self.logger.log_manual_refresh_triggered()

        try:
            # For now, just clear the display
            # TODO: Execute current playlist item
            self.display_controller.clear_display()
            self.last_update = datetime.now()
            return True

        except Exception as e:
            self.logger._logger.error(f"Manual refresh failed: {e}")
            return False

    def run_scheduled_loop(self) -> None:
        """
        Run the main scheduled loop with playlist execution.

        This runs the playlist executor which continuously displays
        content from the active playlist.
        """
        self.logger.log_scheduled_loop_start()
        self.running = True

        try:
            # Run the playlist executor loop
            # This will continuously execute playlist items
            self.playlist_executor.run_loop(
                self.display_controller,
                check_interval=5
            )

        except KeyboardInterrupt:
            self.logger.log_interrupt_received()
            self.running = False

        except Exception as e:
            self.logger.log_scheduled_loop_error(e)
            self.running = False
        finally:
            self.playlist_executor.stop()

    def stop(self) -> None:
        """Stop the scheduled loop."""
        self.logger.log_controller_stopping()
        self.running = False
        self.playlist_executor.stop()

    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        storage_stats = self.storage_manager.get_storage_stats()
        display_state = self.display_controller.get_state()

        # Get playlist executor status
        current_item_info = self.playlist_executor.get_current_item_info()

        return {
            "running": self.running,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "next_scheduled": self.scheduler.get_next_update_time().isoformat(),
            "current_playlist_item": current_item_info,
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
        """
        Test system connections.

        Note: Plugin connection testing is now done per-instance
        via the /api/plugins/instances/{id}/test endpoint.
        """
        return {
            "display": True,  # If we got here, display controller initialized
            "storage": self.storage_manager.storage_dir.exists()
        }

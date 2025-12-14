"""
Main controller for Artframe system.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from .config import ConfigManager
from .display import DisplayController
from .logging import Logger
from .plugins import InstanceManager
from .scheduling import ContentOrchestrator, ScheduleManager
from .storage import StorageManager
from .utils import now_in_tz


class ArtframeController:
    """
    Main controller that orchestrates the Artframe system.

    Uses the unified ContentOrchestrator for all content scheduling
    and display decisions.
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

        # Initialize plugin and schedule management using config paths
        data_dir = self.config_manager.get_data_dir()
        timezone = self.config_manager.get_timezone()
        self.instance_manager = InstanceManager(data_dir, timezone=timezone)
        self.schedule_manager = ScheduleManager(data_dir, timezone=timezone)

        # Create device config
        device_config = self._get_device_config()

        # Create unified content orchestrator
        self.orchestrator = ContentOrchestrator(
            schedule_manager=self.schedule_manager,
            instance_manager=self.instance_manager,
            device_config=device_config,
        )

        # Track state
        self.running = False
        self.last_update: Optional[datetime] = None
        self._tz = ZoneInfo(timezone)
        self._now = lambda: now_in_tz(self._tz)

    def _create_storage_manager(self) -> StorageManager:
        """Create and configure storage manager."""
        cache_dir = self.config_manager.get_cache_dir()
        return StorageManager(storage_dir=cache_dir)

    def _create_display_controller(self) -> DisplayController:
        """Create and configure display controller."""
        display_config = self.config_manager.get_display_config()
        timezone = self.config_manager.get_timezone()
        return DisplayController(display_config, timezone=timezone)

    def _get_device_config(self) -> dict[str, Any]:
        """Get device configuration for image generation."""
        width, height = self.config_manager.get_display_dimensions()
        display_config = self.config_manager.get_display_config().get("config", {})

        return {
            "width": width,
            "height": height,
            "rotation": display_config.get("rotation", 0),
            "color_mode": "grayscale",  # E-ink displays are typically grayscale
            "timezone": self.config_manager.get_timezone(),
            "cache_dir": str(self.config_manager.get_cache_dir()),
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

        Uses the ContentOrchestrator to determine and display
        the current content.

        Returns:
            bool: True if refresh was successful
        """
        self.logger.log_manual_refresh_triggered()

        try:
            success = self.orchestrator.force_refresh(self.display_controller)
            if success:
                self.last_update = self._now()
            return success

        except Exception as e:
            self.logger._logger.error(f"Manual refresh failed: {e}")
            return False

    def run_scheduled_loop(self) -> None:
        """
        Run the main scheduled loop with unified content orchestration.

        This runs the ContentOrchestrator which handles schedule-based
        content selection.
        """
        self.logger.log_scheduled_loop_start()
        self.running = True

        try:
            # Run the unified content orchestrator loop
            self.orchestrator.run_loop(self.display_controller)

        except KeyboardInterrupt:
            self.logger.log_interrupt_received()
            self.running = False

        except Exception as e:
            self.logger.log_scheduled_loop_error(e)
            self.running = False
        finally:
            self.orchestrator.stop()

    def stop(self) -> None:
        """Stop the scheduled loop."""
        self.logger.log_controller_stopping()
        self.running = False
        self.orchestrator.stop()

    def get_status(self) -> dict[str, Any]:
        """Get current system status."""
        display_state = self.display_controller.get_state()

        # Get orchestrator status
        orchestrator_status = self.orchestrator.get_current_status()

        return {
            "running": self.running,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "next_scheduled": self.orchestrator.get_next_update_time().isoformat(),
            "orchestrator": orchestrator_status,
            "display_state": {
                "current_image_id": display_state.current_image_id,
                "last_refresh": (
                    display_state.last_refresh.isoformat() if display_state.last_refresh else None
                ),
            },
        }

    def test_connections(self) -> dict[str, bool]:
        """
        Test system connections.

        Note: Plugin connection testing is now done per-instance
        via the /api/instances/{id}/test endpoint.
        """
        return {
            "display": True,  # If we got here, display controller initialized
            "storage": self.storage_manager.storage_dir.exists(),
        }

"""
Schedule executor for running time-based schedules.

Evaluates the current time and displays the appropriate plugin instance
based on time slot assignments.

Note: This is a legacy executor kept for backward compatibility.
The ContentOrchestrator is the preferred way to handle scheduling.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from ..models import TargetType
from ..plugins import get_plugin
from ..plugins.instance_manager import InstanceManager
from .schedule_manager import ScheduleManager

logger = logging.getLogger(__name__)


class ScheduleExecutor:
    """
    Executes schedules by evaluating current time and running matching plugin instances.

    Unlike PlaylistExecutor which plays sequentially, ScheduleExecutor asks:
    "What should be displaying RIGHT NOW based on the schedule?"
    """

    def __init__(
        self,
        schedule_manager: ScheduleManager,
        instance_manager: InstanceManager,
        device_config: Dict[str, Any],
    ):
        """
        Initialize schedule executor.

        Args:
            schedule_manager: ScheduleManager instance
            instance_manager: InstanceManager instance
            device_config: Display device configuration
        """
        self.schedule_manager = schedule_manager
        self.instance_manager = instance_manager
        self.device_config = device_config

        self.running = False
        self.last_displayed_instance_id: Optional[str] = None
        self.last_check_time: Optional[datetime] = None

    def get_current_scheduled_instance_id(self) -> Optional[str]:
        """
        Determine which instance should be displayed right now.

        Returns:
            Instance ID to display, or None if nothing scheduled
        """
        # Get matching slot for current time
        slot = self.schedule_manager.get_current_slot()

        if slot:
            # Only return instance IDs, not playlist IDs
            if slot.target_type == TargetType.INSTANCE.value:
                logger.debug(f"Current slot: {slot.key} -> {slot.target_id}")
                return slot.target_id
            else:
                # It's a playlist - this executor doesn't handle playlists
                logger.debug(f"Current slot is a playlist: {slot.target_id}")
                return None

        logger.debug("No slot assigned for current time")
        return None

    def should_update_display(self) -> bool:
        """
        Check if the display should be updated.

        Returns True if:
        - We've never displayed anything yet
        - The scheduled instance has changed from what's currently showing
        """
        current_instance_id = self.get_current_scheduled_instance_id()

        # Nothing to display
        if current_instance_id is None:
            return False

        # First run
        if self.last_displayed_instance_id is None:
            return True

        # Instance has changed
        if current_instance_id != self.last_displayed_instance_id:
            logger.info(
                f"Schedule changed: {self.last_displayed_instance_id} -> {current_instance_id}"
            )
            return True

        return False

    def execute_current_schedule(self) -> Optional[Any]:
        """
        Execute the currently scheduled instance and generate content.

        Returns:
            Generated image or None if failed
        """
        instance_id = self.get_current_scheduled_instance_id()

        if instance_id is None:
            logger.warning("No instance scheduled and no default configured")
            return None

        try:
            # Get the instance
            instance = self.instance_manager.get_instance(instance_id)
            if not instance:
                logger.error(f"Instance not found: {instance_id}")
                return None

            if not instance.enabled:
                logger.warning(f"Instance is disabled: {instance_id}")
                return None

            # Get the plugin
            plugin = get_plugin(instance.plugin_id)
            if not plugin:
                logger.error(f"Plugin not found: {instance.plugin_id}")
                return None

            # Generate image
            logger.info(f"Executing scheduled instance: {instance.name}")

            image = plugin.generate_image(instance.settings, self.device_config)

            # Track what we just displayed
            self.last_displayed_instance_id = instance_id
            self.last_check_time = datetime.now()

            return image

        except Exception as e:
            logger.error(f"Failed to execute scheduled instance: {e}", exc_info=True)
            return None

    def get_current_schedule_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current schedule state.

        Returns:
            Dictionary with schedule info or None
        """
        slot = self.schedule_manager.get_current_slot()
        instance_id = self.get_current_scheduled_instance_id()

        if instance_id is None:
            return {
                "status": "no_schedule",
                "message": "Nothing scheduled",
            }

        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            return {
                "status": "error",
                "message": f"Instance {instance_id} not found",
            }

        result = {
            "status": "active",
            "instance_id": instance_id,
            "instance_name": instance.name,
            "plugin_id": instance.plugin_id,
        }

        if slot:
            result.update(
                {
                    "slot_key": slot.key,
                    "day": slot.day,
                    "hour": slot.hour,
                }
            )

        return result

    def run_loop(self, display_controller, check_interval: int = 60) -> None:
        """
        Run the schedule execution loop.

        This loop continuously checks if the display should change based on
        the current time and schedule slots.

        Args:
            display_controller: DisplayController instance
            check_interval: Seconds between checks (default 60)
        """
        self.running = True
        logger.info(f"Schedule executor loop started (checking every {check_interval}s)")

        while self.running:
            try:
                # Check if we should update the display
                if self.should_update_display():
                    # Execute and display the current schedule
                    image = self.execute_current_schedule()

                    if image:
                        # Display the image
                        try:
                            display_controller.display_image(image)
                            logger.info("Successfully displayed scheduled content")
                        except Exception as e:
                            logger.error(f"Failed to display image: {e}", exc_info=True)
                    else:
                        logger.error("Failed to generate image from scheduled instance")

                # Sleep until next check
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("Schedule executor interrupted")
                self.running = False
                break

            except Exception as e:
                logger.error(f"Error in schedule executor loop: {e}", exc_info=True)
                time.sleep(check_interval)

        logger.info("Schedule executor loop stopped")

    def force_refresh(self, display_controller) -> bool:
        """
        Force an immediate refresh of the current scheduled content.

        Args:
            display_controller: DisplayController instance

        Returns:
            True if successful
        """
        try:
            image = self.execute_current_schedule()
            if image:
                display_controller.display_image(image)
                logger.info("Force refresh successful")
                return True
            else:
                logger.error("Force refresh failed: could not generate image")
                return False
        except Exception as e:
            logger.error(f"Force refresh failed: {e}", exc_info=True)
            return False

    def stop(self) -> None:
        """Stop the schedule executor loop."""
        logger.info("Stopping schedule executor")
        self.running = False

"""
Content Orchestrator - unified scheduling and content selection.

This is the single source of truth for determining what content
should be displayed at any given moment.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from PIL import Image

from ..models import ContentSource, TimeSlot
from ..plugins import get_plugin, get_plugin_metadata
from ..plugins.instance_manager import InstanceManager
from ..utils import now_in_tz, seconds_until_next_hour
from .schedule_manager import ScheduleManager

logger = logging.getLogger(__name__)


class ContentOrchestrator:
    """
    Unified content orchestration system.

    This orchestrator is responsible for:
    1. Evaluating time slots to find current content
    2. Resolving instance targets
    3. Determining when to refresh content
    4. Executing plugins to generate images
    """

    def __init__(
        self,
        schedule_manager: ScheduleManager,
        instance_manager: InstanceManager,
        device_config: dict[str, Any],
    ):
        """
        Initialize content orchestrator.

        Args:
            schedule_manager: ScheduleManager instance
            instance_manager: InstanceManager instance
            device_config: Display device configuration
        """
        self.schedule_manager = schedule_manager
        self.instance_manager = instance_manager
        self.device_config = device_config

        # State tracking
        self.running = False
        self.paused = False
        self.current_slot: Optional[TimeSlot] = None
        self.current_item_start: Optional[datetime] = None
        self.last_content_source: Optional[ContentSource] = None
        self.last_displayed_instance_id: Optional[str] = None
        self.last_refresh: Optional[datetime] = None

        # Timezone from schedule manager
        self._tz = ZoneInfo(self.schedule_manager.timezone)

        # Convenience method for current time
        self._now = lambda: now_in_tz(self._tz)

        # Plugin-driven refresh: track active plugin thread
        self._active_plugin_thread: Optional[threading.Thread] = None
        self._active_plugin_stop_event: Optional[threading.Event] = None
        self._active_instance_id: Optional[str] = None

    def get_current_content_source(self) -> ContentSource:
        """
        Determine what content should be displayed RIGHT NOW.

        This is the core method that evaluates:
        1. Active time slot for current time
        2. Target resolution to instance

        Returns:
            ContentSource describing what to display
        """
        # Find active time slot
        slot = self.schedule_manager.get_current_slot()

        if slot is None:
            # No slot assigned for this time
            logger.debug("No slot assigned for current time")
            return ContentSource.empty()

        # Resolve instance content
        return self._resolve_instance_content(slot)

    def _resolve_instance_content(self, slot: TimeSlot) -> ContentSource:
        """
        Resolve a time slot that targets a single instance.

        Args:
            slot: Time slot with target_type="instance"

        Returns:
            ContentSource for the instance
        """
        instance = self.instance_manager.get_instance(slot.target_id)

        if not instance:
            logger.error(f"Instance not found: {slot.target_id}")
            return ContentSource.empty()

        if not instance.enabled:
            logger.warning(f"Instance is disabled: {slot.target_id}")
            return ContentSource.empty()

        # Duration until end of this hour slot
        now = self._now()
        minutes_remaining = 60 - now.minute
        duration = minutes_remaining * 60 - now.second

        return ContentSource(
            instance=instance,
            duration_seconds=max(duration, 60),  # At least 1 minute
            source_type="schedule",
            source_id=slot.key,
            source_name=instance.name,
        )

    def should_update_display(self, content_source: ContentSource) -> bool:
        """
        Determine if the display should be updated.

        Args:
            content_source: The current content source

        Returns:
            True if display should be updated
        """
        # Nothing to display
        if content_source.is_empty():
            return False

        # First run
        if self.last_content_source is None:
            return True

        # Different instance
        if content_source.instance and self.last_displayed_instance_id:
            if content_source.instance.id != self.last_displayed_instance_id:
                return True

        # Check if plugin's refresh interval (cache_ttl) has elapsed
        if content_source.instance and self.current_item_start:
            plugin = get_plugin(content_source.instance.plugin_id)
            if plugin and hasattr(plugin, "get_cache_ttl"):
                try:
                    ttl = plugin.get_cache_ttl(content_source.instance.settings)
                    elapsed = (self._now() - self.current_item_start).total_seconds()
                    if elapsed >= ttl:
                        return True
                except Exception:
                    pass  # If TTL check fails, don't force refresh

        return False

    def execute_content(self, content_source: ContentSource) -> Optional[Image.Image]:
        """
        Execute the plugin for the given content source.

        Args:
            content_source: What to display

        Returns:
            Generated PIL Image or None
        """
        if content_source.is_empty() or content_source.instance is None:
            return None

        instance = content_source.instance

        try:
            # Get the plugin
            plugin = get_plugin(instance.plugin_id)
            if not plugin:
                logger.error(f"Plugin not found: {instance.plugin_id}")
                return None

            # Generate image
            logger.info(f"Executing plugin: {instance.name} ({instance.plugin_id})")
            image = plugin.generate_image(instance.settings, self.device_config)

            # Update state
            self.last_displayed_instance_id = instance.id
            self.last_content_source = content_source
            self.current_item_start = self._now()
            self.last_refresh = self._now()

            return image

        except Exception as e:
            logger.error(f"Failed to execute plugin: {e}", exc_info=True)
            return None

    def run_loop(self, display_controller) -> None:
        """
        Run the main content orchestration loop.

        The orchestrator decides WHICH plugin should be active based on the schedule.
        Each plugin manages its OWN refresh loop via run_active().

        Schedule granularity is 1 hour, so we only check at hour boundaries.

        Args:
            display_controller: DisplayController instance
        """
        self.running = True
        logger.info("Content orchestrator loop started (hourly schedule checks)")

        while self.running:
            try:
                # Get what should display now based on schedule
                content_source = self.get_current_content_source()

                # Check if we need to switch plugins
                new_instance_id = content_source.instance.id if content_source.instance else None

                if new_instance_id != self._active_instance_id:
                    # Plugin changed - stop old one, start new one
                    self._switch_active_plugin(content_source, display_controller)

                # Sleep until next hour boundary
                sleep_seconds = seconds_until_next_hour(self._tz)
                logger.debug(f"Sleeping {sleep_seconds}s until next hour")

                # Sleep in chunks so we can respond to stop signals
                sleep_end = time.time() + sleep_seconds
                while self.running and time.time() < sleep_end:
                    time.sleep(min(10, sleep_end - time.time()))

            except KeyboardInterrupt:
                logger.info("Content orchestrator interrupted")
                self.running = False
                break

            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute on error

        # Stop any active plugin
        self._stop_active_plugin()
        logger.info("Content orchestrator loop stopped")

    def _switch_active_plugin(self, content_source: ContentSource, display_controller) -> None:
        """
        Switch to a new active plugin.

        Stops the current plugin's loop and starts the new one.
        """
        # Stop current plugin if running
        self._stop_active_plugin()

        if content_source.is_empty() or content_source.instance is None:
            logger.info("No content to display")
            self._active_instance_id = None
            return

        instance = content_source.instance
        plugin = get_plugin(instance.plugin_id)

        if not plugin:
            logger.error(f"Plugin not found: {instance.plugin_id}")
            self._active_instance_id = None
            return

        # Create stop event for this plugin
        self._active_plugin_stop_event = threading.Event()
        self._active_instance_id = instance.id

        # Build plugin info for display tracking
        metadata = get_plugin_metadata(instance.plugin_id)
        plugin_info = {
            "plugin_name": metadata.display_name if metadata else instance.plugin_id,
            "instance_name": instance.name,
            "instance_id": instance.id,
            "plugin_id": instance.plugin_id,
        }

        # Start plugin in its own thread
        self._active_plugin_thread = threading.Thread(
            target=self._run_plugin_active,
            args=(
                plugin,
                display_controller,
                instance.settings,
                self.device_config,
                plugin_info,
            ),
            daemon=True,
            name=f"plugin-{instance.plugin_id}",
        )
        self._active_plugin_thread.start()

        logger.info(f"Started plugin: {instance.name} ({instance.plugin_id})")

    def _run_plugin_active(
        self,
        plugin,
        display_controller,
        settings: dict[str, Any],
        device_config: dict[str, Any],
        plugin_info: dict[str, Any],
    ) -> None:
        """Wrapper to run plugin's run_active method."""
        try:
            plugin.run_active(
                display_controller,
                settings,
                device_config,
                self._active_plugin_stop_event,
                plugin_info,
            )
        except Exception as e:
            logger.error(f"Plugin run_active failed: {e}", exc_info=True)

    def _stop_active_plugin(self) -> None:
        """Stop the currently active plugin."""
        if self._active_plugin_stop_event:
            self._active_plugin_stop_event.set()

        if self._active_plugin_thread and self._active_plugin_thread.is_alive():
            # Give it a moment to stop gracefully
            self._active_plugin_thread.join(timeout=2.0)
            if self._active_plugin_thread.is_alive():
                logger.warning("Plugin thread did not stop gracefully")

        self._active_plugin_thread = None
        self._active_plugin_stop_event = None

    def force_refresh(self, display_controller) -> bool:
        """
        Force an immediate refresh of the current content.

        Args:
            display_controller: DisplayController instance

        Returns:
            True if successful
        """
        try:
            content_source = self.get_current_content_source()
            image = self.execute_content(content_source)

            if image:
                # Build plugin info for display tracking
                plugin_info = None
                if content_source.instance:
                    metadata = get_plugin_metadata(content_source.instance.plugin_id)
                    plugin_info = {
                        "plugin_name": (
                            metadata.display_name if metadata else content_source.instance.plugin_id
                        ),
                        "instance_name": content_source.instance.name,
                        "instance_id": content_source.instance.id,
                        "plugin_id": content_source.instance.plugin_id,
                    }
                display_controller.display_image(image, plugin_info)
                logger.info("Force refresh successful")
                return True
            else:
                logger.error("Force refresh failed: could not generate image")
                return False

        except Exception as e:
            logger.error(f"Force refresh failed: {e}", exc_info=True)
            return False

    def stop(self) -> None:
        """Stop the orchestrator loop and active plugin."""
        logger.info("Stopping content orchestrator")
        self.running = False
        self._stop_active_plugin()

    def pause(self) -> None:
        """Pause automatic updates."""
        logger.info("Pausing content orchestrator")
        self.paused = True

    def resume(self) -> None:
        """Resume automatic updates."""
        logger.info("Resuming content orchestrator")
        self.paused = False

    def get_next_update_time(self) -> datetime:
        """
        Get the next scheduled update time (next hour boundary).

        Returns:
            datetime: Next update time in configured timezone
        """
        now = self._now()
        # Next hour starts at minute=0, second=0
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour

    def get_scheduler_status(self) -> dict[str, Any]:
        """
        Get scheduler status for API.

        Returns:
            Dictionary with scheduler state
        """
        now = self._now()

        return {
            "paused": self.paused,
            "update_time": f"{now.hour:02d}:00",  # Current hour slot
            "next_update": self.get_next_update_time().isoformat(),
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "current_time": now.isoformat(),
            "timezone": self.schedule_manager.timezone,
        }

    def get_current_status(self) -> dict[str, Any]:
        """
        Get current orchestrator status for API/UI.

        Returns:
            Dictionary with current state information
        """
        content_source = self.get_current_content_source()

        status: dict[str, Any] = {
            "running": self.running,
            "source_type": content_source.source_type,
            "source_name": content_source.source_name,
            "source_id": content_source.source_id,
            "has_content": not content_source.is_empty(),
        }

        if content_source.instance:
            status["instance"] = {
                "id": content_source.instance.id,
                "name": content_source.instance.name,
                "plugin_id": content_source.instance.plugin_id,
            }

        # Add current slot info
        slot = self.schedule_manager.get_current_slot()
        if slot:
            status["slot"] = {
                "day": slot.day,
                "hour": slot.hour,
                "target_type": slot.target_type,
                "target_id": slot.target_id,
            }

        return status

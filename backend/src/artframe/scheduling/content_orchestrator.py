"""
Content Orchestrator - unified scheduling and content selection.

This is the single source of truth for determining what content
should be displayed at any given moment.
"""

import logging
import random
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from PIL import Image

from ..models import (
    ContentSource,
    PlaybackMode,
    Playlist,
    PlaylistItem,
    PluginInstance,
    TargetType,
    TimeSlot,
)
from ..playlists.playlist_manager import PlaylistManager
from ..playlists.schedule_manager import ScheduleManager
from ..plugins import get_plugin
from ..plugins.instance_manager import InstanceManager
from .condition_evaluator import ConditionEvaluator

logger = logging.getLogger(__name__)


class ContentOrchestrator:
    """
    Unified content orchestration system.

    This orchestrator is responsible for:
    1. Evaluating time slots to find current content
    2. Resolving targets (playlists or instances)
    3. Managing playlist playback state
    4. Determining when to refresh content
    5. Executing plugins to generate images
    """

    def __init__(
        self,
        schedule_manager: ScheduleManager,
        playlist_manager: PlaylistManager,
        instance_manager: InstanceManager,
        device_config: Dict[str, Any],
        condition_evaluator: Optional[ConditionEvaluator] = None,
    ):
        """
        Initialize content orchestrator.

        Args:
            schedule_manager: ScheduleManager instance
            playlist_manager: PlaylistManager instance
            instance_manager: InstanceManager instance
            device_config: Display device configuration
            condition_evaluator: Optional ConditionEvaluator (creates default if None)
        """
        self.schedule_manager = schedule_manager
        self.playlist_manager = playlist_manager
        self.instance_manager = instance_manager
        self.device_config = device_config
        self.condition_evaluator = condition_evaluator or ConditionEvaluator()

        # State tracking
        self.running = False
        self.paused = False
        self.current_slot: Optional[TimeSlot] = None
        self.current_playlist: Optional[Playlist] = None
        self.current_playlist_index: int = 0
        self.current_item_start: Optional[datetime] = None
        self.last_content_source: Optional[ContentSource] = None
        self.last_displayed_instance_id: Optional[str] = None
        self.last_refresh: Optional[datetime] = None

        # For random mode, track history to avoid immediate repeats
        self._random_history: List[str] = []
        self._max_history_size = 5

        # Plugin-driven refresh: track active plugin thread
        self._active_plugin_thread: Optional[threading.Thread] = None
        self._active_plugin_stop_event: Optional[threading.Event] = None
        self._active_instance_id: Optional[str] = None

    def get_current_content_source(self) -> ContentSource:
        """
        Determine what content should be displayed RIGHT NOW.

        This is the core method that evaluates:
        1. Active time slot for current time
        2. Target resolution (playlist or instance)
        3. Playlist item selection based on playback mode

        Returns:
            ContentSource describing what to display
        """
        # Step 1: Find active time slot
        slot = self.schedule_manager.get_current_slot()

        if slot is None:
            # No slot assigned for this time
            logger.debug("No slot assigned for current time")
            return ContentSource.empty()

        # Step 2: Resolve target based on slot type
        if slot.target_type == TargetType.PLAYLIST.value:
            return self._resolve_playlist_content(slot)
        else:
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
        now = datetime.now()
        minutes_remaining = 60 - now.minute
        duration = minutes_remaining * 60 - now.second

        return ContentSource(
            instance=instance,
            duration_seconds=max(duration, 60),  # At least 1 minute
            source_type="schedule",
            source_id=slot.key,
            source_name=instance.name,
        )

    def _resolve_playlist_content(self, slot: TimeSlot) -> ContentSource:
        """
        Resolve a time slot that targets a playlist.

        Args:
            slot: Time slot with target_type="playlist"

        Returns:
            ContentSource for the current playlist item
        """
        playlist = self.playlist_manager.get_playlist(slot.target_id)

        if not playlist:
            logger.error(f"Playlist not found: {slot.target_id}")
            return ContentSource.empty()

        if not playlist.enabled:
            logger.warning(f"Playlist is disabled: {slot.target_id}")
            return ContentSource.empty()

        if not playlist.items:
            logger.warning(f"Playlist has no items: {slot.target_id}")
            return ContentSource.empty()

        # Check if we're switching to a different playlist
        if self.current_playlist is None or self.current_playlist.id != playlist.id:
            self._switch_to_playlist(playlist)

        # Get valid items (those whose conditions are met)
        valid_items = self._get_valid_playlist_items(playlist)

        if not valid_items:
            logger.warning(f"No valid items in playlist: {playlist.name}")
            return ContentSource.empty()

        # Check if we need to advance to next item
        if self._should_advance_playlist():
            self._advance_playlist(playlist, valid_items)

        # Get current item
        item = self._get_current_playlist_item(playlist, valid_items)

        if item is None:
            return ContentSource.empty()

        instance = self.instance_manager.get_instance(item.instance_id)
        if not instance:
            logger.error(f"Instance not found: {item.instance_id}")
            return ContentSource.empty()

        if not instance.enabled:
            logger.warning(f"Instance is disabled: {item.instance_id}")
            # Try next item
            self._advance_playlist(playlist, valid_items)
            return self._resolve_playlist_content(slot)

        return ContentSource(
            instance=instance,
            duration_seconds=item.duration_seconds,
            source_type="playlist",
            source_id=playlist.id,
            source_name=playlist.name,
            playlist_index=self.current_playlist_index,
            playlist_total=len(valid_items),
        )

    def _get_valid_playlist_items(self, playlist: Playlist) -> List[PlaylistItem]:
        """
        Get playlist items whose conditions are currently met.

        Args:
            playlist: The playlist to filter

        Returns:
            List of valid playlist items
        """
        valid = []
        for item in playlist.items:
            if self.condition_evaluator.evaluate(item.conditions):
                valid.append(item)
        return valid

    def _switch_to_playlist(self, playlist: Playlist) -> None:
        """
        Switch to a new playlist, resetting state.

        Args:
            playlist: The playlist to switch to
        """
        logger.info(f"Switching to playlist: {playlist.name}")
        self.current_playlist = playlist
        self.current_playlist_index = 0
        self.current_item_start = None
        self._random_history.clear()

    def _should_advance_playlist(self) -> bool:
        """
        Check if it's time to advance to the next playlist item.

        Returns:
            True if should advance
        """
        if self.current_item_start is None:
            return False  # First item, don't advance yet

        if self.current_playlist is None:
            return False

        # Get current item
        items = self.current_playlist.items
        if not items or self.current_playlist_index >= len(items):
            return False

        current_item = items[self.current_playlist_index]
        elapsed = (datetime.now() - self.current_item_start).total_seconds()

        return elapsed >= current_item.duration_seconds

    def _advance_playlist(
        self, playlist: Playlist, valid_items: List[PlaylistItem]
    ) -> None:
        """
        Advance to the next playlist item.

        Args:
            playlist: Current playlist
            valid_items: List of valid items to choose from
        """
        if not valid_items:
            return

        playback_mode = playlist.playback_mode

        if playback_mode == PlaybackMode.SEQUENTIAL.value:
            self.current_playlist_index = (
                self.current_playlist_index + 1
            ) % len(valid_items)

        elif playback_mode == PlaybackMode.RANDOM.value:
            # Avoid immediate repeat if possible
            available = [
                i for i, item in enumerate(valid_items)
                if item.instance_id not in self._random_history
            ]
            if not available:
                # All items have been shown recently, reset history
                self._random_history.clear()
                available = list(range(len(valid_items)))

            self.current_playlist_index = random.choice(available)

            # Update history
            current_item = valid_items[self.current_playlist_index]
            self._random_history.append(current_item.instance_id)
            if len(self._random_history) > self._max_history_size:
                self._random_history.pop(0)

        elif playback_mode == PlaybackMode.WEIGHTED_RANDOM.value:
            weights = [item.weight for item in valid_items]
            self.current_playlist_index = random.choices(
                range(len(valid_items)), weights=weights
            )[0]

        else:
            # Default to sequential
            self.current_playlist_index = (
                self.current_playlist_index + 1
            ) % len(valid_items)

        self.current_item_start = None  # Will be set when item is displayed
        logger.info(
            f"Advanced to playlist item {self.current_playlist_index + 1}/{len(valid_items)}"
        )

    def _get_current_playlist_item(
        self, playlist: Playlist, valid_items: List[PlaylistItem]
    ) -> Optional[PlaylistItem]:
        """
        Get the current playlist item.

        Args:
            playlist: Current playlist
            valid_items: List of valid items

        Returns:
            Current PlaylistItem or None
        """
        if not valid_items:
            return None

        # Ensure index is in bounds
        if self.current_playlist_index >= len(valid_items):
            self.current_playlist_index = 0

        return valid_items[self.current_playlist_index]

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

        # For playlists, check if item duration has elapsed
        if content_source.source_type == "playlist":
            if self.current_item_start:
                elapsed = (datetime.now() - self.current_item_start).total_seconds()
                if elapsed >= content_source.duration_seconds:
                    return True

        # Check if plugin's refresh interval (cache_ttl) has elapsed
        if content_source.instance and self.current_item_start:
            plugin = get_plugin(content_source.instance.plugin_id)
            if plugin and hasattr(plugin, 'get_cache_ttl'):
                try:
                    ttl = plugin.get_cache_ttl(content_source.instance.settings)
                    elapsed = (datetime.now() - self.current_item_start).total_seconds()
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
            self.current_item_start = datetime.now()
            self.last_refresh = datetime.now()

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
                    self._switch_active_plugin(
                        content_source, display_controller
                    )

                # Sleep until next hour boundary
                sleep_seconds = self._seconds_until_next_hour()
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

    def _seconds_until_next_hour(self) -> int:
        """Calculate seconds until the next hour boundary."""
        now = datetime.now()
        # Next hour starts at minute=0, second=0
        seconds_into_hour = now.minute * 60 + now.second
        seconds_until_next = 3600 - seconds_into_hour
        # Add a small buffer to ensure we're past the boundary
        return seconds_until_next + 1

    def _switch_active_plugin(
        self, content_source: ContentSource, display_controller
    ) -> None:
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

        # Start plugin in its own thread
        self._active_plugin_thread = threading.Thread(
            target=self._run_plugin_active,
            args=(plugin, display_controller, instance.settings, self.device_config),
            daemon=True,
            name=f"plugin-{instance.plugin_id}",
        )
        self._active_plugin_thread.start()

        logger.info(f"Started plugin: {instance.name} ({instance.plugin_id})")

    def _run_plugin_active(
        self, plugin, display_controller, settings: Dict[str, Any], device_config: Dict[str, Any]
    ) -> None:
        """Wrapper to run plugin's run_active method."""
        try:
            plugin.run_active(
                display_controller,
                settings,
                device_config,
                self._active_plugin_stop_event,
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

    def _calculate_sleep_duration(self, content_source: ContentSource) -> int:
        """
        Calculate optimal sleep duration until next check.

        Args:
            content_source: Current content source

        Returns:
            Seconds to sleep
        """
        if content_source.is_empty():
            return 60  # Check every minute when nothing is scheduled

        # Check plugin's refresh interval (cache_ttl)
        if content_source.instance and self.current_item_start:
            plugin = get_plugin(content_source.instance.plugin_id)
            if plugin and hasattr(plugin, 'get_cache_ttl'):
                try:
                    ttl = plugin.get_cache_ttl(content_source.instance.settings)
                    elapsed = (datetime.now() - self.current_item_start).total_seconds()
                    remaining = ttl - elapsed
                    if remaining > 0:
                        return max(1, int(remaining))
                    else:
                        return 1  # Time to refresh
                except Exception:
                    pass

        if content_source.source_type == "playlist" and self.current_item_start:
            # Calculate time until current item expires
            elapsed = (datetime.now() - self.current_item_start).total_seconds()
            remaining = content_source.duration_seconds - elapsed
            return max(1, int(remaining))

        return 30  # Default check interval

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
            datetime: Next update time
        """
        from datetime import timedelta

        now = datetime.now()
        # Next hour starts at minute=0, second=0
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour

    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get scheduler status for API.

        Returns:
            Dictionary with scheduler state
        """
        # Get current time in configured timezone
        timezone = self.schedule_manager.timezone
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)

        return {
            "paused": self.paused,
            "update_time": f"{now.hour:02d}:00",  # Current hour slot
            "next_update": self.get_next_update_time().isoformat(),
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": timezone,
        }

    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status for API/UI.

        Returns:
            Dictionary with current state information
        """
        content_source = self.get_current_content_source()

        status = {
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

        if content_source.source_type == "playlist":
            status["playlist"] = {
                "index": content_source.playlist_index,
                "total": content_source.playlist_total,
                "playback_mode": (
                    self.current_playlist.playback_mode
                    if self.current_playlist
                    else "unknown"
                ),
            }

            if self.current_item_start:
                elapsed = (datetime.now() - self.current_item_start).total_seconds()
                status["playlist"]["elapsed_seconds"] = int(elapsed)
                status["playlist"]["remaining_seconds"] = max(
                    0, content_source.duration_seconds - int(elapsed)
                )

        # Add current slot info
        slot = self.schedule_manager.get_current_slot()
        if slot:
            status["slot"] = {
                "day": slot.day,
                "hour": slot.hour,
                "target_type": slot.target_type,
                "target_id": slot.target_id,
            }

        # Add condition context
        status["condition_context"] = self.condition_evaluator.get_current_context()

        return status

"""
Playlist executor for running playlists and displaying content.

Executes plugin instances from playlists and manages display timing.
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..models import Playlist, PlaylistItem
from ..plugins import get_plugin
from ..plugins.instance_manager import InstanceManager
from .playlist_manager import PlaylistManager


logger = logging.getLogger(__name__)


class PlaylistExecutor:
    """
    Executes playlists by running plugin instances and displaying content.

    Manages the timing and execution of playlist items.
    """

    def __init__(
        self,
        playlist_manager: PlaylistManager,
        instance_manager: InstanceManager,
        device_config: Dict[str, Any],
    ):
        """
        Initialize playlist executor.

        Args:
            playlist_manager: PlaylistManager instance
            instance_manager: InstanceManager instance
            device_config: Display device configuration
        """
        self.playlist_manager = playlist_manager
        self.instance_manager = instance_manager
        self.device_config = device_config

        self.current_item_index = 0
        self.current_item_start_time: Optional[datetime] = None
        self.running = False

    def get_active_playlist(self) -> Optional[Playlist]:
        """Get the currently active playlist."""
        return self.playlist_manager.get_active_playlist()

    def should_advance_to_next_item(self) -> bool:
        """
        Check if it's time to advance to the next playlist item.

        Returns:
            True if should advance, False otherwise
        """
        if self.current_item_start_time is None:
            return True  # No item currently playing

        playlist = self.get_active_playlist()
        if not playlist or not playlist.items:
            return False

        current_item = playlist.items[self.current_item_index]
        elapsed_seconds = (datetime.now() - self.current_item_start_time).total_seconds()

        return elapsed_seconds >= current_item.duration_seconds

    def execute_current_item(self) -> Optional[Any]:
        """
        Execute the current playlist item and generate content.

        Returns:
            Generated image or None if failed
        """
        playlist = self.get_active_playlist()
        if not playlist or not playlist.items:
            logger.warning("No active playlist or empty playlist")
            return None

        # Get current item
        current_item = playlist.items[self.current_item_index]

        try:
            # Get the instance
            instance = self.instance_manager.get_instance(current_item.instance_id)
            if not instance:
                logger.error(f"Instance not found: {current_item.instance_id}")
                return None

            if not instance.enabled:
                logger.warning(f"Instance is disabled: {current_item.instance_id}")
                return None

            # Get the plugin
            plugin = get_plugin(instance.plugin_id)
            if not plugin:
                logger.error(f"Plugin not found: {instance.plugin_id}")
                return None

            # Generate image
            logger.info(
                f"Executing playlist item: {instance.name} "
                f"({current_item.duration_seconds}s duration)"
            )

            image = plugin.generate_image(instance.settings, self.device_config)

            # Mark start time
            self.current_item_start_time = datetime.now()

            return image

        except Exception as e:
            logger.error(f"Failed to execute playlist item: {e}", exc_info=True)
            return None

    def advance_to_next_item(self) -> None:
        """Advance to the next item in the playlist."""
        playlist = self.get_active_playlist()
        if not playlist or not playlist.items:
            return

        self.current_item_index = (self.current_item_index + 1) % len(playlist.items)
        self.current_item_start_time = None

        logger.info(
            f"Advanced to playlist item {self.current_item_index + 1}/{len(playlist.items)}"
        )

    def reset_playlist(self) -> None:
        """Reset playlist to the beginning."""
        self.current_item_index = 0
        self.current_item_start_time = None
        logger.info("Playlist reset to beginning")

    def get_current_item_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently playing item.

        Returns:
            Dictionary with item info or None
        """
        playlist = self.get_active_playlist()
        if not playlist or not playlist.items:
            return None

        current_item = playlist.items[self.current_item_index]
        instance = self.instance_manager.get_instance(current_item.instance_id)

        if not instance:
            return None

        elapsed = 0
        remaining = current_item.duration_seconds

        if self.current_item_start_time:
            elapsed = int((datetime.now() - self.current_item_start_time).total_seconds())
            remaining = max(0, current_item.duration_seconds - elapsed)

        return {
            "playlist_name": playlist.name,
            "instance_name": instance.name,
            "plugin_id": instance.plugin_id,
            "item_index": self.current_item_index,
            "total_items": len(playlist.items),
            "duration_seconds": current_item.duration_seconds,
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
        }

    def run_loop(self, display_controller, check_interval: int = 5) -> None:
        """
        Run the playlist execution loop.

        This is the main loop that continuously executes playlist items
        and displays them.

        Args:
            display_controller: DisplayController instance
            check_interval: Seconds between checks
        """
        self.running = True
        logger.info("Playlist executor loop started")

        while self.running:
            try:
                # Check if there's an active playlist
                playlist = self.get_active_playlist()

                if not playlist:
                    # No active playlist, just wait
                    logger.debug("No active playlist, waiting...")
                    time.sleep(check_interval)
                    continue

                if not playlist.items:
                    # Empty playlist
                    logger.warning("Active playlist has no items")
                    time.sleep(check_interval)
                    continue

                # Check if we should advance to next item
                if self.should_advance_to_next_item():
                    # Execute and display current item
                    image = self.execute_current_item()

                    if image:
                        # Display the image
                        try:
                            display_controller.display_image(image)
                            logger.info("Successfully displayed playlist item")
                        except Exception as e:
                            logger.error(f"Failed to display image: {e}", exc_info=True)

                        # Advance to next item for next iteration
                        self.advance_to_next_item()
                    else:
                        logger.error("Failed to generate image, advancing to next item")
                        self.advance_to_next_item()

                # Sleep for a bit before checking again
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("Playlist executor interrupted")
                self.running = False
                break

            except Exception as e:
                logger.error(f"Error in playlist executor loop: {e}", exc_info=True)
                time.sleep(check_interval)

        logger.info("Playlist executor loop stopped")

    def stop(self) -> None:
        """Stop the playlist executor loop."""
        logger.info("Stopping playlist executor")
        self.running = False

"""
Playlist manager for managing content playlists.

Manages creation, storage, and lifecycle of playlists.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Playlist, PlaylistItem

logger = logging.getLogger(__name__)


class PlaylistManager:
    """
    Manages playlists.

    Provides CRUD operations for playlists with persistence
    to JSON storage.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize playlist manager.

        Args:
            storage_dir: Directory for storing playlist data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.playlists_file = self.storage_dir / "playlists.json"
        self._playlists: Dict[str, Playlist] = {}
        self._active_playlist_id: Optional[str] = None

        # Load existing playlists
        self._load_playlists()

    def _load_playlists(self) -> None:
        """Load playlists from storage."""
        if not self.playlists_file.exists():
            logger.info("No existing playlists found")
            return

        try:
            with open(self.playlists_file, "r") as f:
                data = json.load(f)

            self._active_playlist_id = data.get("active_playlist_id")

            for playlist_data in data.get("playlists", []):
                items = [
                    PlaylistItem(
                        instance_id=item["instance_id"],
                        duration_seconds=item["duration_seconds"],
                        order=item["order"],
                    )
                    for item in playlist_data["items"]
                ]

                playlist = Playlist(
                    id=playlist_data["id"],
                    name=playlist_data["name"],
                    description=playlist_data["description"],
                    enabled=playlist_data["enabled"],
                    items=items,
                    created_at=datetime.fromisoformat(playlist_data["created_at"]),
                    updated_at=datetime.fromisoformat(playlist_data["updated_at"]),
                )
                self._playlists[playlist.id] = playlist

            logger.info(f"Loaded {len(self._playlists)} playlists")

        except Exception as e:
            logger.error(f"Failed to load playlists: {e}", exc_info=True)

    def _save_playlists(self) -> None:
        """Save playlists to storage."""
        try:
            data = {
                "playlists": [
                    {
                        "id": playlist.id,
                        "name": playlist.name,
                        "description": playlist.description,
                        "enabled": playlist.enabled,
                        "items": [
                            {
                                "instance_id": item.instance_id,
                                "duration_seconds": item.duration_seconds,
                                "order": item.order,
                            }
                            for item in playlist.items
                        ],
                        "created_at": playlist.created_at.isoformat(),
                        "updated_at": playlist.updated_at.isoformat(),
                    }
                    for playlist in self._playlists.values()
                ],
                "active_playlist_id": self._active_playlist_id,
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.playlists_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved playlists")

        except Exception as e:
            logger.error(f"Failed to save playlists: {e}", exc_info=True)

    def create_playlist(
        self, name: str, description: str = "", items: Optional[List[PlaylistItem]] = None
    ) -> Playlist:
        """
        Create a new playlist.

        Args:
            name: Human-readable name for playlist
            description: Optional description
            items: Initial playlist items

        Returns:
            Created Playlist
        """
        playlist = Playlist(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            enabled=True,
            items=items or [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self._playlists[playlist.id] = playlist
        self._save_playlists()

        logger.info(f"Created playlist {playlist.name} ({playlist.id})")
        return playlist

    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        Get playlist by ID.

        Args:
            playlist_id: Playlist identifier

        Returns:
            Playlist if found, None otherwise
        """
        return self._playlists.get(playlist_id)

    def list_playlists(self) -> List[Playlist]:
        """
        List all playlists.

        Returns:
            List of Playlist objects
        """
        return list(self._playlists.values())

    def update_playlist(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        items: Optional[List[PlaylistItem]] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """
        Update an existing playlist.

        Args:
            playlist_id: Playlist identifier
            name: Optional new name
            description: Optional new description
            items: Optional new items list
            enabled: Optional enabled state

        Returns:
            True if updated successfully
        """
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            logger.error(f"Playlist not found: {playlist_id}")
            return False

        if name is not None:
            playlist.name = name

        if description is not None:
            playlist.description = description

        if items is not None:
            playlist.items = items

        if enabled is not None:
            playlist.enabled = enabled

        playlist.updated_at = datetime.now()
        self._save_playlists()

        logger.info(f"Updated playlist {playlist.name} ({playlist_id})")
        return True

    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.

        Args:
            playlist_id: Playlist identifier

        Returns:
            True if deleted successfully
        """
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            logger.error(f"Playlist not found: {playlist_id}")
            return False

        # If this was the active playlist, clear it
        if self._active_playlist_id == playlist_id:
            self._active_playlist_id = None

        del self._playlists[playlist_id]
        self._save_playlists()

        logger.info(f"Deleted playlist {playlist.name} ({playlist_id})")
        return True

    def set_active_playlist(self, playlist_id: Optional[str]) -> bool:
        """
        Set the active playlist.

        Args:
            playlist_id: Playlist identifier, or None to deactivate

        Returns:
            True if set successfully
        """
        if playlist_id is not None:
            playlist = self._playlists.get(playlist_id)
            if playlist is None:
                logger.error(f"Playlist not found: {playlist_id}")
                return False

            if not playlist.enabled:
                logger.error(f"Cannot activate disabled playlist: {playlist_id}")
                return False

        self._active_playlist_id = playlist_id
        self._save_playlists()

        if playlist_id:
            logger.info(f"Set active playlist to {playlist_id}")
        else:
            logger.info("Cleared active playlist")

        return True

    def get_active_playlist(self) -> Optional[Playlist]:
        """
        Get the currently active playlist.

        Returns:
            Active Playlist if set, None otherwise
        """
        if self._active_playlist_id is None:
            return None

        return self._playlists.get(self._active_playlist_id)

    def get_active_playlist_id(self) -> Optional[str]:
        """Get the ID of the active playlist."""
        return self._active_playlist_id

    def add_item(
        self, playlist_id: str, instance_id: str, duration_seconds: int, order: Optional[int] = None
    ) -> bool:
        """
        Add an item to a playlist.

        Args:
            playlist_id: Playlist identifier
            instance_id: Plugin instance identifier
            duration_seconds: How long to display
            order: Optional position, defaults to end

        Returns:
            True if added successfully
        """
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            logger.error(f"Playlist not found: {playlist_id}")
            return False

        if order is None:
            order = len(playlist.items)

        item = PlaylistItem(instance_id=instance_id, duration_seconds=duration_seconds, order=order)

        playlist.items.append(item)
        playlist.items.sort(key=lambda x: x.order)
        playlist.updated_at = datetime.now()

        self._save_playlists()

        logger.info(f"Added item to playlist {playlist_id}")
        return True

    def remove_item(self, playlist_id: str, instance_id: str) -> bool:
        """
        Remove an item from a playlist.

        Args:
            playlist_id: Playlist identifier
            instance_id: Plugin instance identifier to remove

        Returns:
            True if removed successfully
        """
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            logger.error(f"Playlist not found: {playlist_id}")
            return False

        original_count = len(playlist.items)
        playlist.items = [item for item in playlist.items if item.instance_id != instance_id]

        if len(playlist.items) == original_count:
            logger.warning(f"Instance {instance_id} not found in playlist {playlist_id}")
            return False

        # Re-order remaining items
        for i, item in enumerate(playlist.items):
            item.order = i

        playlist.updated_at = datetime.now()
        self._save_playlists()

        logger.info(f"Removed item from playlist {playlist_id}")
        return True

    def get_playlist_count(self) -> int:
        """Get total number of playlists."""
        return len(self._playlists)

    def get_enabled_playlists(self) -> List[Playlist]:
        """Get all enabled playlists."""
        return [pl for pl in self._playlists.values() if pl.enabled]

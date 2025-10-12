"""
Schedule manager for time-based content scheduling.

Manages schedule entries that define when specific plugin instances should display.
"""

import json
import uuid
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models import ScheduleEntry, ScheduleConfig


logger = logging.getLogger(__name__)


class ScheduleManager:
    """
    Manages time-based schedule entries.

    Unlike playlists which play sequentially, schedules are evaluated
    based on current time to determine what should display right now.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize schedule manager.

        Args:
            storage_dir: Directory for storing schedule data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.schedules_file = self.storage_dir / "schedules.json"
        self._entries: Dict[str, ScheduleEntry] = {}
        self._config: ScheduleConfig = ScheduleConfig(default_instance_id=None)

        # Load existing schedules
        self._load_schedules()

    def _load_schedules(self) -> None:
        """Load schedules from storage."""
        if not self.schedules_file.exists():
            logger.info("No existing schedules found")
            return

        try:
            with open(self.schedules_file, "r") as f:
                data = json.load(f)

            # Load config
            config_data = data.get("config", {})
            self._config = ScheduleConfig(
                default_instance_id=config_data.get("default_instance_id"),
                check_interval_seconds=config_data.get("check_interval_seconds", 60),
            )

            # Load entries
            for entry_data in data.get("entries", []):
                entry = ScheduleEntry(
                    id=entry_data["id"],
                    name=entry_data["name"],
                    instance_id=entry_data["instance_id"],
                    start_time=entry_data["start_time"],
                    end_time=entry_data["end_time"],
                    days_of_week=entry_data["days_of_week"],
                    priority=entry_data["priority"],
                    enabled=entry_data["enabled"],
                    created_at=datetime.fromisoformat(entry_data["created_at"]),
                    updated_at=datetime.fromisoformat(entry_data["updated_at"]),
                )
                self._entries[entry.id] = entry

            logger.info(f"Loaded {len(self._entries)} schedule entries")

        except Exception as e:
            logger.error(f"Failed to load schedules: {e}", exc_info=True)

    def _save_schedules(self) -> None:
        """Save schedules to storage."""
        try:
            data = {
                "config": {
                    "default_instance_id": self._config.default_instance_id,
                    "check_interval_seconds": self._config.check_interval_seconds,
                },
                "entries": [
                    {
                        "id": entry.id,
                        "name": entry.name,
                        "instance_id": entry.instance_id,
                        "start_time": entry.start_time,
                        "end_time": entry.end_time,
                        "days_of_week": entry.days_of_week,
                        "priority": entry.priority,
                        "enabled": entry.enabled,
                        "created_at": entry.created_at.isoformat(),
                        "updated_at": entry.updated_at.isoformat(),
                    }
                    for entry in self._entries.values()
                ],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.schedules_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved schedules")

        except Exception as e:
            logger.error(f"Failed to save schedules: {e}", exc_info=True)

    def create_entry(
        self,
        name: str,
        instance_id: str,
        start_time: str,
        end_time: str,
        days_of_week: List[int],
        priority: int = 5,
    ) -> ScheduleEntry:
        """
        Create a new schedule entry.

        Args:
            name: Human-readable name for schedule entry
            instance_id: Plugin instance to display
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            days_of_week: List of days (0=Monday, 6=Sunday)
            priority: Priority level (higher = more important)

        Returns:
            Created ScheduleEntry
        """
        entry = ScheduleEntry(
            id=str(uuid.uuid4()),
            name=name,
            instance_id=instance_id,
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week,
            priority=priority,
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self._entries[entry.id] = entry
        self._save_schedules()

        logger.info(f"Created schedule entry {entry.name} ({entry.id})")
        return entry

    def get_entry(self, entry_id: str) -> Optional[ScheduleEntry]:
        """Get entry by ID."""
        return self._entries.get(entry_id)

    def list_entries(self) -> List[ScheduleEntry]:
        """List all schedule entries."""
        return list(self._entries.values())

    def update_entry(
        self,
        entry_id: str,
        name: Optional[str] = None,
        instance_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        days_of_week: Optional[List[int]] = None,
        priority: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """Update an existing schedule entry."""
        entry = self._entries.get(entry_id)
        if entry is None:
            logger.error(f"Schedule entry not found: {entry_id}")
            return False

        if name is not None:
            entry.name = name
        if instance_id is not None:
            entry.instance_id = instance_id
        if start_time is not None:
            entry.start_time = start_time
        if end_time is not None:
            entry.end_time = end_time
        if days_of_week is not None:
            entry.days_of_week = days_of_week
        if priority is not None:
            entry.priority = priority
        if enabled is not None:
            entry.enabled = enabled

        entry.updated_at = datetime.now()
        self._save_schedules()

        logger.info(f"Updated schedule entry {entry.name} ({entry_id})")
        return True

    def delete_entry(self, entry_id: str) -> bool:
        """Delete a schedule entry."""
        entry = self._entries.get(entry_id)
        if entry is None:
            logger.error(f"Schedule entry not found: {entry_id}")
            return False

        del self._entries[entry_id]
        self._save_schedules()

        logger.info(f"Deleted schedule entry {entry.name} ({entry_id})")
        return True

    def get_current_entry(self, current_time: Optional[datetime] = None) -> Optional[ScheduleEntry]:
        """
        Get the schedule entry that should be active right now.

        Evaluates all enabled entries and returns the highest priority match
        for the current time and day of week.

        Args:
            current_time: Time to evaluate (defaults to now)

        Returns:
            Highest priority matching ScheduleEntry, or None if no match
        """
        if current_time is None:
            current_time = datetime.now()

        current_day = current_time.weekday()  # 0=Monday, 6=Sunday
        current_time_str = current_time.strftime("%H:%M")

        # Find all matching entries
        matching_entries = []
        for entry in self._entries.values():
            if not entry.enabled:
                continue

            # Check if current day matches
            if current_day not in entry.days_of_week:
                continue

            # Check if current time is within range
            if self._time_in_range(current_time_str, entry.start_time, entry.end_time):
                matching_entries.append(entry)

        if not matching_entries:
            return None

        # Return highest priority entry
        matching_entries.sort(key=lambda e: e.priority, reverse=True)
        return matching_entries[0]

    def _time_in_range(self, current: str, start: str, end: str) -> bool:
        """
        Check if current time is within start and end time range.

        Args:
            current: Current time in HH:MM format
            start: Start time in HH:MM format
            end: End time in HH:MM format

        Returns:
            True if current is within [start, end)
        """
        try:
            current_t = datetime.strptime(current, "%H:%M").time()
            start_t = datetime.strptime(start, "%H:%M").time()
            end_t = datetime.strptime(end, "%H:%M").time()

            if start_t <= end_t:
                # Normal range (e.g., 08:00 to 17:00)
                return start_t <= current_t < end_t
            else:
                # Overnight range (e.g., 22:00 to 02:00)
                return current_t >= start_t or current_t < end_t

        except ValueError as e:
            logger.error(f"Invalid time format: {e}")
            return False

    def set_default_instance(self, instance_id: Optional[str]) -> None:
        """Set the default instance to show when nothing is scheduled."""
        self._config.default_instance_id = instance_id
        self._save_schedules()
        logger.info(f"Set default instance to {instance_id}")

    def get_default_instance_id(self) -> Optional[str]:
        """Get the default instance ID."""
        return self._config.default_instance_id

    def get_config(self) -> ScheduleConfig:
        """Get the schedule configuration."""
        return self._config

    def get_entry_count(self) -> int:
        """Get total number of schedule entries."""
        return len(self._entries)

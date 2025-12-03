"""
Schedule manager for slot-based content scheduling.

Simple timetable model: each hour slot on each day can have
exactly one content assignment (instance or playlist).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from ..models import TimeSlot

logger = logging.getLogger(__name__)


class ScheduleManager:
    """
    Manages slot-based schedule assignments.

    Simple model: 7 days x 24 hours = 168 possible slots.
    Each slot can have one assignment (instance or playlist).
    No overlapping, no priorities - just direct slot assignments.
    """

    def __init__(self, storage_dir: Path, timezone: str = "UTC"):
        """
        Initialize schedule manager.

        Args:
            storage_dir: Directory for storing schedule data
            timezone: IANA timezone string (e.g. "Australia/Sydney")
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timezone = timezone

        self.schedules_file = self.storage_dir / "schedules.json"
        self._slots: Dict[str, TimeSlot] = {}  # key: "day-hour" -> TimeSlot

        # Load existing schedule
        self._load_schedule()

    def _load_schedule(self) -> None:
        """Load schedule from storage."""
        if not self.schedules_file.exists():
            logger.info("No existing schedule found")
            return

        try:
            with open(self.schedules_file, "r") as f:
                data = json.load(f)

            # Load slots
            slots_data = data.get("slots", {})
            for key, slot_data in slots_data.items():
                self._slots[key] = TimeSlot.from_key(
                    key,
                    target_type=slot_data["target_type"],
                    target_id=slot_data["target_id"],
                )

            logger.info(f"Loaded {len(self._slots)} schedule slots")

        except Exception as e:
            logger.error(f"Failed to load schedule: {e}", exc_info=True)

    def _save_schedule(self) -> None:
        """Save schedule to storage."""
        try:
            data = {
                "slots": {
                    key: {
                        "target_type": slot.target_type,
                        "target_id": slot.target_id,
                    }
                    for key, slot in self._slots.items()
                },
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.schedules_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved schedule")

        except Exception as e:
            logger.error(f"Failed to save schedule: {e}", exc_info=True)

    def set_slot(
        self,
        day: int,
        hour: int,
        target_type: str,
        target_id: str,
    ) -> TimeSlot:
        """
        Assign content to a specific time slot.

        Args:
            day: Day of week (0=Monday, 6=Sunday)
            hour: Hour of day (0-23)
            target_type: "instance" or "playlist"
            target_id: The ID of the instance or playlist

        Returns:
            The created/updated TimeSlot
        """
        slot = TimeSlot(
            day=day,
            hour=hour,
            target_type=target_type,
            target_id=target_id,
        )

        self._slots[slot.key] = slot
        self._save_schedule()

        logger.info(f"Set slot {slot.key} to {target_type}:{target_id}")
        return slot

    def clear_slot(self, day: int, hour: int) -> bool:
        """
        Clear a time slot assignment.

        Args:
            day: Day of week (0=Monday, 6=Sunday)
            hour: Hour of day (0-23)

        Returns:
            True if slot was cleared, False if it wasn't assigned
        """
        key = f"{day}-{hour}"
        if key in self._slots:
            del self._slots[key]
            self._save_schedule()
            logger.info(f"Cleared slot {key}")
            return True
        return False

    def get_slot(self, day: int, hour: int) -> Optional[TimeSlot]:
        """
        Get the assignment for a specific time slot.

        Args:
            day: Day of week (0=Monday, 6=Sunday)
            hour: Hour of day (0-23)

        Returns:
            TimeSlot if assigned, None otherwise
        """
        key = f"{day}-{hour}"
        return self._slots.get(key)

    def get_current_slot(self, current_time: Optional[datetime] = None) -> Optional[TimeSlot]:
        """
        Get the slot for the current time in the configured timezone.

        Args:
            current_time: Time to check (defaults to now in configured timezone)

        Returns:
            TimeSlot if assigned, None otherwise
        """
        if current_time is None:
            # Get current time in the configured timezone
            tz = ZoneInfo(self.timezone)
            current_time = datetime.now(tz)

        day = current_time.weekday()  # 0=Monday, 6=Sunday
        hour = current_time.hour

        return self.get_slot(day, hour)

    def get_all_slots(self) -> List[TimeSlot]:
        """Get all assigned slots."""
        return list(self._slots.values())

    def get_slots_for_day(self, day: int) -> List[TimeSlot]:
        """Get all slots assigned for a specific day."""
        return [slot for slot in self._slots.values() if slot.day == day]

    def get_slots_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Get all slots as a dictionary for JSON serialization.

        Returns:
            Dict mapping "day-hour" keys to {target_type, target_id}
        """
        return {
            key: {
                "target_type": slot.target_type,
                "target_id": slot.target_id,
            }
            for key, slot in self._slots.items()
        }

    def get_slot_count(self) -> int:
        """Get number of assigned slots."""
        return len(self._slots)

    def bulk_set_slots(
        self,
        slots: List[Dict[str, Any]],
    ) -> int:
        """
        Set multiple slots at once.

        Args:
            slots: List of dicts with day, hour, target_type, target_id

        Returns:
            Number of slots set
        """
        count = 0
        for slot_data in slots:
            slot = TimeSlot(
                day=slot_data["day"],
                hour=slot_data["hour"],
                target_type=slot_data["target_type"],
                target_id=slot_data["target_id"],
            )
            self._slots[slot.key] = slot
            count += 1

        self._save_schedule()
        logger.info(f"Bulk set {count} slots")
        return count

    def clear_all_slots(self) -> int:
        """Clear all slot assignments."""
        count = len(self._slots)
        self._slots.clear()
        self._save_schedule()
        logger.info(f"Cleared all {count} slots")
        return count

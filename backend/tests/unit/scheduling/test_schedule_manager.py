"""
Unit tests for ScheduleManager.

Tests cover:
- Time slot CRUD operations
- Current slot retrieval
- Schedule persistence
- Bulk operations
"""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.artframe.models import TimeSlot
from src.artframe.scheduling.schedule_manager import ScheduleManager


class TestScheduleManagerInitialization:
    """Tests for ScheduleManager initialization."""

    def test_creates_storage_directory(self, temp_dir: Path):
        """Should create storage directory if it doesn't exist."""
        storage_path = temp_dir / "schedules"
        manager = ScheduleManager(storage_dir=storage_path)

        assert storage_path.exists()

    def test_initializes_empty_slots(self, temp_dir: Path):
        """Should initialize with no slots."""
        manager = ScheduleManager(storage_dir=temp_dir)

        assert manager.get_slot_count() == 0

    def test_loads_existing_schedule(self, temp_dir: Path):
        """Should load existing schedule from storage."""
        # Create first manager and set a slot
        manager1 = ScheduleManager(storage_dir=temp_dir)
        manager1.set_slot(0, 9, "instance", "test_instance")

        # Create second manager - should load existing schedule
        manager2 = ScheduleManager(storage_dir=temp_dir)

        assert manager2.get_slot_count() == 1
        slot = manager2.get_slot(0, 9)
        assert slot is not None
        assert slot.target_id == "test_instance"

    def test_uses_provided_timezone(self, temp_dir: Path):
        """Should use provided timezone."""
        manager = ScheduleManager(storage_dir=temp_dir, timezone="Australia/Sydney")

        assert manager.timezone == "Australia/Sydney"


class TestSetSlot:
    """Tests for setting time slots."""

    def test_set_slot_creates_new(self, schedule_manager: ScheduleManager):
        """Should create a new time slot."""
        result = schedule_manager.set_slot(0, 9, "instance", "test_instance")

        assert result.day == 0
        assert result.hour == 9
        assert result.target_type == "instance"
        assert result.target_id == "test_instance"

    def test_set_slot_overwrites_existing(self, schedule_manager: ScheduleManager):
        """Should overwrite existing slot."""
        schedule_manager.set_slot(0, 9, "instance", "old_instance")
        schedule_manager.set_slot(0, 9, "instance", "new_instance")

        slot = schedule_manager.get_slot(0, 9)
        assert slot is not None
        assert slot.target_id == "new_instance"

    def test_set_slot_persists(self, temp_dir: Path):
        """Should persist slot to storage."""
        manager = ScheduleManager(storage_dir=temp_dir)
        manager.set_slot(1, 14, "instance", "persisted_instance")

        assert manager.schedules_file.exists()


class TestGetSlot:
    """Tests for getting time slots."""

    def test_get_slot_success(self, schedule_manager: ScheduleManager):
        """Should retrieve existing slot."""
        schedule_manager.set_slot(2, 10, "instance", "test_instance")

        result = schedule_manager.get_slot(2, 10)

        assert result is not None
        assert result.day == 2
        assert result.hour == 10

    def test_get_slot_not_found(self, schedule_manager: ScheduleManager):
        """Should return None for non-existent slot."""
        result = schedule_manager.get_slot(0, 0)

        assert result is None


class TestClearSlot:
    """Tests for clearing time slots."""

    def test_clear_slot_success(self, schedule_manager: ScheduleManager):
        """Should clear existing slot."""
        schedule_manager.set_slot(0, 9, "instance", "test_instance")

        result = schedule_manager.clear_slot(0, 9)

        assert result is True
        assert schedule_manager.get_slot(0, 9) is None

    def test_clear_slot_nonexistent(self, schedule_manager: ScheduleManager):
        """Should return False for non-existent slot."""
        result = schedule_manager.clear_slot(0, 0)

        assert result is False


class TestGetCurrentSlot:
    """Tests for getting current time slot."""

    def test_get_current_slot_with_match(self, schedule_manager: ScheduleManager):
        """Should return slot matching current time."""
        # Set slot for Monday 9 AM
        schedule_manager.set_slot(0, 9, "instance", "monday_9am_instance")

        # Test with a specific time (Monday 9:30 AM)
        test_time = datetime(2024, 6, 17, 9, 30, 0, tzinfo=ZoneInfo("UTC"))  # Monday

        result = schedule_manager.get_current_slot(test_time)

        assert result is not None
        assert result.target_id == "monday_9am_instance"

    def test_get_current_slot_no_match(self, schedule_manager: ScheduleManager):
        """Should return None when no slot matches."""
        # Set slot for Monday 9 AM only
        schedule_manager.set_slot(0, 9, "instance", "test_instance")

        # Test with a different time (Monday 10 AM)
        test_time = datetime(2024, 6, 17, 10, 30, 0, tzinfo=ZoneInfo("UTC"))

        result = schedule_manager.get_current_slot(test_time)

        assert result is None

    def test_get_current_slot_different_days(self, schedule_manager: ScheduleManager):
        """Should correctly match day of week."""
        schedule_manager.set_slot(0, 9, "instance", "monday_instance")  # Monday
        schedule_manager.set_slot(2, 9, "instance", "wednesday_instance")  # Wednesday

        # Test Monday
        monday = datetime(2024, 6, 17, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = schedule_manager.get_current_slot(monday)
        assert result is not None
        assert result.target_id == "monday_instance"

        # Test Wednesday
        wednesday = datetime(2024, 6, 19, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = schedule_manager.get_current_slot(wednesday)
        assert result is not None
        assert result.target_id == "wednesday_instance"


class TestGetAllSlots:
    """Tests for getting all slots."""

    def test_get_all_slots_empty(self, schedule_manager: ScheduleManager):
        """Should return empty list when no slots."""
        result = schedule_manager.get_all_slots()

        assert result == []

    def test_get_all_slots_returns_all(self, schedule_manager: ScheduleManager):
        """Should return all slots."""
        schedule_manager.set_slot(0, 9, "instance", "inst1")
        schedule_manager.set_slot(1, 10, "instance", "inst2")
        schedule_manager.set_slot(2, 11, "instance", "inst3")

        result = schedule_manager.get_all_slots()

        assert len(result) == 3


class TestGetSlotsForDay:
    """Tests for getting slots for a specific day."""

    def test_get_slots_for_day(self, schedule_manager: ScheduleManager):
        """Should return only slots for specified day."""
        schedule_manager.set_slot(0, 9, "instance", "monday_9")
        schedule_manager.set_slot(0, 10, "instance", "monday_10")
        schedule_manager.set_slot(1, 9, "instance", "tuesday_9")

        result = schedule_manager.get_slots_for_day(0)  # Monday

        assert len(result) == 2
        assert all(slot.day == 0 for slot in result)


class TestGetSlotsDict:
    """Tests for getting slots as dictionary."""

    def test_get_slots_dict(self, schedule_manager: ScheduleManager):
        """Should return slots as dictionary."""
        schedule_manager.set_slot(0, 9, "instance", "test_instance")

        result = schedule_manager.get_slots_dict()

        assert "0-9" in result
        assert result["0-9"]["target_type"] == "instance"
        assert result["0-9"]["target_id"] == "test_instance"


class TestBulkSetSlots:
    """Tests for bulk slot operations."""

    def test_bulk_set_slots(self, schedule_manager: ScheduleManager):
        """Should set multiple slots at once."""
        slots = [
            {"day": 0, "hour": 9, "target_type": "instance", "target_id": "inst1"},
            {"day": 0, "hour": 10, "target_type": "instance", "target_id": "inst2"},
            {"day": 1, "hour": 9, "target_type": "instance", "target_id": "inst3"},
        ]

        result = schedule_manager.bulk_set_slots(slots)

        assert result == 3
        assert schedule_manager.get_slot_count() == 3


class TestClearAllSlots:
    """Tests for clearing all slots."""

    def test_clear_all_slots(self, schedule_manager: ScheduleManager):
        """Should clear all slots."""
        schedule_manager.set_slot(0, 9, "instance", "inst1")
        schedule_manager.set_slot(1, 10, "instance", "inst2")

        result = schedule_manager.clear_all_slots()

        assert result == 2
        assert schedule_manager.get_slot_count() == 0


class TestGetNextScheduleChange:
    """Tests for finding next schedule change."""

    def test_get_next_schedule_change_finds_change(self, schedule_manager: ScheduleManager):
        """Should find when schedule changes to different instance."""
        # Set Monday 9-11 AM to one instance
        for hour in range(9, 11):
            schedule_manager.set_slot(0, hour, "instance", "morning_instance")

        # Set Monday 11 AM onwards to different instance
        schedule_manager.set_slot(0, 11, "instance", "different_instance")

        # Check from 9 AM
        test_time = datetime(2024, 6, 17, 9, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = schedule_manager.get_next_schedule_change(test_time)

        assert result is not None
        assert result.hour == 11

    def test_get_next_schedule_change_no_change(self, schedule_manager: ScheduleManager):
        """Should return None if same instance for entire week."""
        # Set all slots to same instance
        for day in range(7):
            for hour in range(24):
                schedule_manager.set_slot(day, hour, "instance", "same_instance")

        test_time = datetime(2024, 6, 17, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = schedule_manager.get_next_schedule_change(test_time)

        assert result is None

    def test_get_next_schedule_change_finds_gap(self, schedule_manager: ScheduleManager):
        """Should detect when schedule goes from instance to no instance."""
        # Set only Monday 9-10 AM
        schedule_manager.set_slot(0, 9, "instance", "test_instance")

        test_time = datetime(2024, 6, 17, 9, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = schedule_manager.get_next_schedule_change(test_time)

        assert result is not None
        assert result.hour == 10


class TestTimeSlotModel:
    """Tests for TimeSlot model."""

    def test_time_slot_key_property(self):
        """Should generate correct key."""
        slot = TimeSlot(day=0, hour=9, target_type="instance", target_id="test")

        assert slot.key == "0-9"

    def test_time_slot_from_key(self):
        """Should create TimeSlot from key."""
        slot = TimeSlot.from_key("2-14", "instance", "test_id")

        assert slot.day == 2
        assert slot.hour == 14
        assert slot.target_type == "instance"
        assert slot.target_id == "test_id"

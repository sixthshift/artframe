"""
Scheduling utilities for Artframe.
"""

from datetime import datetime, time
from typing import Dict, Any, Optional


class Scheduler:
    """Manages scheduling for daily updates with e-ink safety refresh."""

    def __init__(self, update_time: str = "06:00", timezone: Optional[str] = None):
        """
        Initialize scheduler.

        Args:
            update_time: Daily update time in HH:MM format
            timezone: Timezone name (not implemented in this basic version)
        """
        self.update_time = self._parse_time(update_time)
        self.timezone = timezone
        self.paused = False
        self.last_refresh_date: Optional[datetime] = None

    def _parse_time(self, time_str: str) -> time:
        """Parse time string into time object."""
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time values")
            return time(hour, minute)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format: {time_str}. Use HH:MM format")

    def is_update_time(self) -> bool:
        """
        Check if current time matches scheduled update time.

        E-ink safety: Even if paused, returns True once per day for refresh.

        Returns:
            bool: True if it's time for an update
        """
        now = datetime.now()
        now_time = now.time()
        today = now.date()

        # Check if we need daily e-ink refresh (even if paused)
        needs_daily_refresh = (
            self.last_refresh_date is None or self.last_refresh_date.date() < today
        )

        # At update time, always refresh (e-ink safety)
        is_scheduled_time = (
            now_time.hour == self.update_time.hour and now_time.minute == self.update_time.minute
        )

        if is_scheduled_time and needs_daily_refresh:
            return True

        # If not paused, also check scheduled time
        if not self.paused and is_scheduled_time:
            return True

        return False

    def mark_refreshed(self) -> None:
        """Mark that a refresh has occurred (for e-ink safety tracking)."""
        self.last_refresh_date = datetime.now()

    def pause(self) -> None:
        """
        Pause automatic updates.

        Note: Daily e-ink refresh will still occur for screen health.
        """
        self.paused = True

    def resume(self) -> None:
        """Resume automatic updates."""
        self.paused = False

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status.

        Returns:
            Dictionary with scheduler state
        """
        return {
            "paused": self.paused,
            "update_time": self.update_time.strftime("%H:%M"),
            "next_update": self.get_next_update_time().isoformat(),
            "last_refresh": self.last_refresh_date.isoformat() if self.last_refresh_date else None,
        }

    def seconds_until_next_update(self) -> int:
        """
        Calculate seconds until next scheduled update.

        Returns:
            int: Seconds until next update
        """
        now = datetime.now()

        # Create next update datetime
        next_update = datetime.combine(now.date(), self.update_time)

        # If update time has passed today, schedule for tomorrow
        if next_update <= now:
            from datetime import timedelta

            next_update += timedelta(days=1)

        delta = next_update - now
        return int(delta.total_seconds())

    def get_next_update_time(self) -> datetime:
        """
        Get the next scheduled update time.

        Returns:
            datetime: Next update time
        """
        now = datetime.now()
        next_update = datetime.combine(now.date(), self.update_time)

        if next_update <= now:
            from datetime import timedelta

            next_update += timedelta(days=1)

        return next_update

"""
Time utilities for timezone-aware operations.
"""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo


def now_in_tz(tz: ZoneInfo) -> datetime:
    """Get current time in the given timezone."""
    return datetime.now(tz)


def seconds_until_next_hour(tz: ZoneInfo) -> int:
    """
    Calculate seconds until the next hour boundary.

    Args:
        tz: Timezone to calculate in

    Returns:
        Seconds until next hour (with +1 buffer to ensure we're past boundary)
    """
    now = datetime.now(tz)
    seconds_into_hour = now.minute * 60 + now.second
    return 3600 - seconds_into_hour + 1


def datetime_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO format string, handling None.

    Args:
        dt: Datetime to convert, or None

    Returns:
        ISO format string, or None if input is None
    """
    return dt.isoformat() if dt else None

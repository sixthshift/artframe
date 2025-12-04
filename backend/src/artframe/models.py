"""
Data models for the Artframe system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TargetType(str, Enum):
    """Target type for schedule entries."""

    INSTANCE = "instance"


@dataclass
class Photo:
    """Represents a source photo with metadata."""

    id: str
    source_url: str
    retrieved_at: datetime
    original_path: Path
    metadata: dict[str, Any]


@dataclass
class StyledImage:
    """Represents a styled/transformed image."""

    original_photo_id: str
    style_name: str
    styled_path: Path
    created_at: datetime
    metadata: dict[str, Any]


@dataclass
class DisplayState:
    """Represents the current state of the display."""

    current_image_id: Optional[str]
    last_refresh: Optional[datetime]
    next_scheduled: Optional[datetime]
    error_count: int = 0
    status: str = "idle"  # idle, updating, error


@dataclass
class StorageStats:
    """Statistics about local storage."""

    total_photos: int
    total_styled_images: int
    total_size_mb: float
    storage_directory: str


@dataclass
class PluginInstance:
    """Represents an instance of a plugin with specific settings."""

    id: str
    plugin_id: str
    name: str
    settings: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class TimeSlot:
    """
    Represents a single time slot assignment.

    Each slot is one hour on one day of the week.
    Simple model: one slot = one content assignment.
    """

    day: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    target_type: str  # "instance"
    target_id: str  # instance_id

    @property
    def key(self) -> str:
        """Get the unique key for this slot (day-hour)."""
        return f"{self.day}-{self.hour}"

    @classmethod
    def from_key(cls, key: str, target_type: str, target_id: str) -> "TimeSlot":
        """Create a TimeSlot from a key string."""
        day, hour = key.split("-")
        return cls(
            day=int(day),
            hour=int(hour),
            target_type=target_type,
            target_id=target_id,
        )


@dataclass
class ScheduleConfig:
    """Global schedule configuration."""

    pass  # Placeholder for future config options


@dataclass
class ContentSource:
    """
    Represents what content should be displayed right now.

    This is the output of the ContentOrchestrator - it tells us exactly
    what instance to run, how long to show it, and where it came from.
    """

    # The plugin instance to execute (None if nothing to display)
    instance: Optional["PluginInstance"] = None
    # How long to display this content (seconds)
    duration_seconds: int = 0
    # Where this content came from
    source_type: str = "none"  # "schedule", "default", "none"
    source_id: Optional[str] = None  # slot key
    source_name: Optional[str] = None  # Human-readable source name

    @classmethod
    def empty(cls) -> "ContentSource":
        """Create an empty content source (nothing to display)."""
        return cls(
            instance=None,
            duration_seconds=0,
            source_type="none",
        )

    def is_empty(self) -> bool:
        """Check if this content source has nothing to display."""
        return self.instance is None

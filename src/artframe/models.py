"""
Data models for the Artframe system.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List


@dataclass
class Photo:
    """Represents a source photo with metadata."""
    id: str
    source_url: str
    retrieved_at: datetime
    original_path: Path
    metadata: Dict[str, Any]


@dataclass
class StyledImage:
    """Represents a styled/transformed image."""
    original_photo_id: str
    style_name: str
    styled_path: Path
    created_at: datetime
    metadata: Dict[str, Any]


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
    settings: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class PlaylistItem:
    """Represents a single item in a playlist."""
    instance_id: str
    duration_seconds: int
    order: int


@dataclass
class Playlist:
    """Represents a playlist of plugin instances."""
    id: str
    name: str
    description: str
    enabled: bool
    items: List[PlaylistItem]
    created_at: datetime
    updated_at: datetime
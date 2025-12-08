"""
Factories for creating model instances for testing.

Each factory provides a `create()` method that returns a new instance
with default values that can be overridden via kwargs.
"""

import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from PIL import Image

from src.artframe.models import (
    ContentSource,
    DisplayState,
    Photo,
    PluginInstance,
    StorageStats,
    StyledImage,
    TimeSlot,
)


class PhotoFactory:
    """Factory for creating Photo instances."""

    _counter = 0

    @classmethod
    def create(
        cls,
        id: Optional[str] = None,
        source_url: Optional[str] = None,
        retrieved_at: Optional[datetime] = None,
        original_path: Optional[Path] = None,
        metadata: Optional[dict[str, Any]] = None,
        create_file: bool = True,
    ) -> Photo:
        """
        Create a Photo instance with optional overrides.

        Args:
            id: Photo ID (auto-generated if not provided)
            source_url: Source URL
            retrieved_at: Retrieval timestamp
            original_path: Path to image file
            metadata: Photo metadata
            create_file: If True, creates an actual image file

        Returns:
            Photo instance
        """
        cls._counter += 1

        if id is None:
            id = f"photo_{uuid.uuid4().hex[:8]}"

        if source_url is None:
            source_url = f"http://example.com/photos/{id}.jpg"

        if retrieved_at is None:
            retrieved_at = datetime.now(ZoneInfo("UTC"))

        if original_path is None:
            if create_file:
                # Create a temporary image file
                temp_dir = Path(tempfile.mkdtemp())
                original_path = temp_dir / f"{id}.jpg"
                img = Image.new("RGB", (100, 100), color=f"#{cls._counter:06x}")
                img.save(original_path)
            else:
                original_path = Path(f"/tmp/test_photos/{id}.jpg")

        if metadata is None:
            metadata = {
                "original_filename": f"{id}.jpg",
                "file_created_at": retrieved_at.isoformat(),
                "device_id": "test_device",
            }

        return Photo(
            id=id,
            source_url=source_url,
            retrieved_at=retrieved_at,
            original_path=original_path,
            metadata=metadata,
        )

    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[Photo]:
        """Create multiple Photo instances."""
        return [cls.create(**kwargs) for _ in range(count)]


class StyledImageFactory:
    """Factory for creating StyledImage instances."""

    @classmethod
    def create(
        cls,
        original_photo_id: Optional[str] = None,
        style_name: str = "ghibli",
        styled_path: Optional[Path] = None,
        created_at: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None,
        create_file: bool = True,
    ) -> StyledImage:
        """Create a StyledImage instance with optional overrides."""
        if original_photo_id is None:
            original_photo_id = f"photo_{uuid.uuid4().hex[:8]}"

        if created_at is None:
            created_at = datetime.now(ZoneInfo("UTC"))

        if styled_path is None:
            if create_file:
                temp_dir = Path(tempfile.mkdtemp())
                styled_path = temp_dir / f"{original_photo_id}_{style_name}.jpg"
                img = Image.new("RGB", (100, 100), color="blue")
                img.save(styled_path)
            else:
                styled_path = Path(f"/tmp/styled/{original_photo_id}_{style_name}.jpg")

        if metadata is None:
            metadata = {"dimensions": (100, 100), "file_size": 1024}

        return StyledImage(
            original_photo_id=original_photo_id,
            style_name=style_name,
            styled_path=styled_path,
            created_at=created_at,
            metadata=metadata,
        )


class PluginInstanceFactory:
    """Factory for creating PluginInstance instances."""

    PLUGIN_DEFAULTS = {
        "clock": {"show_seconds": True, "format": "24h"},
        "immich": {"server_url": "http://localhost:2283", "api_key": "test_key"},
        "quote_of_the_day": {"font_size": 24, "background_color": "#ffffff"},
        "word_of_the_day": {"show_pronunciation": True},
        "repaint": {"style": "ghibli", "intensity": 0.8},
    }

    @classmethod
    def create(
        cls,
        id: Optional[str] = None,
        plugin_id: str = "clock",
        name: Optional[str] = None,
        settings: Optional[dict[str, Any]] = None,
        enabled: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> PluginInstance:
        """Create a PluginInstance with optional overrides."""
        if id is None:
            id = str(uuid.uuid4())

        if name is None:
            name = f"Test {plugin_id.title()}"

        if settings is None:
            settings = cls.PLUGIN_DEFAULTS.get(plugin_id, {})

        now = datetime.now(ZoneInfo("UTC"))
        if created_at is None:
            created_at = now
        if updated_at is None:
            updated_at = now

        return PluginInstance(
            id=id,
            plugin_id=plugin_id,
            name=name,
            settings=settings,
            enabled=enabled,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def create_clock(cls, **kwargs) -> PluginInstance:
        """Create a clock plugin instance."""
        return cls.create(plugin_id="clock", **kwargs)

    @classmethod
    def create_immich(cls, **kwargs) -> PluginInstance:
        """Create an immich plugin instance."""
        return cls.create(plugin_id="immich", **kwargs)


class TimeSlotFactory:
    """Factory for creating TimeSlot instances."""

    @classmethod
    def create(
        cls,
        day: int = 0,
        hour: int = 9,
        target_type: str = "instance",
        target_id: Optional[str] = None,
    ) -> TimeSlot:
        """Create a TimeSlot instance."""
        if target_id is None:
            target_id = str(uuid.uuid4())

        return TimeSlot(
            day=day,
            hour=hour,
            target_type=target_type,
            target_id=target_id,
        )

    @classmethod
    def create_week_schedule(
        cls,
        instance_id: str,
        days: Optional[list[int]] = None,
        start_hour: int = 9,
        end_hour: int = 17,
    ) -> list[TimeSlot]:
        """Create a week's worth of time slots."""
        if days is None:
            days = list(range(7))  # All days

        slots = []
        for day in days:
            for hour in range(start_hour, end_hour):
                slots.append(
                    cls.create(
                        day=day,
                        hour=hour,
                        target_id=instance_id,
                    )
                )
        return slots


class ContentSourceFactory:
    """Factory for creating ContentSource instances."""

    @classmethod
    def create(
        cls,
        instance: Optional[PluginInstance] = None,
        duration_seconds: int = 3600,
        source_type: str = "schedule",
        source_id: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> ContentSource:
        """Create a ContentSource instance."""
        if instance is None:
            instance = PluginInstanceFactory.create()

        if source_id is None:
            source_id = "0-9"

        if source_name is None:
            source_name = "Monday 9 AM"

        return ContentSource(
            instance=instance,
            duration_seconds=duration_seconds,
            source_type=source_type,
            source_id=source_id,
            source_name=source_name,
        )

    @classmethod
    def create_empty(cls) -> ContentSource:
        """Create an empty ContentSource."""
        return ContentSource.empty()


class DisplayStateFactory:
    """Factory for creating DisplayState instances."""

    @classmethod
    def create(
        cls,
        current_image_id: Optional[str] = None,
        last_refresh: Optional[datetime] = None,
        next_scheduled: Optional[datetime] = None,
    ) -> DisplayState:
        """Create a DisplayState instance."""
        now = datetime.now(ZoneInfo("UTC"))

        return DisplayState(
            current_image_id=current_image_id or "img_test",
            last_refresh=last_refresh or now,
            next_scheduled=next_scheduled or now,
        )


class StorageStatsFactory:
    """Factory for creating StorageStats instances."""

    @classmethod
    def create(
        cls,
        total_photos: int = 10,
        total_styled_images: int = 5,
        total_size_mb: float = 150.5,
        storage_directory: str = "/tmp/test_storage",
    ) -> StorageStats:
        """Create a StorageStats instance."""
        return StorageStats(
            total_photos=total_photos,
            total_styled_images=total_styled_images,
            total_size_mb=total_size_mb,
            storage_directory=storage_directory,
        )

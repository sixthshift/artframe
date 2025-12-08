"""
Unit tests for StorageManager.

Tests cover:
- Photo storage and retrieval
- Styled image storage and retrieval
- Index persistence
- Storage statistics
- Error handling
"""

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from src.artframe.models import Photo, StyledImage
from src.artframe.storage.manager import StorageManager


class TestStorageManagerInitialization:
    """Tests for StorageManager initialization."""

    def test_creates_required_directories(self, temp_dir: Path):
        """Should create photos, styled, and metadata directories."""
        storage = StorageManager(storage_dir=temp_dir / "storage")

        assert storage.photos_dir.exists()
        assert storage.styled_dir.exists()
        assert storage.metadata_dir.exists()

    def test_initializes_empty_index(self, temp_dir: Path):
        """Should initialize with empty index if no existing data."""
        storage = StorageManager(storage_dir=temp_dir / "storage")

        assert storage._index["photos"] == {}
        assert storage._index["styled_images"] == {}

    def test_loads_existing_index(self, temp_dir: Path, sample_photo: Photo):
        """Should load existing index on initialization."""
        # Create first instance and store a photo
        storage1 = StorageManager(storage_dir=temp_dir / "storage")
        storage1.store_photo(sample_photo)

        # Create second instance - should load existing index
        storage2 = StorageManager(storage_dir=temp_dir / "storage")

        assert sample_photo.id in storage2._index["photos"]


class TestPhotoStorage:
    """Tests for photo storage operations."""

    def test_store_photo_success(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should successfully store a photo."""
        result = storage_manager.store_photo(sample_photo)

        assert result is True
        assert storage_manager.photo_exists(sample_photo.id)

    def test_store_photo_creates_copy(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should create a copy of the photo in storage directory."""
        storage_manager.store_photo(sample_photo)

        expected_path = storage_manager.photos_dir / f"{sample_photo.id}.jpg"
        assert expected_path.exists()

    def test_store_photo_updates_index(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should update the index with photo metadata."""
        storage_manager.store_photo(sample_photo)

        index_entry = storage_manager._index["photos"][sample_photo.id]
        assert index_entry["id"] == sample_photo.id
        assert index_entry["source_url"] == sample_photo.source_url
        assert "stored_at" in index_entry

    def test_get_photo_success(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should retrieve a stored photo."""
        storage_manager.store_photo(sample_photo)

        retrieved = storage_manager.get_photo(sample_photo.id)

        assert retrieved is not None
        assert retrieved.id == sample_photo.id
        assert retrieved.source_url == sample_photo.source_url

    def test_get_photo_not_found(self, storage_manager: StorageManager):
        """Should return None for non-existent photo."""
        result = storage_manager.get_photo("nonexistent_id")

        assert result is None

    def test_get_photo_file_missing(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should return None if photo file is missing."""
        storage_manager.store_photo(sample_photo)

        # Delete the actual file
        stored_path = storage_manager.photos_dir / f"{sample_photo.id}.jpg"
        stored_path.unlink()

        result = storage_manager.get_photo(sample_photo.id)
        assert result is None

    def test_get_all_photos(self, storage_manager: StorageManager, temp_dir: Path):
        """Should retrieve all stored photos."""
        # Create and store multiple photos
        photos = []
        for i in range(3):
            img = Image.new("RGB", (100, 100), color=f"#{i*10:02x}0000")
            img_path = temp_dir / f"photo_{i}.jpg"
            img.save(img_path)

            photo = Photo(
                id=f"photo_{i}",
                source_url=f"http://example.com/{i}.jpg",
                retrieved_at=datetime.now(),
                original_path=img_path,
                metadata={},
            )
            storage_manager.store_photo(photo)
            photos.append(photo)

        result = storage_manager.get_all_photos()

        assert len(result) == 3
        ids = {p.id for p in result}
        assert ids == {"photo_0", "photo_1", "photo_2"}

    def test_photo_exists_true(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should return True for existing photo."""
        storage_manager.store_photo(sample_photo)

        assert storage_manager.photo_exists(sample_photo.id) is True

    def test_photo_exists_false(self, storage_manager: StorageManager):
        """Should return False for non-existent photo."""
        assert storage_manager.photo_exists("nonexistent") is False


class TestStyledImageStorage:
    """Tests for styled image storage operations."""

    def test_store_styled_image_success(
        self, storage_manager: StorageManager, sample_styled_image: StyledImage
    ):
        """Should successfully store a styled image."""
        result = storage_manager.store_styled_image(sample_styled_image)

        assert result is True
        assert storage_manager.styled_image_exists(
            sample_styled_image.original_photo_id, sample_styled_image.style_name
        )

    def test_store_styled_image_creates_copy(
        self, storage_manager: StorageManager, sample_styled_image: StyledImage
    ):
        """Should create a copy of the styled image in storage directory."""
        storage_manager.store_styled_image(sample_styled_image)

        expected_filename = (
            f"{sample_styled_image.original_photo_id}_{sample_styled_image.style_name}.jpg"
        )
        expected_path = storage_manager.styled_dir / expected_filename
        assert expected_path.exists()

    def test_get_styled_image_success(
        self, storage_manager: StorageManager, sample_styled_image: StyledImage
    ):
        """Should retrieve a stored styled image."""
        storage_manager.store_styled_image(sample_styled_image)

        retrieved = storage_manager.get_styled_image(
            sample_styled_image.original_photo_id, sample_styled_image.style_name
        )

        assert retrieved is not None
        assert retrieved.original_photo_id == sample_styled_image.original_photo_id
        assert retrieved.style_name == sample_styled_image.style_name

    def test_get_styled_image_not_found(self, storage_manager: StorageManager):
        """Should return None for non-existent styled image."""
        result = storage_manager.get_styled_image("nonexistent", "style")

        assert result is None

    def test_styled_image_exists_true(
        self, storage_manager: StorageManager, sample_styled_image: StyledImage
    ):
        """Should return True for existing styled image."""
        storage_manager.store_styled_image(sample_styled_image)

        result = storage_manager.styled_image_exists(
            sample_styled_image.original_photo_id, sample_styled_image.style_name
        )
        assert result is True

    def test_styled_image_exists_false(self, storage_manager: StorageManager):
        """Should return False for non-existent styled image."""
        assert storage_manager.styled_image_exists("photo", "style") is False


class TestPhotoRemoval:
    """Tests for photo removal operations."""

    def test_remove_photo_success(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should successfully remove a photo."""
        storage_manager.store_photo(sample_photo)

        result = storage_manager.remove_photo(sample_photo.id)

        assert result is True
        assert not storage_manager.photo_exists(sample_photo.id)

    def test_remove_photo_deletes_file(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should delete the photo file."""
        storage_manager.store_photo(sample_photo)
        stored_path = storage_manager.photos_dir / f"{sample_photo.id}.jpg"
        assert stored_path.exists()

        storage_manager.remove_photo(sample_photo.id)

        assert not stored_path.exists()

    def test_remove_photo_removes_styled_variants(
        self,
        storage_manager: StorageManager,
        sample_photo: Photo,
        temp_dir: Path,
    ):
        """Should remove all styled variants when removing a photo."""
        storage_manager.store_photo(sample_photo)

        # Create styled variants
        for style in ["ghibli", "watercolor"]:
            img = Image.new("RGB", (100, 100), color="blue")
            img_path = temp_dir / f"styled_{style}.jpg"
            img.save(img_path)

            styled = StyledImage(
                original_photo_id=sample_photo.id,
                style_name=style,
                styled_path=img_path,
                created_at=datetime.now(),
                metadata={},
            )
            storage_manager.store_styled_image(styled)

        # Verify styled images exist
        assert storage_manager.styled_image_exists(sample_photo.id, "ghibli")
        assert storage_manager.styled_image_exists(sample_photo.id, "watercolor")

        # Remove photo
        storage_manager.remove_photo(sample_photo.id)

        # Verify styled images are removed
        assert not storage_manager.styled_image_exists(sample_photo.id, "ghibli")
        assert not storage_manager.styled_image_exists(sample_photo.id, "watercolor")

    def test_remove_nonexistent_photo(self, storage_manager: StorageManager):
        """Should return True when removing non-existent photo (idempotent)."""
        result = storage_manager.remove_photo("nonexistent")

        # The current implementation returns True for nonexistent (no-op)
        assert result is True


class TestStorageStats:
    """Tests for storage statistics."""

    def test_get_storage_stats_empty(self, storage_manager: StorageManager):
        """Should return zero stats for empty storage."""
        stats = storage_manager.get_storage_stats()

        assert stats.total_photos == 0
        assert stats.total_styled_images == 0
        assert stats.total_size_mb == 0.0

    def test_get_storage_stats_with_data(
        self,
        storage_manager: StorageManager,
        sample_photo: Photo,
        sample_styled_image: StyledImage,
    ):
        """Should return correct stats with stored data."""
        storage_manager.store_photo(sample_photo)
        storage_manager.store_styled_image(sample_styled_image)

        stats = storage_manager.get_storage_stats()

        assert stats.total_photos == 1
        assert stats.total_styled_images == 1
        assert stats.total_size_mb > 0

    def test_storage_stats_directory_path(self, storage_manager: StorageManager):
        """Should include storage directory in stats."""
        stats = storage_manager.get_storage_stats()

        assert stats.storage_directory == str(storage_manager.storage_dir)


class TestIndexPersistence:
    """Tests for index persistence."""

    def test_index_persisted_after_store(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should persist index after storing a photo."""
        storage_manager.store_photo(sample_photo)

        assert storage_manager.index_file.exists()

    def test_index_has_last_updated(self, storage_manager: StorageManager, sample_photo: Photo):
        """Should update last_updated timestamp in index."""
        storage_manager.store_photo(sample_photo)

        assert "last_updated" in storage_manager._index

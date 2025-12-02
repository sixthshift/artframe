"""Storage manager for local photo and styled image storage."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ..logging.logger import Logger
from ..models import Photo, StorageStats, StyledImage


class StorageManager:
    """Manages local storage of photos and styled images."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.photos_dir = self.storage_dir / "photos"
        self.styled_dir = self.storage_dir / "styled"
        self.metadata_dir = self.storage_dir / "metadata"

        # Create directories
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.styled_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.metadata_dir / "index.json"
        self.logger = Logger(__name__)

        # Load or initialize index
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load the storage index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    return cast(Dict[str, Any], json.load(f))
            except (json.JSONDecodeError, OSError) as e:
                self.logger.warning(f"Failed to load index, starting fresh: {e}")

        return {"photos": {}, "styled_images": {}, "last_updated": datetime.now().isoformat()}

    def _save_index(self):
        """Save the storage index to disk."""
        self._index["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.index_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except OSError as e:
            self.logger.error(f"Failed to save index: {e}")

    def store_photo(self, photo: Photo) -> bool:
        """Store a photo locally."""
        try:
            # Create destination path
            dest_path = self.photos_dir / f"{photo.id}.jpg"

            # Copy photo to storage
            shutil.copy2(photo.original_path, dest_path)

            # Update index
            self._index["photos"][photo.id] = {
                "id": photo.id,
                "source_url": photo.source_url,
                "retrieved_at": photo.retrieved_at.isoformat(),
                "local_path": str(dest_path),
                "metadata": photo.metadata,
                "stored_at": datetime.now().isoformat(),
            }

            self._save_index()
            self.logger.info(f"Stored photo {photo.id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store photo {photo.id}: {e}")
            return False

    def get_photo(self, photo_id: str) -> Optional[Photo]:
        """Get a photo by ID."""
        photo_info = self._index["photos"].get(photo_id)
        if not photo_info:
            return None

        local_path = Path(photo_info["local_path"])
        if not local_path.exists():
            self.logger.warning(f"Photo file missing: {local_path}")
            return None

        return Photo(
            id=photo_info["id"],
            source_url=photo_info["source_url"],
            retrieved_at=datetime.fromisoformat(photo_info["retrieved_at"]),
            original_path=local_path,
            metadata=photo_info["metadata"],
        )

    def get_all_photos(self) -> List[Photo]:
        """Get all stored photos."""
        photos = []
        for photo_id in self._index["photos"]:
            photo = self.get_photo(photo_id)
            if photo:
                photos.append(photo)
        return photos

    def store_styled_image(self, styled_image: StyledImage) -> bool:
        """Store a styled image locally."""
        try:
            # Create destination path
            filename = f"{styled_image.original_photo_id}_{styled_image.style_name}.jpg"
            dest_path = self.styled_dir / filename

            # Copy styled image to storage
            shutil.copy2(styled_image.styled_path, dest_path)

            # Update index
            styled_id = f"{styled_image.original_photo_id}_{styled_image.style_name}"
            self._index["styled_images"][styled_id] = {
                "original_photo_id": styled_image.original_photo_id,
                "style_name": styled_image.style_name,
                "created_at": styled_image.created_at.isoformat(),
                "local_path": str(dest_path),
                "metadata": styled_image.metadata,
                "stored_at": datetime.now().isoformat(),
            }

            self._save_index()
            self.logger.info(f"Stored styled image {styled_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store styled image: {e}")
            return False

    def get_styled_image(self, photo_id: str, style_name: str) -> Optional[StyledImage]:
        """Get a styled image by photo ID and style name."""
        styled_id = f"{photo_id}_{style_name}"
        styled_info = self._index["styled_images"].get(styled_id)

        if not styled_info:
            return None

        local_path = Path(styled_info["local_path"])
        if not local_path.exists():
            self.logger.warning(f"Styled image file missing: {local_path}")
            return None

        return StyledImage(
            original_photo_id=styled_info["original_photo_id"],
            style_name=styled_info["style_name"],
            styled_path=local_path,
            created_at=datetime.fromisoformat(styled_info["created_at"]),
            metadata=styled_info["metadata"],
        )

    def photo_exists(self, photo_id: str) -> bool:
        """Check if a photo exists in storage."""
        return photo_id in self._index["photos"]

    def styled_image_exists(self, photo_id: str, style_name: str) -> bool:
        """Check if a styled image exists in storage."""
        styled_id = f"{photo_id}_{style_name}"
        return styled_id in self._index["styled_images"]

    def remove_photo(self, photo_id: str) -> bool:
        """Remove a photo and all its styled variants."""
        try:
            # Remove photo file
            photo_info = self._index["photos"].get(photo_id)
            if photo_info:
                photo_path = Path(photo_info["local_path"])
                if photo_path.exists():
                    photo_path.unlink()
                del self._index["photos"][photo_id]

            # Remove all styled variants
            to_remove = []
            for styled_id, styled_info in self._index["styled_images"].items():
                if styled_info["original_photo_id"] == photo_id:
                    styled_path = Path(styled_info["local_path"])
                    if styled_path.exists():
                        styled_path.unlink()
                    to_remove.append(styled_id)

            for styled_id in to_remove:
                del self._index["styled_images"][styled_id]

            self._save_index()
            self.logger.info(f"Removed photo {photo_id} and its styled variants")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove photo {photo_id}: {e}")
            return False

    def get_storage_stats(self) -> StorageStats:
        """Get storage statistics."""
        total_photos = len(self._index["photos"])
        total_styled = len(self._index["styled_images"])

        # Calculate total size
        total_size = 0
        for photo_info in self._index["photos"].values():
            path = Path(photo_info["local_path"])
            if path.exists():
                total_size += path.stat().st_size

        for styled_info in self._index["styled_images"].values():
            path = Path(styled_info["local_path"])
            if path.exists():
                total_size += path.stat().st_size

        total_size_mb = total_size / (1024 * 1024)

        return StorageStats(
            total_photos=total_photos,
            total_styled_images=total_styled,
            total_size_mb=total_size_mb,
            storage_directory=str(self.storage_dir),
        )

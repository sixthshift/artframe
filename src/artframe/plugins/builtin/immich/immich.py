"""
Immich Album Sync plugin for Artframe.

Syncs photos from an Immich album to local storage and displays them.
Keeps local copy in sync with server (adds new photos, removes deleted ones).
"""

import hashlib
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from artframe.plugins.base_plugin import BasePlugin


class Immich(BasePlugin):
    """
    Sync and display photos from Immich albums.

    This plugin downloads all photos from an Immich album to local storage
    and keeps them synchronized. Photos are displayed from the local cache,
    making it fast and enabling offline operation.
    """

    def __init__(self):
        """Initialize Immich plugin."""
        super().__init__()
        self.session = None
        self._sync_dir = None
        self._photos_dir = None
        self._metadata_file = None
        self._metadata = None
        self._current_index = 0

    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate plugin settings.

        Args:
            settings: Plugin settings dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not settings.get("immich_url"):
            return False, "Immich server URL is required"

        if not settings.get("immich_api_key"):
            return False, "Immich API key is required"

        if not settings["immich_url"].startswith(("http://", "https://")):
            return False, "Immich URL must start with http:// or https://"

        # Validate selection mode
        selection = settings.get("selection_mode", "random")
        if selection not in ["random", "sequential", "newest", "oldest"]:
            return False, f"Invalid selection mode: {selection}"

        # Validate sync interval
        sync_interval = settings.get("sync_interval_hours", 6)
        if not isinstance(sync_interval, (int, float)) or sync_interval < 1:
            return False, "Sync interval must be at least 1 hour"

        return True, ""

    def on_enable(self, settings: Dict[str, Any]) -> None:
        """Initialize plugin when enabled."""
        self.session = requests.Session()
        self.session.headers.update(
            {"x-api-key": settings["immich_api_key"], "Accept": "application/json"}
        )

        # Initialize storage directories
        self._init_storage(settings)

        self.logger.info("Immich plugin enabled")

    def on_disable(self, settings: Dict[str, Any]) -> None:
        """Cleanup when plugin is disabled."""
        if self.session:
            self.session.close()
            self.session = None
        self.logger.info("Immich plugin disabled")

    def _init_storage(self, settings: Dict[str, Any]) -> None:
        """Initialize storage directories for this instance."""
        # Use instance-specific directory
        instance_id = settings.get("_instance_id", "default")

        # Base directory for plugin data
        base_dir = Path.home() / ".artframe" / "plugins" / "immich" / instance_id
        self._sync_dir = base_dir
        self._photos_dir = base_dir / "photos"
        self._metadata_file = base_dir / "sync_metadata.json"

        # Create directories
        self._photos_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize metadata
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load sync metadata from disk."""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, "r") as f:
                    self._metadata = json.load(f)
                self.logger.debug(
                    f"Loaded metadata: {len(self._metadata.get('synced_assets', {}))} assets"
                )
            except Exception as e:
                self.logger.error(f"Failed to load metadata: {e}")
                self._metadata = self._create_empty_metadata()
        else:
            self._metadata = self._create_empty_metadata()

    def _save_metadata(self) -> None:
        """Save sync metadata to disk."""
        try:
            with open(self._metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
            self.logger.debug("Saved metadata")
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")

    def _create_empty_metadata(self) -> Dict[str, Any]:
        """Create empty metadata structure."""
        return {"last_sync": None, "album_id": None, "synced_assets": {}, "sync_count": 0}

    def generate_image(
        self, settings: Dict[str, Any], device_config: Dict[str, Any]
    ) -> Image.Image:
        """
        Generate image from synced photos.

        Args:
            settings: Plugin instance settings
            device_config: Display device configuration

        Returns:
            PIL.Image: Generated image ready for display

        Raises:
            RuntimeError: If image generation fails
        """
        try:
            # Initialize if needed
            if self.session is None:
                self.on_enable(settings)

            # Check if sync is needed
            if self._should_sync(settings):
                self.logger.info("Starting sync with Immich server...")
                self._sync_with_server(settings)
                self.logger.info("Sync completed")

            # Get local photos
            local_photos = self._get_local_photos()

            if not local_photos:
                self.logger.warning("No photos available, triggering sync...")
                self._sync_with_server(settings)
                local_photos = self._get_local_photos()

                if not local_photos:
                    raise RuntimeError("No photos found after sync")

            # Select photo based on mode
            photo_path = self._select_local_photo(local_photos, settings)
            self.logger.info(f"Displaying photo: {photo_path.name}")

            # Load and prepare image
            image = Image.open(photo_path)
            image = self._fit_to_display(image, device_config)

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}", exc_info=True)
            return self._create_error_image(str(e), device_config)

    def _should_sync(self, settings: Dict[str, Any]) -> bool:
        """
        Check if synchronization is needed.

        Args:
            settings: Plugin settings

        Returns:
            True if sync is needed
        """
        last_sync = self._metadata.get("last_sync")

        if last_sync is None:
            return True  # Never synced

        # Check if album ID changed
        current_album_id = settings.get("album_id")
        if current_album_id != self._metadata.get("album_id"):
            self.logger.info("Album ID changed, sync needed")
            return True

        # Check sync interval
        sync_interval = settings.get("sync_interval_hours", 6)
        last_sync_time = datetime.fromisoformat(last_sync)
        time_since_sync = datetime.now() - last_sync_time

        if time_since_sync > timedelta(hours=sync_interval):
            self.logger.info(
                f"Sync interval exceeded ({time_since_sync.total_seconds() / 3600:.1f}h)"
            )
            return True

        return False

    def _sync_with_server(self, settings: Dict[str, Any]) -> None:
        """
        Synchronize local photos with Immich server.

        Args:
            settings: Plugin settings
        """
        immich_url = settings["immich_url"].rstrip("/")
        album_id = settings.get("album_id")

        # Fetch current assets from server
        server_assets = self._fetch_server_assets(immich_url, album_id)

        if not server_assets:
            self.logger.warning("No assets found on server")
            return

        # Apply max photos limit if set
        max_photos = settings.get("max_photos", 0)
        if max_photos > 0 and len(server_assets) > max_photos:
            self.logger.info(f"Limiting to {max_photos} photos")
            server_assets = server_assets[:max_photos]

        # Get currently synced asset IDs
        synced_asset_ids = set(self._metadata["synced_assets"].keys())
        server_asset_ids = {asset["id"] for asset in server_assets}

        # Find assets to download (new assets)
        assets_to_download = [
            asset for asset in server_assets if asset["id"] not in synced_asset_ids
        ]

        # Find assets to delete (removed from server)
        assets_to_delete = synced_asset_ids - server_asset_ids

        # Download new assets
        if assets_to_download:
            self.logger.info(f"Downloading {len(assets_to_download)} new photos...")
            for i, asset in enumerate(assets_to_download, 1):
                try:
                    self._download_asset(immich_url, asset)
                    self.logger.debug(
                        f"Downloaded {i}/{len(assets_to_download)}: {asset.get('originalFileName')}"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to download {asset['id']}: {e}")

        # Delete removed assets
        if assets_to_delete:
            self.logger.info(f"Removing {len(assets_to_delete)} deleted photos...")
            for asset_id in assets_to_delete:
                self._delete_local_asset(asset_id)

        # Update metadata
        self._metadata["last_sync"] = datetime.now().isoformat()
        self._metadata["album_id"] = album_id
        self._metadata["sync_count"] = self._metadata.get("sync_count", 0) + 1
        self._save_metadata()

        self.logger.info(
            f"Sync complete: {len(self._metadata['synced_assets'])} photos, "
            f"+{len(assets_to_download)} new, -{len(assets_to_delete)} removed"
        )

    def _fetch_server_assets(
        self, immich_url: str, album_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch assets from Immich server.

        Args:
            immich_url: Immich server URL
            album_id: Optional album ID

        Returns:
            List of asset dictionaries
        """
        try:
            if album_id:
                # Fetch from specific album
                response = self.session.get(
                    f"{immich_url}/api/albums/{album_id}", params={"withoutAssets": False}
                )
                response.raise_for_status()

                album_data = response.json()
                assets = album_data.get("assets", [])

            else:
                # Fetch all assets using search/metadata endpoint
                assets = []
                page = 1
                page_size = 1000

                while True:
                    response = self.session.post(
                        f"{immich_url}/api/search/metadata", json={"size": page_size, "page": page}
                    )
                    response.raise_for_status()

                    result = response.json()
                    page_assets = result.get("assets", {}).get("items", [])

                    if not page_assets:
                        break

                    assets.extend(page_assets)

                    # Check if done
                    total = result.get("assets", {}).get("total", 0)
                    if len(assets) >= total:
                        break

                    page += 1

            # Filter for images only (exclude videos)
            photos = [asset for asset in assets if asset.get("type") == "IMAGE"]

            self.logger.info(f"Found {len(photos)} photos on server")
            return photos

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch assets from server: {e}")
            raise RuntimeError(f"Failed to fetch from Immich: {e}")

    def _download_asset(self, immich_url: str, asset: Dict[str, Any]) -> None:
        """
        Download asset from Immich to local storage.

        Args:
            immich_url: Immich server URL
            asset: Asset metadata dictionary
        """
        asset_id = asset["id"]
        filename = asset.get("originalFileName", f"{asset_id}.jpg")

        # Create safe filename
        safe_filename = self._sanitize_filename(filename)
        local_path = self._photos_dir / safe_filename

        # Ensure unique filename
        counter = 1
        while local_path.exists():
            name = Path(safe_filename).stem
            ext = Path(safe_filename).suffix
            local_path = self._photos_dir / f"{name}_{counter}{ext}"
            counter += 1

        # Download photo
        try:
            response = self.session.get(f"{immich_url}/api/assets/{asset_id}/original", timeout=60)
            response.raise_for_status()

            # Save to disk
            with open(local_path, "wb") as f:
                f.write(response.content)

            # Calculate checksum
            checksum = hashlib.md5(response.content).hexdigest()

            # Update metadata
            self._metadata["synced_assets"][asset_id] = {
                "filename": filename,
                "local_path": str(local_path.relative_to(self._photos_dir)),
                "file_created_at": asset.get("fileCreatedAt"),
                "checksum": checksum,
                "synced_at": datetime.now().isoformat(),
            }

        except Exception as e:
            # Clean up partial download
            if local_path.exists():
                local_path.unlink()
            raise e

    def _delete_local_asset(self, asset_id: str) -> None:
        """
        Delete local asset file and metadata.

        Args:
            asset_id: Asset ID to delete
        """
        if asset_id not in self._metadata["synced_assets"]:
            return

        asset_info = self._metadata["synced_assets"][asset_id]
        local_path = self._photos_dir / asset_info["local_path"]

        # Delete file
        if local_path.exists():
            try:
                local_path.unlink()
                self.logger.debug(f"Deleted local file: {local_path.name}")
            except Exception as e:
                self.logger.error(f"Failed to delete {local_path}: {e}")

        # Remove from metadata
        del self._metadata["synced_assets"][asset_id]

    def _get_local_photos(self) -> List[Path]:
        """
        Get list of local photo files.

        Returns:
            List of Path objects for local photos
        """
        if not self._photos_dir.exists():
            return []

        # Get all image files
        photos = []
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            photos.extend(self._photos_dir.glob(f"*{ext}"))
            photos.extend(self._photos_dir.glob(f"*{ext.upper()}"))

        return sorted(photos)

    def _select_local_photo(self, photos: List[Path], settings: Dict[str, Any]) -> Path:
        """
        Select photo based on selection mode.

        Args:
            photos: List of photo paths
            settings: Plugin settings

        Returns:
            Selected photo path
        """
        if not photos:
            raise RuntimeError("No photos available")

        selection_mode = settings.get("selection_mode", "random")

        if selection_mode == "random":
            return random.choice(photos)

        elif selection_mode == "sequential":
            # Cycle through photos
            photo = photos[self._current_index % len(photos)]
            self._current_index += 1
            return photo

        elif selection_mode == "newest":
            # Sort by modification time
            return max(photos, key=lambda p: p.stat().st_mtime)

        elif selection_mode == "oldest":
            return min(photos, key=lambda p: p.stat().st_mtime)

        else:
            return photos[0]

    def _fit_to_display(self, image: Image.Image, device_config: Dict[str, Any]) -> Image.Image:
        """
        Resize and fit image to display dimensions.

        Args:
            image: Input image
            device_config: Display configuration

        Returns:
            PIL.Image: Resized image
        """
        display_width = device_config["width"]
        display_height = device_config["height"]

        # Calculate aspect ratios
        image_aspect = image.width / image.height
        display_aspect = display_width / display_height

        # Fit image to display (contain mode)
        if image_aspect > display_aspect:
            new_width = display_width
            new_height = int(display_width / image_aspect)
        else:
            new_height = display_height
            new_width = int(display_height * image_aspect)

        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create canvas and center image
        canvas = Image.new("RGB", (display_width, display_height), "white")
        x = (display_width - new_width) // 2
        y = (display_height - new_height) // 2
        canvas.paste(resized, (x, y))

        return canvas

    def _create_error_image(self, error_message: str, device_config: Dict[str, Any]) -> Image.Image:
        """Create error image with message."""
        from PIL import ImageDraw, ImageFont

        width = device_config["width"]
        height = device_config["height"]

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        text = f"Immich Plugin Error:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Create safe filename by removing problematic characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace problematic characters
        unsafe_chars = '<>:"/\\|?*'
        safe_name = "".join(c if c not in unsafe_chars else "_" for c in filename)

        # Ensure it's not empty
        if not safe_name or safe_name.startswith("."):
            safe_name = "photo_" + safe_name

        return safe_name

    def get_cache_key(self, settings: Dict[str, Any]) -> Optional[str]:
        """
        Photos are cached locally, so no need for system cache.

        Returns None to disable caching.
        """
        return None

    def get_cache_ttl(self, settings: Dict[str, Any]) -> int:
        """No caching needed - photos are stored locally."""
        return 0

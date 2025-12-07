"""
Repaint plugin for Artframe.

Transforms photos from an Immich album into art using AI styles.
Photos are fetched from Immich, styled using Google's Gemini API,
and cached locally for future display.
"""

import json
import random
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import requests
from PIL import Image

from artframe.plugins.base_plugin import BasePlugin
from artframe.plugins.builtin.repaint.gemini_client import GeminiClient


class Repaint(BasePlugin):
    """
    Transform Immich photos into art using AI styles.

    This plugin syncs photo metadata from an Immich album, then on each
    refresh picks a random photo and random style, checks the cache,
    and generates a styled image if not cached.
    """

    def __init__(self):
        """Initialize Repaint plugin."""
        super().__init__()
        self.session: Optional[requests.Session] = None
        self._sync_dir: Optional[Path] = None
        self._cache_dir: Optional[Path] = None
        self._metadata_file: Optional[Path] = None
        self._metadata: Optional[dict[str, Any]] = None
        self._styles: Optional[dict[str, Any]] = None
        self._gemini_client: Optional[GeminiClient] = None

    def validate_settings(self, settings: dict[str, Any]) -> tuple[bool, str]:
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

        if not settings.get("album_id"):
            return False, "Album ID is required"

        if not settings.get("gemini_api_key"):
            return False, "Gemini API key is required"

        # Validate sync interval
        sync_interval = settings.get("sync_interval_hours", 6)
        if not isinstance(sync_interval, (int, float)) or sync_interval < 1:
            return False, "Sync interval must be at least 1 hour"

        # Validate refresh interval
        refresh_interval = settings.get("refresh_interval_minutes", 60)
        if not isinstance(refresh_interval, (int, float)) or refresh_interval < 5:
            return False, "Refresh interval must be at least 5 minutes"

        return True, ""

    def on_enable(self, settings: dict[str, Any]) -> None:
        """Initialize plugin when enabled."""
        self.session = requests.Session()
        self.session.headers.update(
            {"X-API-Key": settings["immich_api_key"], "Accept": "application/json"}
        )

        # Initialize storage directories
        self._init_storage(settings)

        # Load styles
        self._load_styles()

        # Initialize Gemini client
        self._gemini_client = GeminiClient(
            api_key=settings["gemini_api_key"],
            model=settings.get("gemini_model", "gemini-2.0-flash-exp"),
        )

        self.logger.info("Repaint plugin enabled")

    def on_disable(self, settings: dict[str, Any]) -> None:
        """Cleanup when plugin is disabled."""
        if self.session:
            self.session.close()
            self.session = None
        self._gemini_client = None
        self.logger.info("Repaint plugin disabled")

    def _init_storage(self, settings: dict[str, Any]) -> None:
        """Initialize storage directories for this instance."""
        instance_id = settings.get("_instance_id", "default")

        # Base directory for plugin data
        base_dir = Path.home() / ".artframe" / "plugins" / "repaint" / instance_id
        cache_dir = base_dir / "cache"

        # Create directories
        cache_dir.mkdir(parents=True, exist_ok=True)

        self._sync_dir = base_dir
        self._cache_dir = cache_dir
        self._metadata_file = base_dir / "sync_metadata.json"

        # Load or initialize metadata
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load sync metadata from disk."""
        if self._metadata_file is None:
            self._metadata = self._create_empty_metadata()
            return

        if self._metadata_file.exists():
            try:
                with open(self._metadata_file) as f:
                    self._metadata = json.load(f)
                if self._metadata:
                    self.logger.debug(
                        f"Loaded metadata: {len(self._metadata.get('photos', []))} photos"
                    )
            except Exception as e:
                self.logger.error(f"Failed to load metadata: {e}")
                self._metadata = self._create_empty_metadata()
        else:
            self._metadata = self._create_empty_metadata()

    def _save_metadata(self) -> None:
        """Save sync metadata to disk."""
        if self._metadata_file is None or self._metadata is None:
            return

        try:
            with open(self._metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
            self.logger.debug("Saved metadata")
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")

    def _create_empty_metadata(self) -> dict[str, Any]:
        """Create empty metadata structure."""
        return {
            "last_sync": None,
            "album_id": None,
            "photos": [],
            "sync_count": 0,
        }

    def _load_styles(self) -> None:
        """Load styles from styles.json."""
        styles_file = self.get_plugin_directory() / "styles.json"
        try:
            with open(styles_file) as f:
                self._styles = json.load(f)
            if self._styles:
                self.logger.info(f"Loaded {len(self._styles)} styles")
        except Exception as e:
            self.logger.error(f"Failed to load styles: {e}")
            self._styles = {}

    def generate_image(
        self, settings: dict[str, Any], device_config: dict[str, Any]
    ) -> Image.Image:
        """
        Generate a styled image from an Immich photo.

        Args:
            settings: Plugin instance settings
            device_config: Display device configuration

        Returns:
            PIL.Image: Generated styled image ready for display

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
                self._sync_with_immich(settings)
                self.logger.info("Sync completed")

            # Get synced photos
            photos = self._get_synced_photos()
            if not photos:
                self.logger.warning("No photos available, triggering sync...")
                self._sync_with_immich(settings)
                photos = self._get_synced_photos()

                if not photos:
                    raise RuntimeError("No photos found after sync")

            # Select random photo and style
            photo = self._select_random_photo(photos)
            style_id, style = self._select_random_style()

            self.logger.info(
                f"Selected photo: {photo.get('originalFileName', photo['id'])} "
                f"with style: {style['name']}"
            )

            # Check cache
            cache_path = self._get_cache_path(photo["id"], style_id)
            image: Image.Image
            if cache_path.exists():
                self.logger.info(f"Loading from cache: {cache_path.name}")
                image = Image.open(cache_path)
            else:
                # Fetch original from Immich
                self.logger.info("Fetching original from Immich...")
                original = self._fetch_photo_from_immich(settings, photo["id"])

                # Apply style using Gemini
                self.logger.info(f"Applying style: {style['name']}...")
                if self._gemini_client is None:
                    raise RuntimeError("Gemini client not initialized")

                image = self._gemini_client.transform_image(original, style["prompt"])

                # Save to cache
                self._save_to_cache(image, cache_path)
                self.logger.info(f"Saved to cache: {cache_path.name}")

            # Fit to display
            image = self._fit_to_display(image, device_config)

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}", exc_info=True)
            return self._create_error_image(str(e), device_config)

    def _should_sync(self, settings: dict[str, Any]) -> bool:
        """Check if synchronization is needed."""
        if self._metadata is None:
            return True

        last_sync = self._metadata.get("last_sync")
        if last_sync is None:
            return True

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

    def _sync_with_immich(self, settings: dict[str, Any]) -> None:
        """Sync photo metadata from Immich server."""
        if self._metadata is None:
            self.logger.error("Metadata not initialized")
            return

        if self.session is None:
            raise RuntimeError("Session not initialized")

        immich_url = settings["immich_url"].rstrip("/")
        album_id = settings["album_id"]

        try:
            # Fetch album photos
            response = self.session.get(
                f"{immich_url}/api/albums/{album_id}",
                params={"withoutAssets": "false"},
            )
            response.raise_for_status()

            album_data = response.json()
            assets = album_data.get("assets", [])

            # Filter for images only
            photos = [
                {
                    "id": asset["id"],
                    "originalFileName": asset.get("originalFileName", ""),
                    "fileCreatedAt": asset.get("fileCreatedAt", ""),
                }
                for asset in assets
                if asset.get("type") == "IMAGE"
            ]

            self.logger.info(f"Found {len(photos)} photos in album")

            # Update metadata (do NOT delete cache entries)
            self._metadata["photos"] = photos
            self._metadata["album_id"] = album_id
            self._metadata["last_sync"] = datetime.now().isoformat()
            self._metadata["sync_count"] = self._metadata.get("sync_count", 0) + 1

            self._save_metadata()

        except requests.RequestException as e:
            self.logger.error(f"Failed to sync with Immich: {e}")
            raise RuntimeError(f"Failed to sync with Immich: {e}") from e

    def _get_synced_photos(self) -> list[dict[str, Any]]:
        """Get list of synced photo metadata."""
        if self._metadata is None:
            return []
        photos: list[dict[str, Any]] = self._metadata.get("photos", [])
        return photos

    def _select_random_photo(self, photos: list[dict[str, Any]]) -> dict[str, Any]:
        """Select a random photo from the list."""
        return random.choice(photos)

    def _select_random_style(self) -> tuple[str, dict[str, Any]]:
        """Select a random style from available styles."""
        if not self._styles:
            raise RuntimeError("No styles available")

        style_id = random.choice(list(self._styles.keys()))
        return style_id, self._styles[style_id]

    def _get_cache_path(self, photo_id: str, style_id: str) -> Path:
        """Get the cache file path for a photo+style combo."""
        if self._cache_dir is None:
            raise RuntimeError("Cache directory not initialized")
        return self._cache_dir / f"{photo_id}_{style_id}.jpg"

    def _save_to_cache(self, image: Image.Image, cache_path: Path) -> None:
        """Save styled image to cache."""
        # Ensure RGB mode for JPEG
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(cache_path, format="JPEG", quality=95)

    def _fetch_photo_from_immich(
        self, settings: dict[str, Any], photo_id: str
    ) -> Image.Image:
        """Fetch original photo from Immich."""
        if self.session is None:
            raise RuntimeError("Session not initialized")

        immich_url = settings["immich_url"].rstrip("/")

        try:
            response = self.session.get(
                f"{immich_url}/api/assets/{photo_id}/original",
                timeout=60,
            )
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            return image

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch photo from Immich: {e}") from e

    def _fit_to_display(
        self, image: Image.Image, device_config: dict[str, Any]
    ) -> Image.Image:
        """Resize and fit image to display dimensions."""
        display_width = device_config["width"]
        display_height = device_config["height"]

        # Ensure RGB mode
        if image.mode != "RGB":
            image = image.convert("RGB")

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

    def _create_error_image(
        self, error_message: str, device_config: dict[str, Any]
    ) -> Image.Image:
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

        text = f"Repaint Error:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    def get_refresh_interval(self, settings: dict[str, Any]) -> int:
        """Get display refresh interval in seconds."""
        refresh_minutes = settings.get("refresh_interval_minutes", 60)
        return int(refresh_minutes * 60)

    def run_active(
        self,
        display_controller,
        settings: dict[str, Any],
        device_config: dict[str, Any],
        stop_event,
        plugin_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Run the styled photo display.

        Displays styled photos, rotating at the configured refresh interval.
        Each refresh picks a random photo and style combination.
        """
        refresh_interval = self.get_refresh_interval(settings)

        self.logger.info(
            f"Repaint starting with {refresh_interval // 60}min refresh interval"
        )

        while not stop_event.is_set():
            try:
                image = self.generate_image(settings, device_config)
                if image:
                    display_controller.display_image(image, plugin_info)
                    self.logger.debug("Repaint display updated")
            except Exception as e:
                self.logger.error(f"Failed to update Repaint display: {e}")

            stop_event.wait(timeout=refresh_interval)

        self.logger.info("Repaint stopped")

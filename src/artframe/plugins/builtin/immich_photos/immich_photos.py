"""
Immich Photos plugin for Artframe.

Fetches photos from Immich server with optional AI style transformation.
Combines photo retrieval and styling in a single plugin.
"""

import requests
import random
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from PIL import Image
from io import BytesIO

from artframe.plugins.base_plugin import BasePlugin


class ImmichPhotos(BasePlugin):
    """
    Display photos from Immich server with optional AI styling.

    This plugin fetches photos from an Immich photo management server
    and optionally applies AI artistic transformations before display.
    """

    def __init__(self):
        """Initialize Immich Photos plugin."""
        super().__init__()
        self.session = None

    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate plugin settings.

        Args:
            settings: Plugin settings dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate Immich settings
        if not settings.get("immich_url"):
            return False, "Immich server URL is required"

        if not settings.get("immich_api_key"):
            return False, "Immich API key is required"

        if not settings["immich_url"].startswith(("http://", "https://")):
            return False, "Immich URL must start with http:// or https://"

        # Validate selection mode
        selection = settings.get("selection_mode", "random")
        if selection not in ["random", "newest", "oldest"]:
            return False, f"Invalid selection mode: {selection}"

        # Validate AI settings if enabled
        if settings.get("use_ai", False):
            if not settings.get("ai_service_url"):
                return False, "AI service URL is required when AI is enabled"

            if not settings.get("ai_api_key"):
                return False, "AI API key is required when AI is enabled"

            if not settings.get("ai_style"):
                return False, "AI style is required when AI is enabled"

        return True, ""

    def on_enable(self, settings: Dict[str, Any]) -> None:
        """Initialize HTTP session when plugin is enabled."""
        self.session = requests.Session()
        self.session.headers.update(
            {"X-API-Key": settings["immich_api_key"], "Accept": "application/json"}
        )
        self.logger.info("Immich Photos plugin enabled")

    def on_disable(self, settings: Dict[str, Any]) -> None:
        """Close HTTP session when plugin is disabled."""
        if self.session:
            self.session.close()
            self.session = None
        self.logger.info("Immich Photos plugin disabled")

    def generate_image(
        self, settings: Dict[str, Any], device_config: Dict[str, Any]
    ) -> Image.Image:
        """
        Generate image from Immich photo with optional AI styling.

        Args:
            settings: Plugin instance settings
            device_config: Display device configuration

        Returns:
            PIL.Image: Generated image ready for display

        Raises:
            RuntimeError: If image generation fails
        """
        try:
            # Initialize session if needed
            if self.session is None:
                self.on_enable(settings)

            # Fetch photo from Immich
            self.logger.info("Fetching photo from Immich...")
            photo_data = self._fetch_photo_from_immich(settings)
            self.logger.info(f"Fetched photo: {photo_data.get('originalFileName', 'unknown')}")

            # Download photo
            image = self._download_photo(settings, photo_data)
            self.logger.info(f"Downloaded photo: {image.size}")

            # Apply AI styling if enabled
            if settings.get("use_ai", False):
                self.logger.info(f"Applying AI style: {settings['ai_style']}")
                image = self._apply_ai_style(settings, image, device_config)
                self.logger.info("AI styling completed")
            else:
                self.logger.info("AI styling disabled, using original photo")

            # Resize to fit display
            image = self._fit_to_display(image, device_config)

            return image

        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}", exc_info=True)
            # Return error image
            return self._create_error_image(str(e), device_config)

    def _fetch_photo_from_immich(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch photo metadata from Immich.

        Args:
            settings: Plugin settings

        Returns:
            Dict containing photo metadata

        Raises:
            RuntimeError: If fetch fails
        """
        immich_url = settings["immich_url"].rstrip("/")
        album_id = settings.get("album_id")
        selection_mode = settings.get("selection_mode", "random")

        try:
            if album_id:
                # Fetch from specific album
                response = self.session.get(f"{immich_url}/api/album/{album_id}")
                response.raise_for_status()

                album_data = response.json()
                assets = album_data.get("assets", [])

                if not assets:
                    raise RuntimeError(f"No photos found in album {album_id}")

                photo_data = self._select_photo(assets, selection_mode)

            else:
                # Fetch from all assets
                if selection_mode == "random":
                    # Try random endpoint first
                    try:
                        response = self.session.get(f"{immich_url}/api/asset/random")
                        response.raise_for_status()
                        assets = response.json()

                        if isinstance(assets, list):
                            photo_data = assets[0] if assets else None
                        else:
                            photo_data = assets

                        if not photo_data:
                            raise RuntimeError("No random photo returned")

                    except requests.RequestException:
                        # Fallback to regular fetch
                        response = self.session.get(f"{immich_url}/api/asset", params={"take": 100})
                        response.raise_for_status()
                        assets = response.json()
                        photo_data = self._select_photo(assets, "random")
                else:
                    # Fetch assets with pagination
                    response = self.session.get(f"{immich_url}/api/asset", params={"take": 100})
                    response.raise_for_status()
                    assets = response.json()
                    photo_data = self._select_photo(assets, selection_mode)

            return photo_data

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch from Immich: {e}")

    def _select_photo(self, assets: list, mode: str) -> Dict[str, Any]:
        """Select photo based on strategy."""
        if not assets:
            raise RuntimeError("No photos available")

        if mode == "random":
            return random.choice(assets)
        elif mode == "newest":
            return max(assets, key=lambda a: a.get("fileCreatedAt", ""))
        elif mode == "oldest":
            return min(assets, key=lambda a: a.get("fileCreatedAt", ""))
        else:
            return assets[0]

    def _download_photo(self, settings: Dict[str, Any], photo_data: Dict[str, Any]) -> Image.Image:
        """
        Download photo from Immich.

        Args:
            settings: Plugin settings
            photo_data: Photo metadata from Immich

        Returns:
            PIL.Image: Downloaded image

        Raises:
            RuntimeError: If download fails
        """
        immich_url = settings["immich_url"].rstrip("/")
        photo_id = photo_data["id"]

        try:
            image_url = f"{immich_url}/api/asset/file/{photo_id}"
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()

            # Load image from bytes
            image = Image.open(BytesIO(response.content))
            return image

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download photo: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load image: {e}")

    def _apply_ai_style(
        self, settings: Dict[str, Any], image: Image.Image, device_config: Dict[str, Any]
    ) -> Image.Image:
        """
        Apply AI style transformation to image.

        Args:
            settings: Plugin settings
            image: Input image
            device_config: Device configuration

        Returns:
            PIL.Image: Styled image

        Raises:
            RuntimeError: If styling fails (returns original image)
        """
        try:
            api_url = settings["ai_service_url"].rstrip("/")
            api_key = settings["ai_api_key"]
            style = settings["ai_style"]

            # Create AI session
            ai_session = requests.Session()
            ai_session.headers.update(
                {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
            )

            # Save image to temporary file for upload
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG", quality=95)
                temp_path = Path(temp_file.name)

            try:
                # Submit transformation job
                with open(temp_path, "rb") as f:
                    files = {"image": ("photo.jpg", f, "image/jpeg")}
                    data = {"style": style, "quality": "high", "format": "jpeg"}

                    response = ai_session.post(
                        f"{api_url}/v1/transform", files=files, data=data, timeout=30
                    )

                response.raise_for_status()
                result = response.json()
                job_id = result.get("job_id")

                if not job_id:
                    raise RuntimeError("No job_id returned from AI service")

                # Poll for completion (timeout 120 seconds)
                result_url = self._poll_ai_job(ai_session, api_url, job_id, timeout=120)

                # Download styled image
                response = ai_session.get(result_url, timeout=60)
                response.raise_for_status()

                styled_image = Image.open(BytesIO(response.content))
                return styled_image

            finally:
                # Clean up temp file
                temp_path.unlink(missing_ok=True)
                ai_session.close()

        except Exception as e:
            # Log error but return original image as fallback
            self.logger.warning(f"AI styling failed, using original photo: {e}")
            return image

    def _poll_ai_job(
        self, session: requests.Session, api_url: str, job_id: str, timeout: int = 120
    ) -> str:
        """Poll AI service until job completes."""
        start_time = time.time()
        poll_interval = 2

        while time.time() - start_time < timeout:
            try:
                response = session.get(f"{api_url}/v1/job/{job_id}")
                response.raise_for_status()

                job_status = response.json()
                status = job_status.get("status")

                if status == "completed":
                    result_url = job_status.get("result_url")
                    if not result_url:
                        raise RuntimeError("Job completed but no result_url")
                    return result_url

                elif status == "failed":
                    error = job_status.get("error", "Unknown error")
                    raise RuntimeError(f"AI job failed: {error}")

                elif status in ["pending", "processing"]:
                    time.sleep(poll_interval)
                    poll_interval = min(poll_interval * 1.5, 10)

                else:
                    raise RuntimeError(f"Unknown job status: {status}")

            except requests.RequestException as e:
                raise RuntimeError(f"Failed to check job status: {e}")

        raise RuntimeError(f"AI job timeout after {timeout} seconds")

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

        # Fit image to display (contain mode - show full image)
        if image_aspect > display_aspect:
            # Image is wider, fit to width
            new_width = display_width
            new_height = int(display_width / image_aspect)
        else:
            # Image is taller, fit to height
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

        # Draw error message
        try:
            font = ImageFont.load_default()
        except:
            font = None

        text = f"Error loading photo:\n{error_message}"
        draw.text((20, height // 2), text, fill="black", font=font)

        return image

    def get_cache_key(self, settings: Dict[str, Any]) -> str:
        """
        Generate cache key for content.

        Cache per day so we show same photo all day.
        """
        date = datetime.now().strftime("%Y-%m-%d")
        use_ai = settings.get("use_ai", False)
        style = settings.get("ai_style", "none") if use_ai else "none"
        return f"immich_{date}_{style}"

    def get_cache_ttl(self, settings: Dict[str, Any]) -> int:
        """Cache for 24 hours (one day)."""
        return 86400  # 24 hours in seconds

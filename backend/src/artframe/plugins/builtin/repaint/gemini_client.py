"""
Gemini API client for image style transformation.

Uses Google's Gemini API (Nano Banana) to transform photos into various artistic styles.
"""

import logging
from io import BytesIO
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google's Gemini API image generation."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-image"):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google AI API key
            model: Model to use for image generation
        """
        self.api_key = api_key
        self.model = model
        self._client: Optional[object] = None

    def _get_client(self):
        """Lazy-load the Gemini client."""
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
            except ImportError as e:
                raise RuntimeError(
                    "google-genai package not installed. "
                    "Run: pip install google-genai"
                ) from e
        return self._client

    def transform_image(self, image: Image.Image, style_prompt: str) -> Image.Image:
        """
        Transform an image using the given style prompt.

        Args:
            image: PIL Image to transform
            style_prompt: The style prompt describing the transformation

        Returns:
            PIL Image: The transformed image

        Raises:
            RuntimeError: If transformation fails
        """
        try:
            from google.genai import types

            client = self._get_client()

            # Convert PIL Image to bytes for the API
            image_bytes = self._image_to_bytes(image)

            # Create image part
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
            )

            # Generate the styled image
            logger.info(f"Sending image to Gemini API with model {self.model}")
            response = client.models.generate_content(
                model=self.model,
                contents=[style_prompt, image_part],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

            # Extract the image from the response
            if not response.candidates:
                raise RuntimeError("No response from Gemini API")

            # Find the image part in the response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    return Image.open(BytesIO(image_data))

            raise RuntimeError("No image data found in Gemini API response")

        except Exception as e:
            logger.error(f"Gemini API transformation failed: {e}")
            raise RuntimeError(f"Failed to transform image: {e}") from e

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to JPEG bytes."""
        # Convert to RGB if necessary (e.g., RGBA images)
        if image.mode != "RGB":
            image = image.convert("RGB")

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()

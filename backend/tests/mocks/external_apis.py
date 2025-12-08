"""
Mocks for external API services.

Provides mock implementations of external services like Immich and Gemini
that can be used in tests without making actual network requests.
"""

import io
from typing import Any, Optional
from unittest.mock import MagicMock

from PIL import Image


class MockResponse:
    """Mock HTTP response object."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[dict[str, Any]] = None,
        content: Optional[bytes] = None,
        text: str = "",
        headers: Optional[dict[str, str]] = None,
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content or b""
        self.text = text
        self.headers = headers or {"Content-Type": "application/json"}
        self.ok = 200 <= status_code < 300

    def json(self) -> dict[str, Any]:
        return self._json_data

    def raise_for_status(self) -> None:
        if not self.ok:
            raise Exception(f"HTTP {self.status_code}")


class MockRequestsSession:
    """
    Mock requests.Session for testing HTTP calls.

    Usage:
        mock_session = MockRequestsSession()
        mock_session.add_response("GET", "http://example.com/api", {"data": "test"})

        with patch("requests.Session", return_value=mock_session):
            # Your code that uses requests
    """

    def __init__(self):
        self._responses: dict[str, MockResponse] = {}
        self._call_history: list[dict[str, Any]] = []
        self.headers: dict[str, str] = {}

    def add_response(
        self,
        method: str,
        url: str,
        json_data: Optional[dict[str, Any]] = None,
        status_code: int = 200,
        content: Optional[bytes] = None,
    ) -> None:
        """Add a mock response for a specific method and URL."""
        key = f"{method.upper()}:{url}"
        self._responses[key] = MockResponse(
            status_code=status_code,
            json_data=json_data,
            content=content,
        )

    def add_image_response(self, method: str, url: str, size: tuple[int, int] = (100, 100)) -> None:
        """Add a mock response that returns an image."""
        img = Image.new("RGB", size, color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        content = buffer.getvalue()

        key = f"{method.upper()}:{url}"
        self._responses[key] = MockResponse(
            status_code=200,
            content=content,
            headers={"Content-Type": "image/jpeg"},
        )

    def _get_response(self, method: str, url: str) -> MockResponse:
        """Get the mock response for a request."""
        key = f"{method.upper()}:{url}"

        # Try exact match first
        if key in self._responses:
            return self._responses[key]

        # Try prefix match for URLs with query strings
        for response_key, response in self._responses.items():
            if key.startswith(response_key.split("?")[0]):
                return response

        # Default response
        return MockResponse(status_code=404, json_data={"error": "Not found"})

    def get(self, url: str, **kwargs) -> MockResponse:
        self._call_history.append({"method": "GET", "url": url, "kwargs": kwargs})
        return self._get_response("GET", url)

    def post(self, url: str, **kwargs) -> MockResponse:
        self._call_history.append({"method": "POST", "url": url, "kwargs": kwargs})
        return self._get_response("POST", url)

    def put(self, url: str, **kwargs) -> MockResponse:
        self._call_history.append({"method": "PUT", "url": url, "kwargs": kwargs})
        return self._get_response("PUT", url)

    def delete(self, url: str, **kwargs) -> MockResponse:
        self._call_history.append({"method": "DELETE", "url": url, "kwargs": kwargs})
        return self._get_response("DELETE", url)

    def get_call_history(self) -> list[dict[str, Any]]:
        """Get the history of all calls made."""
        return self._call_history

    def reset(self) -> None:
        """Reset call history."""
        self._call_history = []


class MockImmichClient:
    """
    Mock client for Immich photo service.

    Simulates the Immich API for testing photo retrieval plugins.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:2283",
        api_key: str = "test_api_key",
    ):
        self.server_url = server_url
        self.api_key = api_key
        self._photos: list[dict[str, Any]] = []
        self._albums: list[dict[str, Any]] = []
        self._connected = True

    def add_photo(
        self,
        id: str,
        filename: str = "photo.jpg",
        created_at: Optional[str] = None,
        album_id: Optional[str] = None,
    ) -> None:
        """Add a mock photo to the service."""
        self._photos.append(
            {
                "id": id,
                "originalFileName": filename,
                "fileCreatedAt": created_at or "2024-01-01T12:00:00.000Z",
                "type": "IMAGE",
                "albumId": album_id,
            }
        )

    def add_album(self, id: str, name: str, asset_count: int = 0) -> None:
        """Add a mock album."""
        self._albums.append(
            {
                "id": id,
                "albumName": name,
                "assetCount": asset_count,
            }
        )

    def get_random_photos(self, count: int = 1) -> list[dict[str, Any]]:
        """Get random photos (returns first N for testing)."""
        if not self._connected:
            raise ConnectionError("Not connected to Immich")
        return self._photos[:count]

    def get_photo_data(self, photo_id: str) -> bytes:
        """Get photo data (returns a test image)."""
        if not self._connected:
            raise ConnectionError("Not connected to Immich")

        img = Image.new("RGB", (100, 100), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    def get_albums(self) -> list[dict[str, Any]]:
        """Get all albums."""
        return self._albums

    def test_connection(self) -> bool:
        """Test connection to Immich."""
        return self._connected

    def set_connected(self, connected: bool) -> None:
        """Set connection state for testing."""
        self._connected = connected


class MockGeminiClient:
    """
    Mock client for Google Gemini API.

    Simulates the Gemini API for testing AI transformation plugins.
    """

    def __init__(self, api_key: str = "test_api_key"):
        self.api_key = api_key
        self._should_fail = False
        self._failure_message = ""
        self._call_count = 0

    def generate_styled_image(
        self,
        image: Image.Image,
        style: str,
        **kwargs,
    ) -> Image.Image:
        """Generate a styled image (returns a test image)."""
        self._call_count += 1

        if self._should_fail:
            raise Exception(self._failure_message or "Gemini API error")

        # Return a simple transformed image (color-shifted)
        return Image.new("RGB", image.size, color="purple")

    def set_failure(self, should_fail: bool, message: str = "") -> None:
        """Configure the mock to fail on next call."""
        self._should_fail = should_fail
        self._failure_message = message

    def get_call_count(self) -> int:
        """Get number of times generate was called."""
        return self._call_count

    def reset(self) -> None:
        """Reset mock state."""
        self._should_fail = False
        self._failure_message = ""
        self._call_count = 0


def create_mock_requests_get(responses: dict[str, Any]) -> MagicMock:
    """
    Create a mock for requests.get that returns different responses based on URL.

    Args:
        responses: Dict mapping URL patterns to response data

    Returns:
        MagicMock configured to return appropriate responses
    """
    mock = MagicMock()

    def side_effect(url, **kwargs):
        for pattern, data in responses.items():
            if pattern in url:
                response = MagicMock()
                response.status_code = data.get("status_code", 200)
                response.json.return_value = data.get("json", {})
                response.content = data.get("content", b"")
                response.ok = response.status_code < 400
                return response

        # Default 404 response
        response = MagicMock()
        response.status_code = 404
        response.ok = False
        return response

    mock.side_effect = side_effect
    return mock

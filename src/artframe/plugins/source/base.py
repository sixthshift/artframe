"""
Base class for source plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ...models import Photo


class SourcePlugin(ABC):
    """Abstract base class for photo source plugins."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the source plugin with configuration."""
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        """Validate the plugin configuration. Raise ValueError if invalid."""
        pass

    @abstractmethod
    def fetch_photo(self) -> Photo:
        """
        Fetch a photo from the source.

        Returns:
            Photo: The retrieved photo with metadata

        Raises:
            SourceError: If photo retrieval fails
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connectivity to the photo source.

        Returns:
            bool: True if connection is successful
        """
        pass

    @abstractmethod
    def get_available_albums(self) -> List[Dict[str, Any]]:
        """
        Get list of available albums/collections.

        Returns:
            List[Dict]: Album information
        """
        pass

    def get_photo_count(self, album_id: Optional[str] = None) -> int:
        """
        Get count of photos available.

        Args:
            album_id: Optional album ID to count

        Returns:
            int: Number of available photos
        """
        return 0


class SourceError(Exception):
    """Exception raised by source plugins."""
    pass
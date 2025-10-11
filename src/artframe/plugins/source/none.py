"""None source plugin - fallback that provides no photos."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import SourcePlugin, SourceError
from ...models import Photo


class NoneSource(SourcePlugin):
    """Fallback source plugin that provides no photos."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize None source."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.logger.info("NoneSource initialized - no photos will be provided")

    def validate_config(self) -> bool:
        """Validate configuration (always valid)."""
        return True

    def test_connection(self) -> bool:
        """Test connection (always succeeds)."""
        return True

    def fetch_photo(self) -> Photo:
        """Fetch photo (always fails with helpful message)."""
        raise SourceError(
            "No photo source configured. Please configure a valid photo source "
            "(immich, etc.) in your configuration file."
        )

    def get_available_albums(self) -> List[Dict[str, Any]]:
        """Get available albums (returns empty list)."""
        return []

    def get_photo_count(self, album_id: Optional[str] = None) -> int:
        """Get photo count (always returns 0)."""
        return 0
"""
Immich source plugin for photo retrieval.
"""

import requests
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from .base import SourcePlugin, SourceError
from ...models import Photo


class ImmichSource(SourcePlugin):
    """Immich photo source plugin."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Immich source plugin."""
        super().__init__(config)
        self.server_url = self.config['server_url'].rstrip('/')
        self.api_key = self.config['api_key']
        self.album_id = self.config.get('album_id')
        self.selection = self.config.get('selection', 'random')

        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Accept': 'application/json'
        })

    def validate_config(self) -> None:
        """Validate Immich configuration."""
        required_keys = ['server_url', 'api_key']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Immich config missing required key: {key}")

        if not self.config['server_url'].startswith(('http://', 'https://')):
            raise ValueError("server_url must start with http:// or https://")

        valid_selections = ['random', 'newest', 'oldest']
        selection = self.config.get('selection', 'random')
        if selection not in valid_selections:
            raise ValueError(f"Invalid selection method: {selection}. Valid options: {valid_selections}")

    def test_connection(self) -> bool:
        """Test connection to Immich server."""
        try:
            response = self.session.get(f"{self.server_url}/api/server-info/ping")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_available_albums(self) -> List[Dict[str, Any]]:
        """Get list of available albums."""
        try:
            response = self.session.get(f"{self.server_url}/api/album")
            response.raise_for_status()

            albums = response.json()
            return [
                {
                    'id': album['id'],
                    'name': album['albumName'],
                    'asset_count': album['assetCount'],
                    'created_at': album['createdAt']
                }
                for album in albums
            ]
        except requests.RequestException as e:
            raise SourceError(f"Failed to fetch albums: {e}")

    def get_photo_count(self, album_id: Optional[str] = None) -> int:
        """Get count of photos available."""
        try:
            if album_id or self.album_id:
                target_album = album_id or self.album_id
                response = self.session.get(f"{self.server_url}/api/album/{target_album}")
                response.raise_for_status()
                album_data = response.json()
                return album_data.get('assetCount', 0)
            else:
                # Get all assets count
                response = self.session.get(f"{self.server_url}/api/asset", params={'take': 1})
                response.raise_for_status()
                # This is a simplified approach - actual implementation would need pagination handling
                return 1000  # Placeholder
        except requests.RequestException as e:
            raise SourceError(f"Failed to get photo count: {e}")

    def fetch_photo(self) -> Photo:
        """Fetch a photo from Immich."""
        try:
            if self.album_id:
                photo_data = self._fetch_from_album()
            else:
                photo_data = self._fetch_from_all_assets()

            # Download the image
            image_url = f"{self.server_url}/api/asset/file/{photo_data['id']}"
            response = self.session.get(image_url)
            response.raise_for_status()

            # Save to temporary location
            temp_dir = Path("/tmp/artframe")
            temp_dir.mkdir(exist_ok=True)

            file_extension = photo_data.get('originalFileName', 'image.jpg').split('.')[-1]
            temp_path = temp_dir / f"{photo_data['id']}.{file_extension}"

            with open(temp_path, 'wb') as f:
                f.write(response.content)

            # Create Photo object
            return Photo(
                id=photo_data['id'],
                source_url=image_url,
                retrieved_at=datetime.now(),
                original_path=temp_path,
                metadata={
                    'original_filename': photo_data.get('originalFileName', ''),
                    'file_created_at': photo_data.get('fileCreatedAt', ''),
                    'file_modified_at': photo_data.get('fileModifiedAt', ''),
                    'device_id': photo_data.get('deviceId', ''),
                    'type': photo_data.get('type', ''),
                    'immich_id': photo_data['id']
                }
            )

        except requests.RequestException as e:
            raise SourceError(f"Failed to fetch photo: {e}")
        except Exception as e:
            raise SourceError(f"Unexpected error fetching photo: {e}")

    def _fetch_from_album(self) -> Dict[str, Any]:
        """Fetch photo from specific album."""
        response = self.session.get(f"{self.server_url}/api/album/{self.album_id}")
        response.raise_for_status()

        album_data = response.json()
        assets = album_data.get('assets', [])

        if not assets:
            raise SourceError(f"No assets found in album {self.album_id}")

        return self._select_asset_by_strategy(assets)

    def _fetch_from_all_assets(self) -> Dict[str, Any]:
        """Fetch photo from all available assets."""
        if self.selection == 'random':
            # Use Immich's random endpoint if available
            try:
                response = self.session.get(f"{self.server_url}/api/asset/random")
                response.raise_for_status()
                assets = response.json()

                if not assets:
                    raise SourceError("No random assets returned")

                return assets[0] if isinstance(assets, list) else assets
            except requests.RequestException:
                # Fallback to regular asset fetching
                pass

        # Fallback: fetch assets with pagination
        params = {
            'take': 100,
            'skip': 0
        }

        response = self.session.get(f"{self.server_url}/api/asset", params=params)
        response.raise_for_status()

        assets = response.json()
        if not assets:
            raise SourceError("No assets found")

        return self._select_asset_by_strategy(assets)

    def _select_asset_by_strategy(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select asset based on configured strategy."""
        if not assets:
            raise SourceError("No assets to select from")

        if self.selection == 'random':
            return random.choice(assets)
        elif self.selection == 'newest':
            return max(assets, key=lambda a: a.get('fileCreatedAt', ''))
        elif self.selection == 'oldest':
            return min(assets, key=lambda a: a.get('fileCreatedAt', ''))
        else:
            return assets[0]
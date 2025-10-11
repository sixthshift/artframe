"""
NanoBanana style plugin for AI image transformation.
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urljoin

from .base import StylePlugin, StyleError


class NanoBananaStyle(StylePlugin):
    """NanoBanana AI style transformation plugin."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize NanoBanana style plugin."""
        super().__init__(config)
        self.api_url = self.config['api_url'].rstrip('/')
        self.api_key = self.config['api_key']
        self.available_styles = self.config['styles']

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        })

    def validate_config(self) -> None:
        """Validate NanoBanana configuration."""
        required_keys = ['api_url', 'api_key', 'styles']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"NanoBanana config missing required key: {key}")

        if not self.config['api_url'].startswith(('http://', 'https://')):
            raise ValueError("api_url must start with http:// or https://")

        if not isinstance(self.config['styles'], list) or not self.config['styles']:
            raise ValueError("styles must be a non-empty list")

        # Validate rotation strategy if provided
        if 'rotation' in self.config:
            valid_rotations = ['daily', 'random', 'sequential']
            if self.config['rotation'] not in valid_rotations:
                raise ValueError(f"Invalid rotation strategy. Valid options: {valid_rotations}")

    def test_connection(self) -> bool:
        """Test connection to NanoBanana API."""
        try:
            response = self.session.get(f"{self.api_url}/v1/health")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_available_styles(self) -> List[str]:
        """Get list of available artistic styles."""
        try:
            response = self.session.get(f"{self.api_url}/v1/styles")
            response.raise_for_status()

            styles_data = response.json()
            return [style['name'] for style in styles_data.get('styles', [])]
        except requests.RequestException as e:
            # Fallback to configured styles if API call fails
            return self.available_styles.copy()

    def apply_style(self, image_path: Path, style: str, output_path: Path) -> bool:
        """
        Apply artistic style to image using NanoBanana API.

        Args:
            image_path: Path to input image
            style: Style name to apply
            output_path: Path where styled image should be saved

        Returns:
            bool: True if transformation successful
        """
        try:
            # Validate inputs
            if not image_path.exists():
                raise StyleError(f"Input image not found: {image_path}")

            if style not in self.available_styles:
                raise StyleError(f"Style '{style}' not available. Available styles: {self.available_styles}")

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Submit transformation job
            job_id = self._submit_transformation(image_path, style)

            # Poll for completion
            result_url = self._wait_for_completion(job_id)

            # Download result
            self._download_result(result_url, output_path)

            return True

        except Exception as e:
            raise StyleError(f"Style transformation failed: {e}")

    def _submit_transformation(self, image_path: Path, style: str) -> str:
        """Submit transformation job to NanoBanana API."""
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (image_path.name, f, 'image/jpeg')}
                data = {
                    'style': style,
                    'quality': 'high',
                    'format': 'jpeg'
                }

                response = self.session.post(
                    f"{self.api_url}/v1/transform",
                    files=files,
                    data=data,
                    timeout=30
                )

            response.raise_for_status()
            result = response.json()

            job_id = result.get('job_id')
            if not job_id:
                raise StyleError("No job_id returned from API")

            return job_id

        except requests.RequestException as e:
            raise StyleError(f"Failed to submit transformation: {e}")

    def _wait_for_completion(self, job_id: str, timeout: int = 300) -> str:
        """Wait for transformation job to complete."""
        start_time = time.time()
        poll_interval = 2  # Start with 2 second intervals

        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.api_url}/v1/job/{job_id}")
                response.raise_for_status()

                job_status = response.json()
                status = job_status.get('status')

                if status == 'completed':
                    result_url = job_status.get('result_url')
                    if not result_url:
                        raise StyleError("Job completed but no result_url provided")
                    return result_url

                elif status == 'failed':
                    error_msg = job_status.get('error', 'Unknown error')
                    raise StyleError(f"Transformation job failed: {error_msg}")

                elif status in ['pending', 'processing']:
                    # Continue polling
                    time.sleep(poll_interval)
                    # Increase poll interval gradually (exponential backoff)
                    poll_interval = min(poll_interval * 1.5, 10)

                else:
                    raise StyleError(f"Unknown job status: {status}")

            except requests.RequestException as e:
                raise StyleError(f"Failed to check job status: {e}")

        raise StyleError(f"Transformation timeout after {timeout} seconds")

    def _download_result(self, result_url: str, output_path: Path) -> None:
        """Download transformation result."""
        try:
            response = self.session.get(result_url, timeout=60)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        except requests.RequestException as e:
            raise StyleError(f"Failed to download result: {e}")

    def estimate_processing_time(self, image_path: Path, style: str) -> int:
        """
        Estimate processing time based on image size and style complexity.

        Args:
            image_path: Path to input image
            style: Style to apply

        Returns:
            int: Estimated processing time in seconds
        """
        try:
            # Get image file size
            file_size_mb = image_path.stat().st_size / (1024 * 1024)

            # Base processing time estimates by style
            style_multipliers = {
                'ghibli': 1.0,
                'impressionist': 1.2,
                'watercolor': 0.8,
                'oil_painting': 1.5,
                'pencil_sketch': 0.6
            }

            base_time = 20  # Base 20 seconds
            size_factor = max(1.0, file_size_mb / 2)  # Scale with file size
            style_factor = style_multipliers.get(style, 1.0)

            estimated_time = int(base_time * size_factor * style_factor)
            return min(estimated_time, 180)  # Cap at 3 minutes

        except Exception:
            return 30  # Default fallback
"""None style plugin - fallback that provides no styling."""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .base import StylePlugin, StyleError


class NoneStyle(StylePlugin):
    """Fallback style plugin that provides no styling."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize None style."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.logger.info("NoneStyle initialized - no styling will be applied")

    def validate_config(self) -> bool:
        """Validate configuration (always valid)."""
        return True

    def test_connection(self) -> bool:
        """Test connection (always succeeds)."""
        return True

    def apply_style(self, input_path: Path, style_name: str, output_path: Path) -> bool:
        """Apply style (always fails with helpful message)."""
        raise StyleError(
            f"No style provider configured. Cannot apply style '{style_name}'. "
            "Please configure a valid style provider (nanobanana, etc.) in your configuration file."
        )

    def get_available_styles(self) -> List[str]:
        """Get available styles (returns empty list)."""
        return []
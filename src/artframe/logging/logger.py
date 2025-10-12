"""
Domain-specific logger for Artframe operations.
"""

import logging
from typing import Optional


class Logger:
    """Logger with domain-specific methods for Artframe events."""

    def __init__(self, name: str):
        """
        Initialize logger.

        Args:
            name: Logger name (typically __name__)
        """
        self._logger = logging.getLogger(name)

    def log_initialization_start(self) -> None:
        """Log start of controller initialization."""
        self._logger.info("Initializing Artframe controller")

    def log_initialization_success(self) -> None:
        """Log successful controller initialization."""
        self._logger.info("Artframe controller initialized successfully")

    def log_initialization_error(self, error: Exception) -> None:
        """Log controller initialization error."""
        self._logger.error(f"Failed to initialize Artframe controller: {error}")

    def log_update_start(self) -> None:
        """Log start of daily photo update."""
        self._logger.info("Starting daily photo update")

    def log_photo_fetched(self, photo_id: str) -> None:
        """Log successful photo fetch."""
        self._logger.info(f"Fetched photo: {photo_id}")

    def log_style_selected(self, style: str) -> None:
        """Log style selection."""
        self._logger.info(f"Selected style: {style}")

    def log_style_applying(self, photo_id: str, style: str) -> None:
        """Log start of style transformation."""
        self._logger.info(f"Applying style '{style}' to photo {photo_id}")

    def log_cached_image_used(self, image_id: str) -> None:
        """Log use of stored styled image."""
        self._logger.info(f"Using stored styled image: {image_id}")

    def log_update_success(self) -> None:
        """Log successful update completion."""
        self._logger.info("Daily photo update completed successfully")

    def log_update_error(self, error: Exception) -> None:
        """Log update failure."""
        self._logger.error(f"Daily photo update failed: {error}")

    def log_display_error_failed(self, error: Exception) -> None:
        """Log failure to display error message."""
        self._logger.error(f"Failed to display error message: {error}")

    def log_scheduled_loop_start(self) -> None:
        """Log start of scheduled loop."""
        self._logger.info("Starting Artframe scheduled loop")

    def log_interrupt_received(self) -> None:
        """Log receipt of interrupt signal."""
        self._logger.info("Received interrupt signal, stopping")

    def log_scheduled_loop_error(self, error: Exception) -> None:
        """Log unexpected error in scheduled loop."""
        self._logger.error(f"Unexpected error in scheduled loop: {error}")

    def log_controller_stopping(self) -> None:
        """Log controller shutdown."""
        self._logger.info("Stopping Artframe controller")

    def log_manual_refresh_triggered(self) -> None:
        """Log manual refresh trigger."""
        self._logger.info("Manual refresh triggered")

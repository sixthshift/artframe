"""
Logging setup and configuration for Artframe.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional


def setup_logging(
    config: dict[str, Any], cli_level: Optional[str] = None, cli_file: Optional[Path] = None
) -> None:
    """
    Setup logging configuration from config file with CLI overrides.

    Args:
        config: Logging configuration from config file
        cli_level: Optional CLI override for log level
        cli_file: Optional CLI override for log file path
    """
    level = cli_level or config.get("level", "INFO")
    log_file = cli_file or config.get("file")

    log_level = getattr(logging, level.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    if log_file:
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        max_bytes = config.get("max_bytes", 10485760)
        backup_count = config.get("backup_count", 5)

        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers, force=True)

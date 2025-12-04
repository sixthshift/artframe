"""
File utilities for JSON persistence and directory management.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        The same path for chaining
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path, default: Optional[Any] = None) -> Any:
    """
    Load JSON from a file with error handling.

    Args:
        path: Path to JSON file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    path = Path(path)
    if not path.exists():
        return default

    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load JSON from {path}: {e}")
        return default


def save_json(path: Path, data: Any, indent: int = 2) -> bool:
    """
    Save data to a JSON file with error handling.

    Args:
        path: Path to JSON file
        data: Data to serialize
        indent: JSON indentation (default 2)

    Returns:
        True if saved successfully, False otherwise
    """
    path = Path(path)
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=indent)
        return True
    except OSError as e:
        logger.error(f"Failed to save JSON to {path}: {e}")
        return False

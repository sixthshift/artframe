"""
Type definitions for Artframe web module.

Note: With FastAPI, most types are now defined as Pydantic models in schemas.py.
This module is kept for any shared type definitions.
"""

from typing import Any, Dict

# Type alias for settings dictionary
SettingsDict = Dict[str, Any]

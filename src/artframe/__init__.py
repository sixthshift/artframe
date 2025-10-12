"""
Artframe - Digital Photo Frame with AI Style Transformation

A Raspberry Pi-based digital photo frame that automatically retrieves photos
from sources like Immich and applies artistic styles using AI services.
"""

__version__ = "1.0.0"
__author__ = "Artframe Team"

from .config import ConfigManager
from .models import DisplayState, Photo, StyledImage

__all__ = ["Photo", "StyledImage", "DisplayState", "ConfigManager"]

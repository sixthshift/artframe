"""
Source plugins for photo retrieval.
"""

from .base import SourcePlugin
from .immich import ImmichSource
from .none import NoneSource

__all__ = ["SourcePlugin", "ImmichSource", "NoneSource"]
"""
Plugin system for Artframe.

Provides abstract base classes for source and style plugins,
allowing modular integration of different photo sources and AI services.
"""

from .source.base import SourcePlugin
from .style.base import StylePlugin

__all__ = ["SourcePlugin", "StylePlugin"]
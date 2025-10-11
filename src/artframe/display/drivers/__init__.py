"""
Display drivers for different e-ink displays.
"""

from .base import DriverInterface

__all__ = ["DriverInterface", "MockDriver", "Spectra6Driver"]

def __getattr__(name):
    """Lazy import for drivers."""
    if name == "MockDriver":
        from .mock import MockDriver
        return MockDriver
    elif name == "Spectra6Driver":
        from .spectra6 import Spectra6Driver
        return Spectra6Driver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
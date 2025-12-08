"""
Display drivers for different e-ink displays.
"""

from .base import DriverInterface

__all__ = ["DriverInterface", "MockDriver", "WaveshareDriver"]


def __getattr__(name):
    """Lazy import for drivers."""
    if name == "MockDriver":
        from .mock import MockDriver

        return MockDriver
    elif name == "WaveshareDriver":
        from .waveshare_driver import WaveshareDriver

        return WaveshareDriver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

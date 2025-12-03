"""
Web routes for Artframe dashboard.

This module organizes routes into logical groups:
- core: Main control endpoints (status, config, update, clear, restart, scheduler)
- system: System info and logs
- display: Display preview and health
- plugins: Plugin listing and instance CRUD
- schedules: Slot-based schedule management
- spa: Single-page application serving
"""

from . import core, display, plugins, schedules, spa, system

__all__ = ["core", "display", "plugins", "schedules", "spa", "system"]

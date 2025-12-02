"""
Web routes for Artframe dashboard.

This module organizes routes into logical groups:
- core: Main control endpoints (status, config, update, clear, restart, scheduler)
- system: System info and logs
- display: Display preview and health
- plugins: Plugin listing and instance CRUD
- playlists: Playlist CRUD and activation
- schedules: Slot-based schedule management
- spa: Single-page application serving
"""

from . import core, display, playlists, plugins, schedules, spa, system

__all__ = ["core", "display", "playlists", "plugins", "schedules", "spa", "system"]

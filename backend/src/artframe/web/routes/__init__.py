"""
Web routes for Artframe dashboard.

This module organizes routes into logical groups:
- core: Main control endpoints (status, connections, update, clear, restart)
- config: Configuration management
- scheduler: Scheduler control (status, pause, resume)
- system: System info and logs
- display: Display preview and health
- plugins: Plugin listing and details
- instances: Plugin instance CRUD
- schedules: Slot-based schedule management
- spa: Single-page application serving
"""

from . import config, core, display, instances, plugins, scheduler, schedules, spa, system

__all__ = [
    "config",
    "core",
    "display",
    "instances",
    "plugins",
    "schedules",
    "scheduler",
    "spa",
    "system",
]

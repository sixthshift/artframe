"""
FastAPI dependency injection for Artframe.

Provides typed dependencies for route handlers, enabling better testability
and cleaner code than global state access.
"""

from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from ..controller import ArtframeController
    from ..playlists.schedule_manager import ScheduleManager
    from ..plugins.instance_manager import InstanceManager


def get_app_state(request: Request):
    """Get the application state from the request."""
    return request.app.state


def get_controller(request: Request) -> "ArtframeController":
    """Get the Artframe controller."""
    return request.app.state.controller


def get_instance_manager(request: Request) -> "InstanceManager":
    """Get the plugin instance manager."""
    return request.app.state.instance_manager


def get_schedule_manager(request: Request) -> "ScheduleManager":
    """Get the schedule manager."""
    return request.app.state.schedule_manager


def get_device_config(request: Request) -> dict:
    """Get device configuration from the controller."""
    controller = request.app.state.controller
    display_config = controller.config_manager.get_display_config()
    return {
        "width": display_config.get("width", 600),
        "height": display_config.get("height", 448),
        "rotation": display_config.get("rotation", 0),
        "color_mode": display_config.get("color_mode", "grayscale"),
    }

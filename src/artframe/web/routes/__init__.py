"""
Web routes for Artframe dashboard.

This module organizes routes into logical groups for better maintainability.
"""

from typing import cast

from flask import Blueprint, current_app

from ..types import ArtframeFlask

# Create the main blueprint
bp = Blueprint("dashboard", __name__)


def get_app() -> ArtframeFlask:
    """Get the current app with proper typing."""
    return cast(ArtframeFlask, current_app)


# Import route modules to register their routes
from . import api_core  # noqa: E402, F401
from . import api_display  # noqa: E402, F401
from . import api_playlists  # noqa: E402, F401
from . import api_plugins  # noqa: E402, F401
from . import api_schedules  # noqa: E402, F401
from . import api_system  # noqa: E402, F401
from . import pages  # noqa: E402, F401

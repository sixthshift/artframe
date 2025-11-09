"""
Type definitions for Flask app with custom attributes.
"""

import threading
from flask import Flask

from ..controller import ArtframeController
from ..playlists import PlaylistManager
from ..playlists.schedule_executor import ScheduleExecutor
from ..playlists.schedule_manager import ScheduleManager
from ..plugins.instance_manager import InstanceManager


class ArtframeFlask(Flask):
    """
    Flask app with Artframe-specific attributes.

    This adds type hints for custom attributes we attach to the Flask app.
    """

    controller: ArtframeController
    instance_manager: InstanceManager
    playlist_manager: PlaylistManager
    schedule_manager: ScheduleManager
    schedule_executor: ScheduleExecutor
    scheduler_started: bool
    scheduler_thread: threading.Thread

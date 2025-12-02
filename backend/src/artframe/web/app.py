"""
FastAPI application setup for Artframe web dashboard.
"""

import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..controller import ArtframeController
from ..playlists import PlaylistManager
from ..playlists.schedule_executor import ScheduleExecutor
from ..playlists.schedule_manager import ScheduleManager
from ..plugins.instance_manager import InstanceManager
from ..plugins.plugin_registry import load_plugins


class AppState:
    """Application state container for shared resources."""

    def __init__(self):
        self.controller: Optional[ArtframeController] = None
        self.instance_manager: Optional[InstanceManager] = None
        self.playlist_manager: Optional[PlaylistManager] = None
        self.schedule_manager: Optional[ScheduleManager] = None
        self.schedule_executor: Optional[ScheduleExecutor] = None
        self.scheduler_started: bool = False
        self.scheduler_thread: Optional[threading.Thread] = None


# Global app state
app_state = AppState()


def create_app(controller: ArtframeController, config: Optional[dict] = None) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        controller: Artframe controller instance
        config: Optional configuration

    Returns:
        Configured FastAPI application
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup and shutdown lifecycle management."""
        # Startup: Initialize managers and start scheduler
        app_state.controller = controller

        # Load plugins from builtin directory
        plugins_dir = Path(__file__).parent.parent / "plugins" / "builtin"
        load_plugins(plugins_dir)

        # Create instance manager
        storage_dir = Path.home() / ".artframe" / "data"
        app_state.instance_manager = InstanceManager(storage_dir)

        # Create playlist manager
        app_state.playlist_manager = PlaylistManager(storage_dir)

        # Create schedule manager and executor
        app_state.schedule_manager = ScheduleManager(storage_dir)
        device_config = {
            "width": 600,  # TODO: Get from controller/config
            "height": 448,
            "rotation": 0,
            "color_mode": "grayscale",
        }
        app_state.schedule_executor = ScheduleExecutor(
            app_state.schedule_manager, app_state.instance_manager, device_config
        )

        # Start scheduler in background thread
        if not app_state.scheduler_started:
            app_state.scheduler_started = True
            scheduler_thread = threading.Thread(
                target=controller.run_scheduled_loop, daemon=True, name="ArtframeScheduler"
            )
            scheduler_thread.start()
            app_state.scheduler_thread = scheduler_thread

        yield

        # Shutdown: cleanup if needed
        pass

    app = FastAPI(
        title="Artframe API",
        description="REST API for Artframe e-ink display platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware for frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and include routers
    from .routes import api_core, api_display, api_playlists, api_plugins, api_schedules, api_system
    from .routes import pages

    app.include_router(api_core.router, tags=["Core"])
    app.include_router(api_display.router, tags=["Display"])
    app.include_router(api_playlists.router, tags=["Playlists"])
    app.include_router(api_plugins.router, tags=["Plugins"])
    app.include_router(api_schedules.router, tags=["Schedules"])
    app.include_router(api_system.router, tags=["System"])
    app.include_router(pages.router, tags=["Pages"])

    return app


def get_state() -> AppState:
    """Get the global application state."""
    return app_state

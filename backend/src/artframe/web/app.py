"""
FastAPI application setup for Artframe web dashboard.
"""

import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..controller import ArtframeController
from ..plugins.plugin_registry import load_plugins


def create_app(controller: ArtframeController) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        controller: Artframe controller instance

    Returns:
        Configured FastAPI application
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup and shutdown lifecycle management."""
        # Startup: Initialize managers and start scheduler
        app.state.controller = controller

        # Load plugins from builtin directory
        plugins_dir = Path(__file__).parent.parent / "plugins" / "builtin"
        load_plugins(plugins_dir)

        # Use the controller's managers so API and orchestrator share the same state
        app.state.instance_manager = controller.instance_manager
        app.state.schedule_manager = controller.schedule_manager

        # Start scheduler in background thread
        if not getattr(app.state, "scheduler_started", False):
            app.state.scheduler_started = True
            scheduler_thread = threading.Thread(
                target=controller.run_scheduled_loop, daemon=True, name="ArtframeScheduler"
            )
            scheduler_thread.start()
            app.state.scheduler_thread = scheduler_thread

        yield

        # Shutdown: cleanup if needed
        pass

    app = FastAPI(
        title="Artframe API",
        description="REST API for Artframe e-ink display platform",
        version="1.0.0",
        lifespan=lifespan,
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
        swagger_favicon_url="/favicon.svg",
        redoc_url=None,  # Disable ReDoc, we use /api instead
    )

    # Add CORS middleware for frontend development
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and include routers
    from .routes import (
        config as config_routes,
    )
    from .routes import (
        core,
        display,
        instances,
        plugins,
        scheduler,
        schedules,
        spa,
        system,
    )

    app.include_router(core.router)
    app.include_router(config_routes.router)
    app.include_router(scheduler.router)
    app.include_router(system.router)
    app.include_router(display.router)
    app.include_router(plugins.router)
    app.include_router(instances.router)
    app.include_router(schedules.router)
    app.include_router(spa.router)

    return app

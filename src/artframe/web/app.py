"""
Flask application setup for Artframe web dashboard.
"""

import threading
from pathlib import Path
from flask import Flask
from typing import Optional

from ..controller import ArtframeController


def create_app(controller: ArtframeController, config: Optional[dict] = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        controller: Artframe controller instance
        config: Optional Flask configuration

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    if config:
        app.config.update(config)

    app.controller = controller

    # Initialize InstanceManager
    from ..plugins.instance_manager import InstanceManager
    from ..plugins.plugin_registry import load_plugins

    # Load plugins from builtin directory
    plugins_dir = Path(__file__).parent.parent / 'plugins' / 'builtin'
    load_plugins(plugins_dir)

    # Create instance manager
    storage_dir = Path.home() / '.artframe' / 'data'
    app.instance_manager = InstanceManager(storage_dir)

    from . import routes
    app.register_blueprint(routes.bp)

    @app.before_request
    def start_scheduler_once():
        """Start scheduler in background thread on first request."""
        if not hasattr(app, 'scheduler_started'):
            app.scheduler_started = True
            scheduler_thread = threading.Thread(
                target=controller.run_scheduled_loop,
                daemon=True,
                name="ArtframeScheduler"
            )
            scheduler_thread.start()
            app.scheduler_thread = scheduler_thread

    return app
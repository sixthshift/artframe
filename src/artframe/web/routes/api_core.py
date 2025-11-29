"""
Core API routes for Artframe dashboard.

Includes status, config, update, clear, restart, and scheduler APIs.
"""

import os
import signal

from flask import jsonify, request

from . import bp, get_app


@bp.route("/api/status")
def api_status():
    """Get current system status as JSON."""
    controller = get_app().controller

    try:
        status = controller.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/config")
def api_config():
    """Get current configuration as JSON."""
    controller = get_app().controller

    try:
        config = controller.config_manager.config
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/connections")
def api_connections():
    """Test all external connections."""
    controller = get_app().controller

    try:
        connections = controller.test_connections()
        return jsonify({"success": True, "data": connections})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/update", methods=["POST"])
def api_trigger_update():
    """Trigger immediate photo update."""
    controller = get_app().controller

    try:
        success = controller.manual_refresh()
        return jsonify(
            {
                "success": success,
                "message": "Update completed successfully" if success else "Update failed",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/clear", methods=["POST"])
def api_clear_display():
    """Clear the display."""
    controller = get_app().controller

    try:
        controller.display_controller.clear_display()
        return jsonify({"success": True, "message": "Display cleared"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/config", methods=["PUT"])
def api_update_config():
    """Update in-memory configuration (validation only, not saved)."""
    controller = get_app().controller

    try:
        new_config = request.get_json()
        if not new_config:
            return jsonify({"success": False, "error": "No configuration data provided"}), 400

        # Validate and update in-memory config
        controller.config_manager.update_config(new_config)

        return jsonify(
            {"success": True, "message": "Configuration updated in memory (not saved to file yet)"}
        )
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid configuration: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/config/save", methods=["POST"])
def api_save_config():
    """Save current in-memory configuration to YAML file."""
    controller = get_app().controller

    try:
        controller.config_manager.save_to_file(backup=True)
        return jsonify(
            {
                "success": True,
                "message": "Configuration saved to file. Restart required for changes to take effect.",
                "restart_required": True,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save configuration: {e}"}), 500


@bp.route("/api/config/revert", methods=["POST"])
def api_revert_config():
    """Revert in-memory config to what's on disk."""
    controller = get_app().controller

    try:
        controller.config_manager.revert_to_file()
        return jsonify({"success": True, "message": "Configuration reverted to saved version"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/restart", methods=["POST"])
def api_restart():
    """Restart the application."""
    try:
        # Send SIGTERM to self to trigger graceful restart
        # In production, systemd will restart the service automatically
        os.kill(os.getpid(), signal.SIGTERM)

        return jsonify({"success": True, "message": "Restart initiated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Scheduler APIs =====


@bp.route("/api/scheduler/status")
def api_scheduler_status():
    """Get scheduler status."""
    controller = get_app().controller

    try:
        status = controller.scheduler.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/scheduler/pause", methods=["POST"])
def api_scheduler_pause():
    """Pause automatic updates (daily e-ink refresh still occurs)."""
    controller = get_app().controller

    try:
        controller.scheduler.pause()
        return jsonify(
            {
                "success": True,
                "message": "Scheduler paused. Daily e-ink refresh will still occur for screen health.",
                "status": controller.scheduler.get_status(),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/scheduler/resume", methods=["POST"])
def api_scheduler_resume():
    """Resume automatic updates."""
    controller = get_app().controller

    try:
        controller.scheduler.resume()
        return jsonify(
            {
                "success": True,
                "message": "Scheduler resumed",
                "status": controller.scheduler.get_status(),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/source/stats")
def api_source_stats():
    """Get source statistics."""
    controller = get_app().controller

    try:
        # Basic stats for now
        return jsonify(
            {
                "success": True,
                "data": {
                    "provider": controller.config_manager.get_source_config().get(
                        "provider", "Unknown"
                    ),
                    "total_photos": "N/A",  # TODO: Get from source plugin
                    "album_name": controller.config_manager.get_source_config()
                    .get("config", {})
                    .get("album_id", "N/A"),
                    "last_sync": "N/A",  # TODO: Track sync time
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

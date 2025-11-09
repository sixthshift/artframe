"""
Web routes for Artframe dashboard.
"""

import os
import signal
from pathlib import Path
from typing import Any, cast

from flask import Blueprint, current_app, jsonify, render_template, request, send_file

from .types import ArtframeFlask

# Placeholder image path for when no display image is available
PLACEHOLDER_IMAGE_PATH = Path(__file__).parent / "static" / "placeholder.png"

bp = Blueprint("dashboard", __name__)


def get_app() -> ArtframeFlask:
    """Get the current app with proper typing."""
    return cast(ArtframeFlask, current_app)


@bp.route("/")
def index():
    """Render main dashboard."""
    return render_template("dashboard.html")


@bp.route("/display")
def display_page():
    """Render display page."""
    return render_template("display.html")


@bp.route("/system")
def system_page():
    """Render system page."""
    return render_template("system.html")


@bp.route("/config")
def config_page():
    """Render configuration page."""
    return render_template("config.html")


@bp.route("/plugins")
def plugins_page():
    """Render plugins management page."""
    return render_template("plugins.html")


@bp.route("/playlists")
def playlists_page():
    """Render playlists management page."""
    return render_template("playlists.html")


@bp.route("/schedule")
def schedule_page():
    """Render schedule management page."""
    return render_template("schedule.html")


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


@bp.route("/api/display/current")
def api_display_current():
    """Get current display information."""
    controller = get_app().controller

    try:
        state = controller.display_controller.get_state()
        driver = controller.display_controller.driver

        # Check if using mock driver
        has_preview = hasattr(driver, 'get_current_image_path')
        plugin_info = driver.get_last_plugin_info() if hasattr(driver, 'get_last_plugin_info') else {}

        return jsonify(
            {
                "success": True,
                "data": {
                    "image_id": state.current_image_id,
                    "last_update": state.last_refresh.isoformat() if state.last_refresh else None,
                    "plugin_name": plugin_info.get("plugin_name", "Unknown"),
                    "instance_name": plugin_info.get("instance_name", "Unknown"),
                    "status": state.status,
                    "has_preview": has_preview,
                    "display_count": driver.get_display_count() if hasattr(driver, 'get_display_count') else 0,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/display/preview")
def api_display_preview():
    """Serve the current display preview image (mock driver only)."""
    from flask import send_file
    from pathlib import Path
    import os
    controller = get_app().controller

    try:
        driver = controller.display_controller.driver

        # Check if mock driver
        if hasattr(driver, 'get_current_image_path'):
            # Try to get the current image path
            image_path = driver.get_current_image_path()

            # If no image displayed yet, check if latest.png exists in output dir
            if not image_path or not image_path.exists():
                # Get output dir and ensure it's an absolute path (MockDriver only)
                output_dir = getattr(driver, 'output_dir', None)
                if output_dir is None:
                    return send_file(PLACEHOLDER_IMAGE_PATH, mimetype="image/png")
                if isinstance(output_dir, str):
                    output_dir = Path(output_dir)

                # Make absolute if relative
                if not output_dir.is_absolute():
                    # Resolve relative to project root (where config file is)
                    project_root = Path(__file__).parent.parent.parent.parent
                    output_dir = (project_root / output_dir).resolve()

                latest_path = output_dir / "latest.png"

                if latest_path.exists():
                    return send_file(str(latest_path), mimetype='image/png')
            elif image_path.exists():
                return send_file(str(image_path), mimetype='image/png')

        # Return placeholder if no image available
        return jsonify({"success": False, "error": "No preview available"}), 404

    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        return jsonify({"success": False, "error": str(e), "detail": error_detail}), 500


@bp.route("/api/display/history")
def api_display_history():
    """Get display history."""
    try:
        # TODO: Implement history tracking
        return jsonify({"success": True, "data": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/display/health")
def api_display_health():
    """Get e-ink display health metrics."""
    controller = get_app().controller

    try:
        state = controller.display_controller.get_state()
        return jsonify(
            {
                "success": True,
                "data": {
                    "refresh_count": 0,  # TODO: Track refresh count
                    "last_refresh": state.last_refresh.isoformat() if state.last_refresh else None,
                    "status": state.status,
                    "error_count": state.error_count,
                },
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


@bp.route("/api/system/info")
def api_system_info():
    """Get system information."""
    try:
        import platform
        import time
        from datetime import timedelta

        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime_seconds = psutil.boot_time()
        uptime = str(timedelta(seconds=int(time.time() - uptime_seconds)))

        # Try to get temperature (Raspberry Pi)
        temp = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = round(int(f.read()) / 1000, 1)
        except Exception:
            pass

        return jsonify(
            {
                "success": True,
                "data": {
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory.percent, 1),
                    "disk_percent": round(disk.percent, 1),
                    "temperature": temp,
                    "uptime": uptime,
                    "platform": platform.system(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/system/logs")
def api_system_logs():
    """Get system logs."""
    try:
        # TODO: Read from actual log file
        # For now, return placeholder
        return jsonify(
            {
                "success": True,
                "data": [
                    {
                        "timestamp": "2025-09-27 20:00:00",
                        "level": "INFO",
                        "message": "Artframe controller initialized successfully",
                    },
                    {
                        "timestamp": "2025-09-27 20:00:30",
                        "level": "INFO",
                        "message": "Starting Artframe scheduled loop",
                    },
                ],
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/system/logs/export")
def api_system_logs_export():
    """Export system logs as text file."""
    try:
        # TODO: Read from actual log file
        logs_text = "Artframe System Logs\n\n"
        logs_text += "2025-09-27 20:00:00 INFO Artframe controller initialized successfully\n"

        from flask import Response

        return Response(
            logs_text,
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment;filename=artframe-logs.txt"},
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Plugin Management APIs =====


@bp.route("/api/plugins")
def api_plugins_list():
    """Get list of all available plugins."""
    try:
        from ..plugins.plugin_registry import list_plugin_metadata

        plugins_data = []
        for metadata in list_plugin_metadata():
            plugins_data.append(
                {
                    "id": metadata.plugin_id,
                    "display_name": metadata.display_name,
                    "class_name": metadata.class_name,
                    "description": metadata.description,
                    "author": metadata.author,
                    "version": metadata.version,
                    "icon": metadata.icon,
                }
            )

        return jsonify({"success": True, "data": plugins_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/<plugin_id>")
def api_plugin_details(plugin_id):
    """Get details for a specific plugin."""
    try:
        from ..plugins.plugin_registry import get_plugin_metadata

        metadata = get_plugin_metadata(plugin_id)
        if metadata is None:
            return jsonify({"success": False, "error": f"Plugin not found: {plugin_id}"}), 404

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": metadata.plugin_id,
                    "display_name": metadata.display_name,
                    "class_name": metadata.class_name,
                    "description": metadata.description,
                    "author": metadata.author,
                    "version": metadata.version,
                    "icon": metadata.icon,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/<plugin_id>/settings-template")
def api_plugin_settings_template(plugin_id):
    """Get plugin's settings HTML template."""
    try:
        from ..plugins.plugin_registry import get_plugin

        plugin = get_plugin(plugin_id)
        if plugin is None:
            return jsonify({"success": False, "error": f"Plugin not found: {plugin_id}"}), 404

        # Look for settings.html in plugin directory
        plugin_dir = plugin.get_plugin_directory()
        settings_file = plugin_dir / "settings.html"

        if not settings_file.exists():
            return (
                jsonify({"success": False, "error": "No settings template found for this plugin"}),
                404,
            )

        with open(settings_file, "r") as f:
            template_html = f.read()

        return jsonify({"success": True, "data": {"template": template_html}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Plugin Instance Management APIs =====


@bp.route("/api/plugins/instances", methods=["GET"])
def api_instances_list():
    """Get list of all plugin instances."""
    try:
        instance_manager = get_app().instance_manager
        instances = instance_manager.list_instances()

        instances_data = []
        for inst in instances:
            instances_data.append(
                {
                    "id": inst.id,
                    "plugin_id": inst.plugin_id,
                    "name": inst.name,
                    "settings": inst.settings,
                    "enabled": inst.enabled,
                    "created_at": inst.created_at.isoformat(),
                    "updated_at": inst.updated_at.isoformat(),
                }
            )

        return jsonify({"success": True, "data": instances_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances", methods=["POST"])
def api_instances_create():
    """Create a new plugin instance."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        plugin_id = data.get("plugin_id")
        name = data.get("name")
        settings = data.get("settings", {})

        if not plugin_id:
            return jsonify({"success": False, "error": "plugin_id is required"}), 400

        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400

        instance_manager = get_app().instance_manager
        instance = instance_manager.create_instance(plugin_id, name, settings)

        if instance is None:
            return (
                jsonify(
                    {"success": False, "error": "Failed to create instance (check validation)"}
                ),
                400,
            )

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": instance.id,
                    "plugin_id": instance.plugin_id,
                    "name": instance.name,
                    "settings": instance.settings,
                    "enabled": instance.enabled,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances/<instance_id>", methods=["GET"])
def api_instance_details(instance_id):
    """Get details for a specific instance."""
    try:
        instance_manager = get_app().instance_manager
        instance = instance_manager.get_instance(instance_id)

        if instance is None:
            return jsonify({"success": False, "error": "Instance not found"}), 404

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": instance.id,
                    "plugin_id": instance.plugin_id,
                    "name": instance.name,
                    "settings": instance.settings,
                    "enabled": instance.enabled,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances/<instance_id>", methods=["PUT"])
def api_instance_update(instance_id):
    """Update an instance."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        settings = data.get("settings")

        instance_manager = get_app().instance_manager
        success = instance_manager.update_instance(instance_id, name, settings)

        if not success:
            return jsonify({"success": False, "error": "Failed to update instance"}), 400

        instance = instance_manager.get_instance(instance_id)
        if instance is None:
            return jsonify({"success": False, "error": "Instance not found"}), 404
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": instance.id,
                    "plugin_id": instance.plugin_id,
                    "name": instance.name,
                    "settings": instance.settings,
                    "enabled": instance.enabled,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances/<instance_id>", methods=["DELETE"])
def api_instance_delete(instance_id):
    """Delete an instance."""
    try:
        instance_manager = get_app().instance_manager
        success = instance_manager.delete_instance(instance_id)

        if not success:
            return jsonify({"success": False, "error": "Failed to delete instance"}), 400

        return jsonify({"success": True, "message": "Instance deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances/<instance_id>/enable", methods=["POST"])
def api_instance_enable(instance_id):
    """Enable an instance."""
    try:
        instance_manager = get_app().instance_manager
        success = instance_manager.enable_instance(instance_id)

        if not success:
            return jsonify({"success": False, "error": "Failed to enable instance"}), 400

        return jsonify({"success": True, "message": "Instance enabled successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances/<instance_id>/disable", methods=["POST"])
def api_instance_disable(instance_id):
    """Disable an instance."""
    try:
        instance_manager = get_app().instance_manager
        success = instance_manager.disable_instance(instance_id)

        if not success:
            return jsonify({"success": False, "error": "Failed to disable instance"}), 400

        return jsonify({"success": True, "message": "Instance disabled successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/plugins/instances/<instance_id>/test", methods=["POST"])
def api_instance_test(instance_id):
    """Test run a plugin instance."""
    try:
        instance_manager = get_app().instance_manager

        # Get device config from display controller
        device_config = {
            "width": 600,  # TODO: Get from actual display
            "height": 448,
            "rotation": 0,
            "color_mode": "grayscale",
        }

        success, error_msg = instance_manager.test_instance(instance_id, device_config)

        if not success:
            return jsonify({"success": False, "error": error_msg or "Test failed"}), 400

        return jsonify({"success": True, "message": "Instance test successful"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Playlist Management APIs =====


@bp.route("/api/playlists", methods=["GET"])
def api_playlists_list():
    """Get list of all playlists."""
    try:
        playlist_manager = get_app().playlist_manager
        playlists = playlist_manager.list_playlists()

        playlists_data = []
        for playlist in playlists:
            playlists_data.append(
                {
                    "id": playlist.id,
                    "name": playlist.name,
                    "description": playlist.description,
                    "enabled": playlist.enabled,
                    "items": [
                        {
                            "instance_id": item.instance_id,
                            "duration_seconds": item.duration_seconds,
                            "order": item.order,
                        }
                        for item in playlist.items
                    ],
                    "created_at": playlist.created_at.isoformat(),
                    "updated_at": playlist.updated_at.isoformat(),
                }
            )

        active_playlist_id = playlist_manager.get_active_playlist_id()

        return jsonify(
            {"success": True, "data": playlists_data, "active_playlist_id": active_playlist_id}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/playlists", methods=["POST"])
def api_playlist_create():
    """Create a new playlist."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        description = data.get("description", "")
        items_data = data.get("items", [])

        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400

        # Parse items
        from ..models import PlaylistItem
        from typing import List

        items: List[PlaylistItem] = []
        for item_data in items_data:
            items.append(
                PlaylistItem(
                    instance_id=item_data["instance_id"],
                    duration_seconds=item_data["duration_seconds"],
                    order=item_data.get("order", len(items)),
                )
            )

        playlist_manager = get_app().playlist_manager
        playlist = playlist_manager.create_playlist(name, description, items)

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": playlist.id,
                    "name": playlist.name,
                    "description": playlist.description,
                    "enabled": playlist.enabled,
                    "items": [
                        {
                            "instance_id": item.instance_id,
                            "duration_seconds": item.duration_seconds,
                            "order": item.order,
                        }
                        for item in playlist.items
                    ],
                    "created_at": playlist.created_at.isoformat(),
                    "updated_at": playlist.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/playlists/<playlist_id>", methods=["GET"])
def api_playlist_details(playlist_id):
    """Get details for a specific playlist."""
    try:
        playlist_manager = get_app().playlist_manager
        playlist = playlist_manager.get_playlist(playlist_id)

        if playlist is None:
            return jsonify({"success": False, "error": "Playlist not found"}), 404

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": playlist.id,
                    "name": playlist.name,
                    "description": playlist.description,
                    "enabled": playlist.enabled,
                    "items": [
                        {
                            "instance_id": item.instance_id,
                            "duration_seconds": item.duration_seconds,
                            "order": item.order,
                        }
                        for item in playlist.items
                    ],
                    "created_at": playlist.created_at.isoformat(),
                    "updated_at": playlist.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/playlists/<playlist_id>", methods=["PUT"])
def api_playlist_update(playlist_id):
    """Update a playlist."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        description = data.get("description")
        enabled = data.get("enabled")
        items_data = data.get("items")

        # Parse items if provided
        from typing import List, Optional
        from ..models import PlaylistItem

        items: Optional[List[PlaylistItem]] = None
        if items_data is not None:
            items = []
            for item_data in items_data:
                items.append(
                    PlaylistItem(
                        instance_id=item_data["instance_id"],
                        duration_seconds=item_data["duration_seconds"],
                        order=item_data.get("order", len(items)),
                    )
                )

        playlist_manager = get_app().playlist_manager
        success = playlist_manager.update_playlist(
            playlist_id, name=name, description=description, items=items, enabled=enabled
        )

        if not success:
            return jsonify({"success": False, "error": "Failed to update playlist"}), 400

        playlist = playlist_manager.get_playlist(playlist_id)
        if playlist is None:
            return jsonify({"success": False, "error": "Playlist not found"}), 404
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": playlist.id,
                    "name": playlist.name,
                    "description": playlist.description,
                    "enabled": playlist.enabled,
                    "items": [
                        {
                            "instance_id": item.instance_id,
                            "duration_seconds": item.duration_seconds,
                            "order": item.order,
                        }
                        for item in playlist.items
                    ],
                    "created_at": playlist.created_at.isoformat(),
                    "updated_at": playlist.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/playlists/<playlist_id>", methods=["DELETE"])
def api_playlist_delete(playlist_id):
    """Delete a playlist."""
    try:
        playlist_manager = get_app().playlist_manager
        success = playlist_manager.delete_playlist(playlist_id)

        if not success:
            return jsonify({"success": False, "error": "Failed to delete playlist"}), 400

        return jsonify({"success": True, "message": "Playlist deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/playlists/<playlist_id>/activate", methods=["POST"])
def api_playlist_activate(playlist_id):
    """Set a playlist as active."""
    try:
        playlist_manager = get_app().playlist_manager
        success = playlist_manager.set_active_playlist(playlist_id)

        if not success:
            return jsonify({"success": False, "error": "Failed to activate playlist"}), 400

        return jsonify({"success": True, "message": "Playlist activated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/playlists/deactivate", methods=["POST"])
def api_playlist_deactivate():
    """Deactivate the current playlist."""
    try:
        playlist_manager = get_app().playlist_manager
        success = playlist_manager.set_active_playlist(None)

        if not success:
            return jsonify({"success": False, "error": "Failed to deactivate playlist"}), 400

        return jsonify({"success": True, "message": "Playlist deactivated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Schedule Management APIs =====


@bp.route("/api/schedules", methods=["GET"])
def api_schedules_list():
    """Get list of all schedule entries."""
    try:
        schedule_manager = get_app().schedule_manager
        entries = schedule_manager.list_entries()

        entries_data = []
        for entry in entries:
            entries_data.append(
                {
                    "id": entry.id,
                    "name": entry.name,
                    "instance_id": entry.instance_id,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "days_of_week": entry.days_of_week,
                    "priority": entry.priority,
                    "enabled": entry.enabled,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                }
            )

        config = schedule_manager.get_config()

        return jsonify(
            {
                "success": True,
                "data": entries_data,
                "config": {
                    "default_instance_id": config.default_instance_id,
                    "check_interval_seconds": config.check_interval_seconds,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules", methods=["POST"])
def api_schedule_create():
    """Create a new schedule entry."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        name = data.get("name")
        instance_id = data.get("instance_id")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        days_of_week = data.get("days_of_week", [])
        priority = data.get("priority", 5)

        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400
        if not instance_id:
            return jsonify({"success": False, "error": "instance_id is required"}), 400
        if not start_time:
            return jsonify({"success": False, "error": "start_time is required"}), 400
        if not end_time:
            return jsonify({"success": False, "error": "end_time is required"}), 400

        schedule_manager = get_app().schedule_manager
        entry = schedule_manager.create_entry(
            name=name,
            instance_id=instance_id,
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week,
            priority=priority,
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": entry.id,
                    "name": entry.name,
                    "instance_id": entry.instance_id,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "days_of_week": entry.days_of_week,
                    "priority": entry.priority,
                    "enabled": entry.enabled,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/<entry_id>", methods=["GET"])
def api_schedule_details(entry_id):
    """Get details for a specific schedule entry."""
    try:
        schedule_manager = get_app().schedule_manager
        entry = schedule_manager.get_entry(entry_id)

        if entry is None:
            return jsonify({"success": False, "error": "Schedule entry not found"}), 404

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": entry.id,
                    "name": entry.name,
                    "instance_id": entry.instance_id,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "days_of_week": entry.days_of_week,
                    "priority": entry.priority,
                    "enabled": entry.enabled,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/<entry_id>", methods=["PUT"])
def api_schedule_update(entry_id):
    """Update a schedule entry."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        schedule_manager = get_app().schedule_manager
        success = schedule_manager.update_entry(
            entry_id,
            name=data.get("name"),
            instance_id=data.get("instance_id"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            days_of_week=data.get("days_of_week"),
            priority=data.get("priority"),
            enabled=data.get("enabled"),
        )

        if not success:
            return jsonify({"success": False, "error": "Failed to update schedule entry"}), 400

        entry = schedule_manager.get_entry(entry_id)
        if entry is None:
            return jsonify({"success": False, "error": "Schedule entry not found"}), 404
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": entry.id,
                    "name": entry.name,
                    "instance_id": entry.instance_id,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "days_of_week": entry.days_of_week,
                    "priority": entry.priority,
                    "enabled": entry.enabled,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/<entry_id>", methods=["DELETE"])
def api_schedule_delete(entry_id):
    """Delete a schedule entry."""
    try:
        schedule_manager = get_app().schedule_manager
        success = schedule_manager.delete_entry(entry_id)

        if not success:
            return jsonify({"success": False, "error": "Failed to delete schedule entry"}), 400

        return jsonify({"success": True, "message": "Schedule entry deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/config", methods=["PUT"])
def api_schedule_config_update():
    """Update schedule configuration (e.g., default instance)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        schedule_manager = get_app().schedule_manager

        if "default_instance_id" in data:
            schedule_manager.set_default_instance(data["default_instance_id"])

        return jsonify({"success": True, "message": "Schedule configuration updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/current", methods=["GET"])
def api_schedule_current():
    """Get information about what's currently scheduled."""
    try:
        schedule_executor = get_app().schedule_executor
        info = schedule_executor.get_current_schedule_info()

        return jsonify({"success": True, "data": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/timeline", methods=["GET"])
def api_schedule_timeline():
    """
    Get timeline view of schedule for visualization.

    Query params:
    - day: Day of week (0=Monday, 6=Sunday). Defaults to today.
    """
    try:
        from datetime import datetime

        schedule_manager = get_app().schedule_manager
        instance_manager = get_app().instance_manager

        # Get day parameter (defaults to today)
        day_param = request.args.get("day")
        if day_param is not None:
            day = int(day_param)
        else:
            day = datetime.now().weekday()

        # Get all entries for this day
        entries = schedule_manager.list_entries()
        day_entries = [e for e in entries if e.enabled and day in e.days_of_week]

        # Sort by start time
        day_entries.sort(key=lambda e: e.start_time)

        # Build timeline data
        timeline = []
        for entry in day_entries:
            instance = instance_manager.get_instance(entry.instance_id)
            timeline.append(
                {
                    "entry_id": entry.id,
                    "entry_name": entry.name,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "priority": entry.priority,
                    "instance_id": entry.instance_id,
                    "instance_name": instance.name if instance else "Unknown",
                    "plugin_id": instance.plugin_id if instance else "Unknown",
                }
            )

        # Get default instance info
        default_id = schedule_manager.get_default_instance_id()
        default_info = None
        if default_id:
            default_instance = instance_manager.get_instance(default_id)
            if default_instance:
                default_info = {
                    "instance_id": default_id,
                    "instance_name": default_instance.name,
                    "plugin_id": default_instance.plugin_id,
                }

        return jsonify(
            {
                "success": True,
                "data": {
                    "day": day,
                    "entries": timeline,
                    "default": default_info,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

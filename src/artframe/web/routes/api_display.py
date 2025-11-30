"""
Display API routes for Artframe dashboard.

Includes current display info, preview, history, and health APIs.
"""

from pathlib import Path

from flask import jsonify, send_file

from . import bp, get_app


@bp.route("/api/display/current")
def api_display_current():
    """Get current display information."""
    controller = get_app().controller

    try:
        state = controller.display_controller.get_state()
        driver = controller.display_controller.driver

        # Get plugin info and check if preview is available
        plugin_info = driver.get_last_plugin_info()
        preview_path = driver.get_current_image_path()

        return jsonify(
            {
                "success": True,
                "data": {
                    "image_id": state.current_image_id,
                    "last_update": state.last_refresh.isoformat() if state.last_refresh else None,
                    "plugin_name": plugin_info.get("plugin_name", "Unknown"),
                    "instance_name": plugin_info.get("instance_name", "Unknown"),
                    "status": state.status,
                    "has_preview": preview_path is not None,
                    "display_count": driver.get_display_count(),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/display/preview")
def api_display_preview():
    """Serve the current display preview image (if available)."""
    controller = get_app().controller

    try:
        driver = controller.display_controller.driver

        # Get current image path from driver (any driver can provide this)
        image_path = driver.get_current_image_path()

        if image_path is not None:
            # Ensure path is absolute
            if isinstance(image_path, str):
                image_path = Path(image_path)

            if not image_path.is_absolute():
                # Resolve relative to project root
                project_root = Path(__file__).parent.parent.parent.parent
                image_path = (project_root / image_path).resolve()

            if image_path.exists():
                return send_file(str(image_path), mimetype="image/png")

        # No preview available from this driver
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

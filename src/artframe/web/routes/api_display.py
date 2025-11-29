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

        # Check if using mock driver
        has_preview = hasattr(driver, "get_current_image_path")
        plugin_info = (
            driver.get_last_plugin_info() if hasattr(driver, "get_last_plugin_info") else {}
        )

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
                    "display_count": (
                        driver.get_display_count() if hasattr(driver, "get_display_count") else 0
                    ),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/display/preview")
def api_display_preview():
    """Serve the current display preview image (mock driver only)."""
    controller = get_app().controller

    try:
        driver = controller.display_controller.driver

        # Check if mock driver
        if hasattr(driver, "get_current_image_path"):
            # Get output dir and ensure it's an absolute path (MockDriver only)
            output_dir = getattr(driver, "output_dir", None)
            if output_dir is None:
                return jsonify({"success": False, "error": "No output dir configured"}), 404

            if isinstance(output_dir, str):
                output_dir = Path(output_dir)

            # Make absolute if relative
            if not output_dir.is_absolute():
                # Resolve relative to project root (where config file is)
                project_root = Path(__file__).parent.parent.parent.parent
                output_dir = (project_root / output_dir).resolve()

            latest_path = output_dir / "latest.png"

            if latest_path.exists():
                return send_file(str(latest_path), mimetype="image/png")

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

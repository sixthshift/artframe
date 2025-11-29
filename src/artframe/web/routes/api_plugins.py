"""
Plugin and instance management API routes for Artframe dashboard.

Includes plugin listing, details, and instance CRUD operations.
"""

from flask import jsonify, request

from . import bp, get_app


# ===== Plugin Management APIs =====


@bp.route("/api/plugins")
def api_plugins_list():
    """Get list of all available plugins."""
    try:
        from ...plugins.plugin_registry import list_plugin_metadata

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
        from ...plugins.plugin_registry import get_plugin_metadata

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
        from ...plugins.plugin_registry import get_plugin

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

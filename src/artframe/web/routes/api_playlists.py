"""
Playlist management API routes for Artframe dashboard.

Includes playlist CRUD operations and activation.
"""

from typing import List, Optional

from flask import jsonify, request

from ...models import PlaylistItem
from . import bp, get_app


def _serialize_playlist_item(item):
    """Serialize a playlist item to a dictionary."""
    return {
        "instance_id": item.instance_id,
        "duration_seconds": item.duration_seconds,
        "order": item.order,
        "conditions": item.conditions,
        "weight": item.weight,
    }


def _serialize_playlist(playlist):
    """Serialize a playlist to a dictionary."""
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "enabled": playlist.enabled,
        "playback_mode": playlist.playback_mode,
        "items": [_serialize_playlist_item(item) for item in playlist.items],
        "created_at": playlist.created_at.isoformat(),
        "updated_at": playlist.updated_at.isoformat(),
    }


@bp.route("/api/playlists", methods=["GET"])
def api_playlists_list():
    """Get list of all playlists."""
    try:
        playlist_manager = get_app().playlist_manager
        playlists = playlist_manager.list_playlists()

        playlists_data = [_serialize_playlist(playlist) for playlist in playlists]
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
        playback_mode = data.get("playback_mode", "sequential")

        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400

        # Parse items
        items: List[PlaylistItem] = []
        for item_data in items_data:
            items.append(
                PlaylistItem(
                    instance_id=item_data["instance_id"],
                    duration_seconds=item_data["duration_seconds"],
                    order=item_data.get("order", len(items)),
                    conditions=item_data.get("conditions"),
                    weight=item_data.get("weight", 1),
                )
            )

        playlist_manager = get_app().playlist_manager
        playlist = playlist_manager.create_playlist(
            name, description, items, playback_mode=playback_mode
        )

        return jsonify({"success": True, "data": _serialize_playlist(playlist)})
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

        return jsonify({"success": True, "data": _serialize_playlist(playlist)})
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
        playback_mode = data.get("playback_mode")
        items_data = data.get("items")

        # Parse items if provided
        items: Optional[List[PlaylistItem]] = None
        if items_data is not None:
            items = []
            for item_data in items_data:
                items.append(
                    PlaylistItem(
                        instance_id=item_data["instance_id"],
                        duration_seconds=item_data["duration_seconds"],
                        order=item_data.get("order", len(items)),
                        conditions=item_data.get("conditions"),
                        weight=item_data.get("weight", 1),
                    )
                )

        playlist_manager = get_app().playlist_manager
        success = playlist_manager.update_playlist(
            playlist_id,
            name=name,
            description=description,
            items=items,
            enabled=enabled,
            playback_mode=playback_mode,
        )

        if not success:
            return jsonify({"success": False, "error": "Failed to update playlist"}), 400

        playlist = playlist_manager.get_playlist(playlist_id)
        if playlist is None:
            return jsonify({"success": False, "error": "Playlist not found"}), 404

        return jsonify({"success": True, "data": _serialize_playlist(playlist)})
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

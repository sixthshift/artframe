"""
Schedule management API routes for Artframe dashboard.

Includes slot-based schedule CRUD operations.
"""

from datetime import datetime

from flask import jsonify, request

from . import bp, get_app


def _serialize_slot(slot, instance_manager, playlist_manager):
    """Serialize a time slot with target info."""
    target_name = "Unknown"
    target_details = {}

    if slot.target_type == "playlist":
        playlist = playlist_manager.get_playlist(slot.target_id)
        if playlist:
            target_name = playlist.name
            target_details = {
                "item_count": len(playlist.items),
                "playback_mode": playlist.playback_mode,
            }
    else:
        instance = instance_manager.get_instance(slot.target_id)
        if instance:
            target_name = instance.name
            target_details = {"plugin_id": instance.plugin_id}

    return {
        "day": slot.day,
        "hour": slot.hour,
        "key": slot.key,
        "target_type": slot.target_type,
        "target_id": slot.target_id,
        "target_name": target_name,
        "target_details": target_details,
    }


@bp.route("/api/schedules", methods=["GET"])
def api_schedules_list():
    """Get all schedule slots."""
    try:
        schedule_manager = get_app().schedule_manager
        instance_manager = get_app().instance_manager
        playlist_manager = get_app().playlist_manager

        # Get all slots as a dict for easy lookup
        slots_dict = schedule_manager.get_slots_dict()

        return jsonify(
            {
                "success": True,
                "slots": slots_dict,
                "slot_count": schedule_manager.get_slot_count(),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/slot", methods=["POST"])
def api_schedule_set_slot():
    """Set a single time slot."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        day = data.get("day")
        hour = data.get("hour")
        target_type = data.get("target_type", "instance")
        target_id = data.get("target_id")

        if day is None:
            return jsonify({"success": False, "error": "day is required"}), 400
        if hour is None:
            return jsonify({"success": False, "error": "hour is required"}), 400
        if not target_id:
            return jsonify({"success": False, "error": "target_id is required"}), 400

        schedule_manager = get_app().schedule_manager
        slot = schedule_manager.set_slot(day, hour, target_type, target_id)

        return jsonify(
            {
                "success": True,
                "slot": {
                    "day": slot.day,
                    "hour": slot.hour,
                    "key": slot.key,
                    "target_type": slot.target_type,
                    "target_id": slot.target_id,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/slot", methods=["DELETE"])
def api_schedule_clear_slot():
    """Clear a single time slot."""
    try:
        # Accept both query params and JSON body
        data = request.get_json(silent=True) or {}
        day = data.get("day") if data else request.args.get("day", type=int)
        hour = data.get("hour") if data else request.args.get("hour", type=int)

        if day is None:
            return jsonify({"success": False, "error": "day is required"}), 400
        if hour is None:
            return jsonify({"success": False, "error": "hour is required"}), 400

        schedule_manager = get_app().schedule_manager
        cleared = schedule_manager.clear_slot(int(day), int(hour))

        return jsonify({"success": True, "cleared": cleared})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/slots/bulk", methods=["POST"])
def api_schedule_bulk_set():
    """Set multiple slots at once."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        slots = data.get("slots", [])
        if not slots:
            return jsonify({"success": False, "error": "slots array is required"}), 400

        schedule_manager = get_app().schedule_manager
        count = schedule_manager.bulk_set_slots(slots)

        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/current", methods=["GET"])
def api_schedule_current():
    """Get what's currently scheduled for right now."""
    try:
        schedule_manager = get_app().schedule_manager
        instance_manager = get_app().instance_manager
        playlist_manager = get_app().playlist_manager

        now = datetime.now()
        slot = schedule_manager.get_current_slot(now)

        if slot:
            if slot.target_type == "playlist":
                playlist = playlist_manager.get_playlist(slot.target_id)
                return jsonify(
                    {
                        "success": True,
                        "data": {
                            "has_content": True,
                            "source_type": "schedule",
                            "target_type": "playlist",
                            "target_id": slot.target_id,
                            "target_name": playlist.name if playlist else "Unknown",
                            "day": slot.day,
                            "hour": slot.hour,
                        },
                    }
                )
            else:
                instance = instance_manager.get_instance(slot.target_id)
                return jsonify(
                    {
                        "success": True,
                        "data": {
                            "has_content": True,
                            "source_type": "schedule",
                            "target_type": "instance",
                            "target_id": slot.target_id,
                            "target_name": instance.name if instance else "Unknown",
                            "instance": {"name": instance.name} if instance else None,
                            "day": slot.day,
                            "hour": slot.hour,
                        },
                    }
                )

        # No slot assigned for current time
        return jsonify(
            {"success": True, "data": {"has_content": False, "source_type": "none"}}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/schedules/clear", methods=["POST"])
def api_schedule_clear_all():
    """Clear all schedule slots."""
    try:
        schedule_manager = get_app().schedule_manager
        count = schedule_manager.clear_all_slots()

        return jsonify({"success": True, "cleared": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

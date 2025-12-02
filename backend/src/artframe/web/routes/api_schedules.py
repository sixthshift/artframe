"""
Schedule management API routes for Artframe dashboard.

Includes slot-based schedule CRUD operations.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..schemas import (
    APIResponse,
    APIResponseWithData,
    BulkSlotSetRequest,
    ScheduleCurrentResponse,
    ScheduleSlotsResponse,
    SlotSetRequest,
    SlotSetResponse,
)
from . import get_state

router = APIRouter()


class SlotClearRequest(BaseModel):
    """Request body for clearing a slot."""

    day: Optional[int] = None
    hour: Optional[int] = None


def _serialize_slot(slot, instance_manager, playlist_manager):
    """Serialize a time slot with target info."""
    target_name = "Unknown"
    target_details: Dict[str, Any] = {}

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


@router.get("/api/schedules", response_model=APIResponseWithData)
def api_schedules_list():
    """Get all schedule slots."""
    state = get_state()

    try:
        schedule_manager = state.schedule_manager

        # Get all slots as a dict for easy lookup
        slots_dict = schedule_manager.get_slots_dict()

        return {
            "success": True,
            "data": {
                "slots": slots_dict,
                "slot_count": schedule_manager.get_slot_count(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/schedules/slot", response_model=SlotSetResponse)
def api_schedule_set_slot(request: SlotSetRequest):
    """Set a single time slot."""
    state = get_state()

    try:
        schedule_manager = state.schedule_manager
        slot = schedule_manager.set_slot(
            request.day, request.hour, request.target_type, request.target_id
        )

        return {
            "success": True,
            "slot": {
                "day": slot.day,
                "hour": slot.hour,
                "key": slot.key,
                "target_type": slot.target_type,
                "target_id": slot.target_id,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/schedules/slot", response_model=APIResponseWithData)
def api_schedule_clear_slot(
    day: Optional[int] = Query(None),
    hour: Optional[int] = Query(None),
    request: Optional[SlotClearRequest] = None,
):
    """Clear a single time slot."""
    state = get_state()

    try:
        # Accept both query params and JSON body
        actual_day = day
        actual_hour = hour

        if request:
            if request.day is not None:
                actual_day = request.day
            if request.hour is not None:
                actual_hour = request.hour

        if actual_day is None:
            raise HTTPException(status_code=400, detail="day is required")
        if actual_hour is None:
            raise HTTPException(status_code=400, detail="hour is required")

        schedule_manager = state.schedule_manager
        cleared = schedule_manager.clear_slot(int(actual_day), int(actual_hour))

        return {"success": True, "data": {"cleared": cleared}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/schedules/slots/bulk", response_model=APIResponseWithData)
def api_schedule_bulk_set(request: BulkSlotSetRequest):
    """Set multiple slots at once."""
    state = get_state()

    try:
        schedule_manager = state.schedule_manager
        slots_data = [
            {
                "day": s.day,
                "hour": s.hour,
                "target_type": s.target_type,
                "target_id": s.target_id,
            }
            for s in request.slots
        ]
        count = schedule_manager.bulk_set_slots(slots_data)

        return {"success": True, "data": {"count": count}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/schedules/current", response_model=ScheduleCurrentResponse)
def api_schedule_current():
    """Get what's currently scheduled for right now."""
    state = get_state()

    try:
        schedule_manager = state.schedule_manager
        instance_manager = state.instance_manager
        playlist_manager = state.playlist_manager

        now = datetime.now()
        slot = schedule_manager.get_current_slot(now)

        if slot:
            if slot.target_type == "playlist":
                playlist = playlist_manager.get_playlist(slot.target_id)
                return {
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
            else:
                instance = instance_manager.get_instance(slot.target_id)
                return {
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

        # No slot assigned for current time
        return {"success": True, "data": {"has_content": False, "source_type": "none"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/schedules/clear", response_model=APIResponseWithData)
def api_schedule_clear_all():
    """Clear all schedule slots."""
    state = get_state()

    try:
        schedule_manager = state.schedule_manager
        count = schedule_manager.clear_all_slots()

        return {"success": True, "data": {"cleared": count}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

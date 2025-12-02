"""
Playlist management API routes for Artframe dashboard.

Includes playlist CRUD operations and activation.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ...models import PlaylistItem
from ..schemas import (
    APIResponse,
    PlaylistCreateRequest,
    PlaylistResponse,
    PlaylistsListResponse,
    PlaylistUpdateRequest,
)
from . import get_state

router = APIRouter()


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


@router.get("/api/playlists", response_model=PlaylistsListResponse)
def api_playlists_list():
    """Get list of all playlists."""
    state = get_state()

    try:
        playlist_manager = state.playlist_manager
        playlists = playlist_manager.list_playlists()

        playlists_data = [_serialize_playlist(playlist) for playlist in playlists]
        active_playlist_id = playlist_manager.get_active_playlist_id()

        return {
            "success": True,
            "data": playlists_data,
            "active_playlist_id": active_playlist_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/playlists", response_model=PlaylistResponse)
def api_playlist_create(request: PlaylistCreateRequest):
    """Create a new playlist."""
    state = get_state()

    try:
        # Parse items
        items: List[PlaylistItem] = []
        for item_data in request.items:
            items.append(
                PlaylistItem(
                    instance_id=item_data.instance_id,
                    duration_seconds=item_data.duration_seconds,
                    order=item_data.order,
                    conditions=item_data.conditions,
                    weight=item_data.weight,
                )
            )

        playlist_manager = state.playlist_manager
        playlist = playlist_manager.create_playlist(
            request.name, request.description, items, playback_mode=request.playback_mode
        )

        return {"success": True, "data": _serialize_playlist(playlist)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/playlists/{playlist_id}", response_model=PlaylistResponse)
def api_playlist_details(playlist_id: str):
    """Get details for a specific playlist."""
    state = get_state()

    try:
        playlist_manager = state.playlist_manager
        playlist = playlist_manager.get_playlist(playlist_id)

        if playlist is None:
            raise HTTPException(status_code=404, detail="Playlist not found")

        return {"success": True, "data": _serialize_playlist(playlist)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/playlists/{playlist_id}", response_model=PlaylistResponse)
def api_playlist_update(playlist_id: str, request: PlaylistUpdateRequest):
    """Update a playlist."""
    state = get_state()

    try:
        # Parse items if provided
        items: Optional[List[PlaylistItem]] = None
        if request.items is not None:
            items = []
            for item_data in request.items:
                items.append(
                    PlaylistItem(
                        instance_id=item_data.instance_id,
                        duration_seconds=item_data.duration_seconds,
                        order=item_data.order,
                        conditions=item_data.conditions,
                        weight=item_data.weight,
                    )
                )

        playlist_manager = state.playlist_manager
        success = playlist_manager.update_playlist(
            playlist_id,
            name=request.name,
            description=request.description,
            items=items,
            enabled=request.enabled,
            playback_mode=request.playback_mode,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update playlist")

        playlist = playlist_manager.get_playlist(playlist_id)
        if playlist is None:
            raise HTTPException(status_code=404, detail="Playlist not found")

        return {"success": True, "data": _serialize_playlist(playlist)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/playlists/{playlist_id}", response_model=APIResponse)
def api_playlist_delete(playlist_id: str):
    """Delete a playlist."""
    state = get_state()

    try:
        playlist_manager = state.playlist_manager
        success = playlist_manager.delete_playlist(playlist_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete playlist")

        return {"success": True, "message": "Playlist deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/playlists/{playlist_id}/activate", response_model=APIResponse)
def api_playlist_activate(playlist_id: str):
    """Set a playlist as active."""
    state = get_state()

    try:
        playlist_manager = state.playlist_manager
        success = playlist_manager.set_active_playlist(playlist_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate playlist")

        return {"success": True, "message": "Playlist activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/playlists/deactivate", response_model=APIResponse)
def api_playlist_deactivate():
    """Deactivate the current playlist."""
    state = get_state()

    try:
        playlist_manager = state.playlist_manager
        success = playlist_manager.set_active_playlist(None)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to deactivate playlist")

        return {"success": True, "message": "Playlist deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

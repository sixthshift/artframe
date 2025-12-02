"""
Playlist management API routes for Artframe dashboard.

Provides endpoints for playlist CRUD operations and activation.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ...models import PlaylistItem
from ..dependencies import get_playlist_manager
from ..schemas import (
    APIResponse,
    PlaylistCreateRequest,
    PlaylistResponse,
    PlaylistsListResponse,
    PlaylistUpdateRequest,
)

router = APIRouter(prefix="/api/playlists", tags=["Playlists"])


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


@router.get("", response_model=PlaylistsListResponse)
def list_playlists(playlist_manager=Depends(get_playlist_manager)):
    """Get list of all playlists."""
    try:
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


@router.post("", response_model=PlaylistResponse)
def create_playlist(request: PlaylistCreateRequest, playlist_manager=Depends(get_playlist_manager)):
    """Create a new playlist."""
    try:
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

        playlist = playlist_manager.create_playlist(
            request.name, request.description, items, playback_mode=request.playback_mode
        )

        return {"success": True, "data": _serialize_playlist(playlist)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{playlist_id}", response_model=PlaylistResponse)
def get_playlist(playlist_id: str, playlist_manager=Depends(get_playlist_manager)):
    """Get details for a specific playlist."""
    try:
        playlist = playlist_manager.get_playlist(playlist_id)

        if playlist is None:
            raise HTTPException(status_code=404, detail="Playlist not found")

        return {"success": True, "data": _serialize_playlist(playlist)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: str,
    request: PlaylistUpdateRequest,
    playlist_manager=Depends(get_playlist_manager),
):
    """Update a playlist."""
    try:
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


@router.delete("/{playlist_id}", response_model=APIResponse)
def delete_playlist(playlist_id: str, playlist_manager=Depends(get_playlist_manager)):
    """Delete a playlist."""
    try:
        success = playlist_manager.delete_playlist(playlist_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete playlist")

        return {"success": True, "message": "Playlist deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playlist_id}/activate", response_model=APIResponse)
def activate_playlist(playlist_id: str, playlist_manager=Depends(get_playlist_manager)):
    """Set a playlist as active."""
    try:
        success = playlist_manager.set_active_playlist(playlist_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate playlist")

        return {"success": True, "message": "Playlist activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deactivate", response_model=APIResponse)
def deactivate_playlist(playlist_manager=Depends(get_playlist_manager)):
    """Deactivate the current playlist."""
    try:
        success = playlist_manager.set_active_playlist(None)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to deactivate playlist")

        return {"success": True, "message": "Playlist deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

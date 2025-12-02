"""
Display API routes for Artframe dashboard.

Includes current display info, preview, history, and health APIs.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..schemas import APIResponseWithData, DisplayCurrentResponse, DisplayHealthResponse
from . import get_state

router = APIRouter()


@router.get("/api/display/current", response_model=DisplayCurrentResponse)
def api_display_current():
    """Get current display information."""
    state = get_state()
    controller = state.controller

    try:
        display_state = controller.display_controller.get_state()
        driver = controller.display_controller.driver

        # Get plugin info and check if preview is available
        plugin_info = driver.get_last_plugin_info()
        preview_path = driver.get_current_image_path()

        return {
            "success": True,
            "data": {
                "image_id": display_state.current_image_id,
                "last_update": display_state.last_refresh.isoformat() if display_state.last_refresh else None,
                "plugin_name": plugin_info.get("plugin_name", "Unknown"),
                "instance_name": plugin_info.get("instance_name", "Unknown"),
                "status": display_state.status,
                "has_preview": preview_path is not None,
                "display_count": driver.get_display_count(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/display/preview")
def api_display_preview():
    """Serve the current display preview image (if available)."""
    state = get_state()
    controller = state.controller

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
                return FileResponse(str(image_path), media_type="image/png")

        # No preview available from this driver
        raise HTTPException(status_code=404, detail="No preview available")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/api/display/history", response_model=APIResponseWithData)
def api_display_history():
    """Get display history."""
    try:
        # TODO: Implement history tracking
        return {"success": True, "data": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/display/health", response_model=DisplayHealthResponse)
def api_display_health():
    """Get e-ink display health metrics."""
    state = get_state()
    controller = state.controller

    try:
        display_state = controller.display_controller.get_state()
        return {
            "success": True,
            "data": {
                "refresh_count": 0,  # TODO: Track refresh count
                "last_refresh": display_state.last_refresh.isoformat() if display_state.last_refresh else None,
                "status": display_state.status,
                "error_count": display_state.error_count,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

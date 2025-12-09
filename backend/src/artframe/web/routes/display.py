"""
Display API routes for Artframe dashboard.

Provides endpoints for display info, preview, control, and health at /api/display/*.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..dependencies import get_controller
from ..schemas import (
    APIResponse,
    APIResponseWithData,
    DisplayCurrentResponse,
    DisplayHealthResponse,
)

router = APIRouter(prefix="/api/display", tags=["Display"])


@router.get("/current", response_model=DisplayCurrentResponse)
def get_current(controller=Depends(get_controller)):
    """Get current display information."""
    try:
        display_state = controller.display_controller.get_state()
        driver = controller.display_controller.driver

        plugin_info = driver.get_last_plugin_info()
        preview_path = driver.get_current_image_path()

        return {
            "success": True,
            "data": {
                "image_id": display_state.current_image_id,
                "last_update": display_state.last_refresh.isoformat()
                if display_state.last_refresh
                else None,
                "plugin_name": plugin_info.get("plugin_name", "Unknown"),
                "instance_name": plugin_info.get("instance_name", "Unknown"),
                "has_preview": preview_path is not None,
                "display_count": driver.get_display_count(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/preview")
def get_preview(controller=Depends(get_controller)):
    """Serve the current display preview image."""
    try:
        driver = controller.display_controller.driver
        image_path = driver.get_current_image_path()

        if image_path is not None:
            if isinstance(image_path, str):
                image_path = Path(image_path)

            if not image_path.is_absolute():
                # Resolve relative to backend/ directory (5 levels up from routes/display.py)
                project_root = Path(__file__).parent.parent.parent.parent.parent
                image_path = (project_root / image_path).resolve()

            if image_path.exists():
                return FileResponse(str(image_path), media_type="image/png")

        raise HTTPException(status_code=404, detail="No preview available")

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.get("/history", response_model=APIResponseWithData)
def get_history():
    """Get display history."""
    # TODO: Implement history tracking
    return {"success": True, "data": []}


@router.get("/health", response_model=DisplayHealthResponse)
def get_health(controller=Depends(get_controller)):
    """Get e-ink display health metrics."""
    try:
        display_state = controller.display_controller.get_state()
        return {
            "success": True,
            "data": {
                "refresh_count": 0,  # TODO: Track refresh count
                "last_refresh": display_state.last_refresh.isoformat()
                if display_state.last_refresh
                else None,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/refresh", response_model=APIResponse)
def trigger_refresh(controller=Depends(get_controller)):
    """Trigger immediate display refresh."""
    try:
        success = controller.manual_refresh()
        return {
            "success": success,
            "message": "Refresh completed successfully" if success else "Refresh failed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/clear", response_model=APIResponse)
def clear_display(controller=Depends(get_controller)):
    """Clear the display."""
    try:
        controller.display_controller.clear_display()
        return {"success": True, "message": "Display cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/hardware-test", response_model=APIResponseWithData)
def run_hardware_test(controller=Depends(get_controller)):
    """Run hardware test pattern to verify display connectivity.

    Displays a test pattern with colors, shapes, and text to prove
    the Raspberry Pi can communicate with the e-ink display.
    """
    try:
        driver = controller.display_controller.driver
        result = driver.run_hardware_test()
        return {
            "success": result.get("success", False),
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

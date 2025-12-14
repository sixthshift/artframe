"""
Display API routes for Artframe dashboard.

Provides endpoints for display info, preview, control, and health at /api/display/*.
"""

import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image

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

        # Check for manual override status
        is_manual_override = controller.orchestrator.has_manual_override()

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
                "manual_override_active": is_manual_override,
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


@router.post("/upload", response_model=APIResponse)
async def upload_manual_image(
    file: UploadFile = File(...),
    controller=Depends(get_controller),
):
    """
    Upload and display a manual image immediately.

    The image will be displayed until the current plugin's next scheduled refresh,
    at which point normal plugin-based updates resume.

    Accepts: image/jpeg, image/png, image/gif, image/webp
    """
    try:
        # Validate content type
        valid_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {file.content_type}. Must be one of: {valid_types}",
            )

        # Read and open image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Get display dimensions and resize/fit image
        display_size = controller.display_controller.get_display_size()
        image = _fit_image_to_display(image, display_size)

        # Display via orchestrator (sets override flag)
        success = controller.orchestrator.display_manual_image(image)

        if success:
            return {
                "success": True,
                "message": "Image uploaded and displayed. Will revert on next plugin refresh.",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to display image")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/clear-override", response_model=APIResponse)
def clear_manual_override(controller=Depends(get_controller)):
    """
    Clear any manual image override and resume normal plugin updates.

    If no override is active, this is a no-op.
    """
    try:
        was_active = controller.orchestrator.has_manual_override()
        controller.orchestrator.clear_manual_override()

        if was_active:
            return {"success": True, "message": "Manual override cleared"}
        else:
            return {"success": True, "message": "No override was active"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _fit_image_to_display(
    image: Image.Image, display_size: tuple[int, int]
) -> Image.Image:
    """
    Resize and fit image to display dimensions (contain mode).

    Args:
        image: Input PIL Image
        display_size: (width, height) of display

    Returns:
        PIL Image fitted to display size with letterboxing if needed
    """
    display_width, display_height = display_size

    # Calculate aspect ratios
    image_aspect = image.width / image.height
    display_aspect = display_width / display_height

    # Fit image (contain mode)
    if image_aspect > display_aspect:
        new_width = display_width
        new_height = int(display_width / image_aspect)
    else:
        new_height = display_height
        new_width = int(display_height * image_aspect)

    # Resize
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create canvas and center
    canvas = Image.new("RGB", (display_width, display_height), "white")
    x = (display_width - new_width) // 2
    y = (display_height - new_height) // 2
    canvas.paste(resized, (x, y))

    return canvas

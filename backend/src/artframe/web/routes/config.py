"""
Configuration API routes for Artframe dashboard.

Provides endpoints for configuration management at /api/config/*.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_controller
from ..schemas import APIResponse, APIResponseWithData

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("", response_model=APIResponseWithData)
def get_config(controller=Depends(get_controller)):
    """Get current configuration."""
    try:
        config = controller.config_manager.config
        return {"success": True, "data": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("", response_model=APIResponse)
def update_config(new_config: dict[str, Any], controller=Depends(get_controller)):
    """Update in-memory configuration (validation only, not saved)."""
    try:
        if not new_config:
            raise HTTPException(status_code=400, detail="No configuration data provided")

        controller.config_manager.update_config(new_config)

        return {
            "success": True,
            "message": "Configuration updated in memory (not saved to file yet)",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/save", response_model=APIResponseWithData)
def save_config(controller=Depends(get_controller)):
    """Save current in-memory configuration to YAML file."""
    try:
        controller.config_manager.save_to_file(backup=True)
        return {
            "success": True,
            "message": "Configuration saved to file. Restart required for changes to take effect.",
            "data": {"restart_required": True},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {e}") from e


@router.post("/revert", response_model=APIResponse)
def revert_config(controller=Depends(get_controller)):
    """Revert in-memory config to what's on disk."""
    try:
        controller.config_manager.revert_to_file()
        return {"success": True, "message": "Configuration reverted to saved version"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

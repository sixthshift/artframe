"""
Core API routes for Artframe dashboard.

Provides endpoints for status, config, connections, update, clear, restart, and scheduler.
These are the main control endpoints at /api/* level.
"""

import os
import signal
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_controller
from ..schemas import (
    APIResponse,
    APIResponseWithData,
    SchedulerStatusResponse,
)

router = APIRouter(prefix="/api", tags=["Core"])


# ===== Status & Connections =====


@router.get("/status", response_model=APIResponseWithData)
def get_status(controller=Depends(get_controller)):
    """Get current system status."""
    try:
        status = controller.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=APIResponseWithData)
def test_connections(controller=Depends(get_controller)):
    """Test all external connections."""
    try:
        connections = controller.test_connections()
        return {"success": True, "data": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Display Control =====


@router.post("/update", response_model=APIResponse)
def trigger_update(controller=Depends(get_controller)):
    """Trigger immediate photo update."""
    try:
        success = controller.manual_refresh()
        return {
            "success": success,
            "message": "Update completed successfully" if success else "Update failed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=APIResponse)
def clear_display(controller=Depends(get_controller)):
    """Clear the display."""
    try:
        controller.display_controller.clear_display()
        return {"success": True, "message": "Display cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Configuration =====


@router.get("/config", response_model=APIResponseWithData)
def get_config(controller=Depends(get_controller)):
    """Get current configuration."""
    try:
        config = controller.config_manager.config
        return {"success": True, "data": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=APIResponse)
def update_config(new_config: Dict[str, Any], controller=Depends(get_controller)):
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
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/save", response_model=APIResponseWithData)
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
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {e}")


@router.post("/config/revert", response_model=APIResponse)
def revert_config(controller=Depends(get_controller)):
    """Revert in-memory config to what's on disk."""
    try:
        controller.config_manager.revert_to_file()
        return {"success": True, "message": "Configuration reverted to saved version"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Restart =====


@router.post("/restart", response_model=APIResponse)
def restart():
    """Restart the application."""
    try:
        os.kill(os.getpid(), signal.SIGTERM)
        return {"success": True, "message": "Restart initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Scheduler Control =====


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(controller=Depends(get_controller)):
    """Get scheduler status."""
    try:
        status = controller.scheduler.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/pause", response_model=SchedulerStatusResponse)
def pause_scheduler(controller=Depends(get_controller)):
    """Pause automatic updates (daily e-ink refresh still occurs)."""
    try:
        controller.scheduler.pause()
        return {
            "success": True,
            "message": "Scheduler paused. Daily e-ink refresh will still occur for screen health.",
            "status": controller.scheduler.get_status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/resume", response_model=SchedulerStatusResponse)
def resume_scheduler(controller=Depends(get_controller)):
    """Resume automatic updates."""
    try:
        controller.scheduler.resume()
        return {
            "success": True,
            "message": "Scheduler resumed",
            "status": controller.scheduler.get_status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

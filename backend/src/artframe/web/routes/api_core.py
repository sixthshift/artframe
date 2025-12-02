"""
Core API routes for Artframe dashboard.

Includes status, config, update, clear, restart, and scheduler APIs.
"""

import os
import signal
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..schemas import APIResponse, APIResponseWithData, SchedulerStatusResponse
from . import get_state

router = APIRouter()


@router.get("/api/status", response_model=APIResponseWithData)
def api_status():
    """Get current system status as JSON."""
    state = get_state()
    controller = state.controller

    try:
        status = controller.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/config", response_model=APIResponseWithData)
def api_config():
    """Get current configuration as JSON."""
    state = get_state()
    controller = state.controller

    try:
        config = controller.config_manager.config
        return {"success": True, "data": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/connections", response_model=APIResponseWithData)
def api_connections():
    """Test all external connections."""
    state = get_state()
    controller = state.controller

    try:
        connections = controller.test_connections()
        # Returns dict like {"display": true, "storage": true}
        return {"success": True, "data": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/update", response_model=APIResponse)
def api_trigger_update():
    """Trigger immediate photo update."""
    state = get_state()
    controller = state.controller

    try:
        success = controller.manual_refresh()
        return {
            "success": success,
            "message": "Update completed successfully" if success else "Update failed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/clear", response_model=APIResponse)
def api_clear_display():
    """Clear the display."""
    state = get_state()
    controller = state.controller

    try:
        controller.display_controller.clear_display()
        return {"success": True, "message": "Display cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/config", response_model=APIResponse)
def api_update_config(new_config: Dict[str, Any]):
    """Update in-memory configuration (validation only, not saved)."""
    state = get_state()
    controller = state.controller

    try:
        if not new_config:
            raise HTTPException(status_code=400, detail="No configuration data provided")

        # Validate and update in-memory config
        controller.config_manager.update_config(new_config)

        return {
            "success": True,
            "message": "Configuration updated in memory (not saved to file yet)",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/save", response_model=APIResponseWithData)
def api_save_config():
    """Save current in-memory configuration to YAML file."""
    state = get_state()
    controller = state.controller

    try:
        controller.config_manager.save_to_file(backup=True)
        return {
            "success": True,
            "message": "Configuration saved to file. Restart required for changes to take effect.",
            "data": {"restart_required": True},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {e}")


@router.post("/api/config/revert", response_model=APIResponse)
def api_revert_config():
    """Revert in-memory config to what's on disk."""
    state = get_state()
    controller = state.controller

    try:
        controller.config_manager.revert_to_file()
        return {"success": True, "message": "Configuration reverted to saved version"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/restart", response_model=APIResponse)
def api_restart():
    """Restart the application."""
    try:
        # Send SIGTERM to self to trigger graceful restart
        # In production, systemd will restart the service automatically
        os.kill(os.getpid(), signal.SIGTERM)

        return {"success": True, "message": "Restart initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Scheduler APIs =====


@router.get("/api/scheduler/status", response_model=SchedulerStatusResponse)
def api_scheduler_status():
    """Get scheduler status."""
    state = get_state()
    controller = state.controller

    try:
        status = controller.scheduler.get_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/scheduler/pause", response_model=SchedulerStatusResponse)
def api_scheduler_pause():
    """Pause automatic updates (daily e-ink refresh still occurs)."""
    state = get_state()
    controller = state.controller

    try:
        controller.scheduler.pause()
        return {
            "success": True,
            "message": "Scheduler paused. Daily e-ink refresh will still occur for screen health.",
            "status": controller.scheduler.get_status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/scheduler/resume", response_model=SchedulerStatusResponse)
def api_scheduler_resume():
    """Resume automatic updates."""
    state = get_state()
    controller = state.controller

    try:
        controller.scheduler.resume()
        return {
            "success": True,
            "message": "Scheduler resumed",
            "status": controller.scheduler.get_status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/source/stats", response_model=APIResponseWithData)
def api_source_stats():
    """
    Get source statistics.

    DEPRECATED: Sources are now managed as plugins.
    Use /api/plugins/instances for plugin instance information.
    """
    return {
        "success": True,
        "data": {
            "message": "Sources are now managed as plugins. Use /api/plugins/instances instead.",
            "provider": "plugin-based",
        },
    }

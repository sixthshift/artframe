"""
Scheduler API routes for Artframe dashboard.

Provides endpoints for scheduler control at /api/scheduler/*.
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_controller
from ..schemas import SchedulerStatusResponse

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])


@router.get("/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(controller=Depends(get_controller)):
    """Get scheduler status."""
    try:
        status = controller.orchestrator.get_scheduler_status()
        return {"success": True, "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/pause", response_model=SchedulerStatusResponse)
def pause_scheduler(controller=Depends(get_controller)):
    """Pause automatic updates."""
    try:
        controller.orchestrator.pause()
        return {
            "success": True,
            "message": "Scheduler paused",
            "status": controller.orchestrator.get_scheduler_status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/resume", response_model=SchedulerStatusResponse)
def resume_scheduler(controller=Depends(get_controller)):
    """Resume automatic updates."""
    try:
        controller.orchestrator.resume()
        return {
            "success": True,
            "message": "Scheduler resumed",
            "status": controller.orchestrator.get_scheduler_status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

"""
System API routes for Artframe dashboard.

Provides endpoints for system info and logs at /api/system/*.
"""

import platform
import time
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..schemas import SystemInfoResponse, SystemLogsResponse

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/info", response_model=SystemInfoResponse)
def get_info():
    """Get system information (CPU, memory, disk, temperature)."""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime_seconds = psutil.boot_time()
        uptime = str(timedelta(seconds=int(time.time() - uptime_seconds)))

        # Try to get temperature (Raspberry Pi)
        temp = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp = round(int(f.read()) / 1000, 1)
        except Exception:
            pass

        return {
            "success": True,
            "data": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "disk_percent": round(disk.percent, 1),
                "temperature": temp,
                "uptime": uptime,
                "platform": platform.system(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/logs", response_model=SystemLogsResponse)
def get_logs():
    """Get system logs."""
    try:
        # TODO: Read from actual log file
        return {
            "success": True,
            "data": [
                {
                    "timestamp": "2025-09-27 20:00:00",
                    "level": "INFO",
                    "message": "Artframe controller initialized successfully",
                },
                {
                    "timestamp": "2025-09-27 20:00:30",
                    "level": "INFO",
                    "message": "Starting Artframe scheduled loop",
                },
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/logs/export")
def export_logs():
    """Export system logs as text file."""
    try:
        # TODO: Read from actual log file
        logs_text = "Artframe System Logs\n\n"
        logs_text += "2025-09-27 20:00:00 INFO Artframe controller initialized successfully\n"

        return PlainTextResponse(
            content=logs_text,
            headers={"Content-Disposition": "attachment;filename=artframe-logs.txt"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

"""
System API routes for Artframe dashboard.

Includes system info and logs APIs.
"""

import platform
import time
from datetime import timedelta

from flask import Response, jsonify

from . import bp


@bp.route("/api/system/info")
def api_system_info():
    """Get system information."""
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
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = round(int(f.read()) / 1000, 1)
        except Exception:
            pass

        return jsonify(
            {
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
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/system/logs")
def api_system_logs():
    """Get system logs."""
    try:
        # TODO: Read from actual log file
        # For now, return placeholder
        return jsonify(
            {
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
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/system/logs/export")
def api_system_logs_export():
    """Export system logs as text file."""
    try:
        # TODO: Read from actual log file
        logs_text = "Artframe System Logs\n\n"
        logs_text += "2025-09-27 20:00:00 INFO Artframe controller initialized successfully\n"

        return Response(
            logs_text,
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment;filename=artframe-logs.txt"},
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

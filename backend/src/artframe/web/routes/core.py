"""
Core API routes for Artframe dashboard.

Provides endpoints for status, config, connections, update, clear, restart, and scheduler.
These are the main control endpoints at /api/* level.
"""

import os
import signal
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from ..dependencies import get_controller
from ..schemas import (
    APIResponse,
    APIResponseWithData,
    SchedulerStatusResponse,
)

router = APIRouter(prefix="/api", tags=["Core"])


# ===== API Index =====


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def api_index():
    """API explorer page showing all endpoints with live data."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Artframe API</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 24px; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #334155; }
        h1 { font-size: 24px; font-weight: 600; color: #f1f5f9; }
        .status-badge { display: flex; align-items: center; gap: 8px; font-size: 14px; padding: 6px 12px; border-radius: 6px; background: #1e293b; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #fbbf24; }
        .status-dot.ok { background: #22c55e; }
        .status-dot.error { background: #ef4444; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 32px; }
        .card { background: #1e293b; border-radius: 8px; border: 1px solid #334155; overflow: hidden; }
        .card-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #334155; }
        .card-title { font-size: 14px; font-weight: 500; color: #f1f5f9; }
        .card-link { font-size: 12px; color: #94a3b8; text-decoration: none; font-family: monospace; }
        .card-link:hover { color: #60a5fa; }
        pre { padding: 16px; font-size: 12px; line-height: 1.5; overflow: auto; max-height: 280px; background: #0f172a; color: #94a3b8; margin: 0; }
        pre.loading { color: #64748b; font-style: italic; }
        pre.error { color: #f87171; }
        .endpoints { background: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 20px; }
        .endpoints h2 { font-size: 16px; font-weight: 600; color: #f1f5f9; margin-bottom: 16px; }
        .endpoint-group { margin-bottom: 16px; }
        .endpoint-group:last-child { margin-bottom: 0; }
        .endpoint-group-title { font-size: 12px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
        .endpoint-list { display: flex; flex-wrap: wrap; gap: 8px; }
        .endpoint { display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 4px; text-decoration: none; font-size: 13px; font-family: monospace; background: #334155; color: #e2e8f0; transition: background 0.15s; }
        .endpoint:hover { background: #475569; }
        .method { font-size: 10px; font-weight: 600; padding: 2px 5px; border-radius: 3px; }
        .method.get { background: #3b82f6; color: white; }
        .method.post { background: #22c55e; color: white; }
        .method.put { background: #f59e0b; color: white; }
        .method.delete { background: #ef4444; color: white; }
        .docs-link { background: #7c3aed; }
        .docs-link:hover { background: #8b5cf6; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Artframe API</h1>
            <div class="status-badge">
                <span class="status-dot" id="health-dot"></span>
                <span id="health-text">Checking...</span>
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">System Status</span>
                    <a class="card-link" href="/api/status" target="_blank">/api/status</a>
                </div>
                <pre id="status" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Current Display</span>
                    <a class="card-link" href="/api/display/current" target="_blank">/api/display/current</a>
                </div>
                <pre id="display" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Scheduler</span>
                    <a class="card-link" href="/api/scheduler/status" target="_blank">/api/scheduler/status</a>
                </div>
                <pre id="scheduler" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Connections</span>
                    <a class="card-link" href="/api/connections" target="_blank">/api/connections</a>
                </div>
                <pre id="connections" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Plugins</span>
                    <a class="card-link" href="/api/plugins" target="_blank">/api/plugins</a>
                </div>
                <pre id="plugins" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Configuration</span>
                    <a class="card-link" href="/api/config" target="_blank">/api/config</a>
                </div>
                <pre id="config" class="loading">Loading...</pre>
            </div>
        </div>

        <div class="endpoints">
            <h2>All Endpoints</h2>
            <div class="endpoint-group">
                <div class="endpoint-group-title">Core</div>
                <div class="endpoint-list">
                    <a class="endpoint" href="/api/status" target="_blank"><span class="method get">GET</span>/api/status</a>
                    <a class="endpoint" href="/api/connections" target="_blank"><span class="method get">GET</span>/api/connections</a>
                    <a class="endpoint" href="/api/config" target="_blank"><span class="method get">GET</span>/api/config</a>
                    <a class="endpoint" href="/api/system/info" target="_blank"><span class="method get">GET</span>/api/system/info</a>
                </div>
            </div>
            <div class="endpoint-group">
                <div class="endpoint-group-title">Display</div>
                <div class="endpoint-list">
                    <a class="endpoint" href="/api/display/current" target="_blank"><span class="method get">GET</span>/api/display/current</a>
                    <a class="endpoint" href="/api/display/preview" target="_blank"><span class="method get">GET</span>/api/display/preview</a>
                    <a class="endpoint" href="/api/display/health" target="_blank"><span class="method get">GET</span>/api/display/health</a>
                </div>
            </div>
            <div class="endpoint-group">
                <div class="endpoint-group-title">Scheduler</div>
                <div class="endpoint-list">
                    <a class="endpoint" href="/api/scheduler/status" target="_blank"><span class="method get">GET</span>/api/scheduler/status</a>
                </div>
            </div>
            <div class="endpoint-group">
                <div class="endpoint-group-title">Content</div>
                <div class="endpoint-list">
                    <a class="endpoint" href="/api/plugins" target="_blank"><span class="method get">GET</span>/api/plugins</a>
                    <a class="endpoint" href="/api/schedules" target="_blank"><span class="method get">GET</span>/api/schedules</a>
                    <a class="endpoint" href="/api/playlists" target="_blank"><span class="method get">GET</span>/api/playlists</a>
                </div>
            </div>
            <div class="endpoint-group">
                <div class="endpoint-group-title">Documentation</div>
                <div class="endpoint-list">
                    <a class="endpoint docs-link" href="/docs" target="_blank">OpenAPI (Swagger)</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchAndDisplay(url, elementId) {
            const el = document.getElementById(elementId);
            try {
                const res = await fetch(url);
                const data = await res.json();
                el.textContent = JSON.stringify(data, null, 2);
                el.classList.remove('loading');
                return { ok: res.ok, data };
            } catch (e) {
                el.textContent = 'Error: ' + e.message;
                el.classList.remove('loading');
                el.classList.add('error');
                return { ok: false };
            }
        }

        async function init() {
            const results = await Promise.all([
                fetchAndDisplay('/api/status', 'status'),
                fetchAndDisplay('/api/display/current', 'display'),
                fetchAndDisplay('/api/scheduler/status', 'scheduler'),
                fetchAndDisplay('/api/config', 'config'),
                fetchAndDisplay('/api/connections', 'connections'),
                fetchAndDisplay('/api/plugins', 'plugins'),
            ]);

            const dot = document.getElementById('health-dot');
            const text = document.getElementById('health-text');
            const allOk = results.every(r => r.ok);

            if (allOk) {
                dot.classList.add('ok');
                text.textContent = 'All systems operational';
            } else {
                dot.classList.add('error');
                text.textContent = 'Some endpoints failed';
            }
        }

        init();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


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

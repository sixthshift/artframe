"""
SPA page routes for Artframe dashboard.

Serves the built Preact SPA for all non-API routes.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(tags=["SPA"])


def get_static_dir() -> Path:
    """Get the static directory path."""
    return Path(__file__).parent.parent / "static" / "dist"


def get_spa_index():
    """Serve the SPA index.html with correct asset paths."""
    static_dir = get_static_dir()
    index_path = static_dir / "index.html"

    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")

    # Fallback: show API explorer with live data
    fallback_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Artframe API Explorer</title>
        <style>
            * { box-sizing: border-box; }
            body { font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            h1 { color: #667eea; margin-bottom: 5px; }
            .subtitle { color: #666; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 16px; }
            .card { background: white; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .card h3 { margin: 0 0 12px 0; color: #333; display: flex; align-items: center; gap: 8px; }
            .card h3 a { color: #667eea; text-decoration: none; font-size: 14px; }
            .card h3 a:hover { text-decoration: underline; }
            pre { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 0; max-height: 300px; overflow-y: auto; }
            .loading { color: #999; font-style: italic; }
            .error { color: #e53e3e; }
            .endpoints { margin-top: 20px; }
            .endpoints h2 { color: #333; }
            .endpoint-list { display: flex; flex-wrap: wrap; gap: 8px; }
            .endpoint { background: #667eea; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 13px; }
            .endpoint:hover { background: #5a67d8; }
            .endpoint.post { background: #48bb78; }
            .endpoint.post:hover { background: #38a169; }
            .build-info { background: #fef3c7; border: 1px solid #f59e0b; padding: 12px; border-radius: 6px; margin-bottom: 20px; }
            .build-info code { background: #fff; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Artframe API Explorer</h1>
        <p class="subtitle">Frontend not built - showing raw API data</p>

        <div class="build-info">
            To build the frontend: <code>cd frontend && npm install && npm run build</code>
        </div>

        <div class="grid">
            <div class="card">
                <h3>System Status <a href="/api/status" target="_blank">/api/status</a></h3>
                <pre id="status" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <h3>Current Display <a href="/api/display/current" target="_blank">/api/display/current</a></h3>
                <pre id="display" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <h3>Scheduler <a href="/api/scheduler/status" target="_blank">/api/scheduler/status</a></h3>
                <pre id="scheduler" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <h3>Configuration <a href="/api/config" target="_blank">/api/config</a></h3>
                <pre id="config" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <h3>Connections <a href="/api/connections" target="_blank">/api/connections</a></h3>
                <pre id="connections" class="loading">Loading...</pre>
            </div>
            <div class="card">
                <h3>Plugins <a href="/api/plugins" target="_blank">/api/plugins</a></h3>
                <pre id="plugins" class="loading">Loading...</pre>
            </div>
        </div>

        <div class="endpoints">
            <h2>All API Endpoints</h2>
            <div class="endpoint-list">
                <a class="endpoint" href="/api/status" target="_blank">GET /api/status</a>
                <a class="endpoint" href="/api/connections" target="_blank">GET /api/connections</a>
                <a class="endpoint" href="/api/config" target="_blank">GET /api/config</a>
                <a class="endpoint" href="/api/scheduler/status" target="_blank">GET /api/scheduler/status</a>
                <a class="endpoint" href="/api/display/current" target="_blank">GET /api/display/current</a>
                <a class="endpoint" href="/api/display/preview" target="_blank">GET /api/display/preview</a>
                <a class="endpoint" href="/api/display/health" target="_blank">GET /api/display/health</a>
                <a class="endpoint" href="/api/plugins" target="_blank">GET /api/plugins</a>
                <a class="endpoint" href="/api/system/info" target="_blank">GET /api/system/info</a>
                <a class="endpoint" href="/api/schedules" target="_blank">GET /api/schedules</a>
                <a class="endpoint" href="/api/playlists" target="_blank">GET /api/playlists</a>
                <a class="endpoint post" href="/docs" target="_blank">OpenAPI Docs</a>
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
                } catch (e) {
                    el.textContent = 'Error: ' + e.message;
                    el.classList.remove('loading');
                    el.classList.add('error');
                }
            }

            fetchAndDisplay('/api/status', 'status');
            fetchAndDisplay('/api/display/current', 'display');
            fetchAndDisplay('/api/scheduler/status', 'scheduler');
            fetchAndDisplay('/api/config', 'config');
            fetchAndDisplay('/api/connections', 'connections');
            fetchAndDisplay('/api/plugins', 'plugins');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=fallback_html, status_code=200)


@router.get("/")
def index():
    """Serve SPA for root route."""
    return get_spa_index()


@router.get("/plugins")
def plugins_page():
    """Serve SPA for plugins page."""
    return get_spa_index()


@router.get("/schedule")
def schedule_page():
    """Serve SPA for schedule page."""
    return get_spa_index()


@router.get("/system")
def system_page():
    """Serve SPA for system page."""
    return get_spa_index()


@router.get("/config")
def config_page():
    """Serve SPA for config page."""
    return get_spa_index()


@router.get("/playlists")
def playlists_page():
    """Serve SPA for playlists page."""
    return get_spa_index()


@router.get("/assets/{filename:path}")
def serve_assets(filename: str):
    """Serve built assets from dist directory."""
    static_dir = get_static_dir() / "assets"
    file_path = static_dir / filename

    if not file_path.exists():
        return HTMLResponse(content="Not found", status_code=404)

    suffix = file_path.suffix.lower()
    media_types = {
        ".js": "application/javascript",
        ".css": "text/css",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)

"""
SPA page routes for Artframe dashboard.

Serves the built Preact SPA for all non-API routes.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()


def get_static_dir() -> Path:
    """Get the static directory path."""
    return Path(__file__).parent.parent / "static" / "dist"


def get_spa_index():
    """Serve the SPA index.html with correct asset paths."""
    static_dir = get_static_dir()

    # Check if the built SPA exists
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")

    # Fallback: return a simple HTML that explains the situation
    fallback_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Artframe - Build Required</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; }
            h1 { color: #667eea; }
            code { background: #f0f0f0; padding: 2px 8px; border-radius: 4px; }
            pre { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>Frontend Not Built</h1>
        <p>The frontend SPA has not been built yet. Run the following commands:</p>
        <pre>cd frontend
npm install
npm run build</pre>
        <p>This will build the frontend and place it in <code>src/artframe/web/static/dist/</code></p>
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


# Serve static assets from the dist directory
@router.get("/assets/{filename:path}")
def serve_assets(filename: str):
    """Serve built assets from dist directory."""
    static_dir = get_static_dir() / "assets"
    file_path = static_dir / filename

    if not file_path.exists():
        return HTMLResponse(content="Not found", status_code=404)

    # Determine media type based on extension
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

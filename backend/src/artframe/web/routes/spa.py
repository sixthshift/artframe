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

    # Fallback: explain how to build the frontend, with link to API
    fallback_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Artframe - Build Required</title>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <style>
            body { font-family: system-ui, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; }
            h1 { color: #667eea; }
            code { background: #f0f0f0; padding: 2px 8px; border-radius: 4px; }
            pre { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; }
            a { color: #667eea; }
            .links { margin-top: 20px; display: flex; gap: 12px; }
            .link { background: #667eea; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; }
            .link:hover { background: #5a67d8; }
        </style>
    </head>
    <body>
        <h1>Frontend Not Built</h1>
        <p>The frontend SPA has not been built yet. Run the following commands:</p>
        <pre>cd frontend
npm install
npm run build</pre>
        <p>This will build the frontend and place it in <code>src/artframe/web/static/dist/</code></p>
        <div class="links">
            <a class="link" href="/api">API Explorer</a>
            <a class="link" href="/docs">OpenAPI Docs</a>
        </div>
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


@router.get("/favicon.svg")
def serve_favicon():
    """Serve the favicon."""
    # First try the built dist directory
    static_dir = get_static_dir()
    favicon_path = static_dir / "favicon.svg"

    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")

    # Fallback to inline SVG
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect x="2" y="4" width="28" height="24" rx="2" fill="none" stroke="#1e293b" stroke-width="2.5"/>
  <rect x="6" y="8" width="20" height="16" rx="1" fill="none" stroke="#1e293b" stroke-width="1.5"/>
  <path d="M8 20 L12 15 L16 18 L20 12 L24 17 L24 22 L8 22 Z" fill="#f59e0b" opacity="0.8"/>
  <circle cx="21" cy="12" r="2" fill="#f59e0b"/>
</svg>'''
    from fastapi.responses import Response

    return Response(content=svg_content, media_type="image/svg+xml")


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

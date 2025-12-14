#!/bin/bash
# Update script to run directly on the Raspberry Pi
# Pulls latest code, copies frontend dist to backend, and restarts the service
#
# Usage: ./update.sh

set -e

# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Updating Artframe..."
echo "   Project root: $PROJECT_ROOT"
echo ""

# Pull latest from git
echo "Pulling latest from git..."
cd "$PROJECT_ROOT"
git pull

# Copy frontend dist to backend static
echo ""
echo "Copying frontend dist to backend..."
BACKEND_STATIC="$PROJECT_ROOT/backend/src/artframe/web/static/dist"
FRONTEND_DIST="$PROJECT_ROOT/frontend/dist"

if [ -d "$FRONTEND_DIST" ]; then
    rm -rf "$BACKEND_STATIC"
    cp -r "$FRONTEND_DIST" "$BACKEND_STATIC"
    echo "Frontend dist copied"
else
    echo "Warning: frontend/dist not found - skipping copy"
    echo "   (Build frontend on dev machine and commit, or build locally)"
fi

# Sync dependencies with uv
echo ""
echo "Syncing dependencies..."
cd "$PROJECT_ROOT/backend"
if command -v uv &> /dev/null; then
    uv sync
else
    echo "Warning: uv not found - skipping dependency sync"
fi

# Restart systemd service if running
echo ""
echo "Checking for systemd service..."
if systemctl is-active --quiet artframe 2>/dev/null; then
    echo "Restarting artframe service..."
    sudo systemctl restart artframe
    sleep 2
    sudo systemctl status artframe --no-pager -l | head -10
else
    echo "Service not running (start manually if needed)"
fi

echo ""
echo "Update complete!"

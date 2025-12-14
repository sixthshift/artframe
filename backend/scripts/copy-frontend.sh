#!/bin/bash
# Copy frontend dist to backend static directory
#
# Usage: ./copy-frontend.sh [--build]
#   --build    Build frontend before copying
#
# Run from anywhere - script detects project root automatically

set -e

# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

FRONTEND_DIR="$PROJECT_ROOT/frontend"
FRONTEND_DIST="$FRONTEND_DIR/dist"
BACKEND_STATIC="$PROJECT_ROOT/backend/src/artframe/web/static/dist"

# Check for --build flag
BUILD_FIRST=false
if [[ "$1" == "--build" ]]; then
    BUILD_FIRST=true
fi

# Build frontend if requested
if [[ "$BUILD_FIRST" == true ]]; then
    echo "Building frontend..."
    cd "$FRONTEND_DIR"

    # Install dependencies if node_modules doesn't exist
    if [[ ! -d "node_modules" ]]; then
        echo "Installing dependencies..."
        npm install
    fi

    npm run build
    echo ""
fi

# Check frontend dist exists
if [[ ! -d "$FRONTEND_DIST" ]]; then
    echo "Error: frontend/dist not found"
    echo "Build the frontend first:"
    echo "  cd frontend && npm run build"
    echo ""
    echo "Or run this script with --build:"
    echo "  ./copy-frontend.sh --build"
    exit 1
fi

# Copy to backend
echo "Copying frontend dist to backend..."
rm -rf "$BACKEND_STATIC"
cp -r "$FRONTEND_DIST" "$BACKEND_STATIC"

# Show what was copied
echo "Done! Copied to: $BACKEND_STATIC"
ls -la "$BACKEND_STATIC"

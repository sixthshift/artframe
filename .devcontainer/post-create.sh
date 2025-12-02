#!/bin/bash
# Post-create script for Artframe devcontainer

set -e

echo "Setting up Artframe development environment..."

# Install uv - fast Python package manager
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install Python package with all dependencies
echo "Installing Python dependencies with uv..."
cd /workspace/backend && uv sync --dev
cd /workspace

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd /workspace/frontend && npm install
cd /workspace

# Create development directories
echo "Creating development directories..."
mkdir -p logs
mkdir -p /tmp/artframe_dev
mkdir -p /tmp/artframe_cache

# Create environment file from template if it doesn't exist
echo "Setting up environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env file from template"
    fi
fi

# Make scripts executable
chmod +x backend/scripts/*.sh 2>/dev/null || true

echo ""
echo "Development environment setup complete!"
echo ""
echo "Useful commands:"
echo "  Python:"
echo "    cd backend && uv sync --dev      - Sync dependencies"
echo "    pytest backend/tests/ -v         - Run tests"
echo "    black backend/src/ backend/tests/  - Format code"
echo "    mypy backend/src/artframe        - Type check"
echo ""
echo "  Frontend:"
echo "    cd frontend && npm run dev    - Start dev server"
echo "    cd frontend && npm run build  - Build for production"
echo ""

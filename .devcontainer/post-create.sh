#!/bin/bash
# Post-create script for Artframe devcontainer

set -e

echo "🚀 Setting up Artframe development environment..."

# Install the package with all dependencies using uv sync (native mode)
echo "📦 Installing Artframe with uv sync (includes dev dependencies)..."
uv sync --dev

# Create development directories
echo "📁 Creating development directories..."
mkdir -p logs
mkdir -p /tmp/artframe_dev
mkdir -p /tmp/artframe_cache

# Create environment file from template if it doesn't exist
echo "⚙️  Setting up environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
    else
        echo "⚠️  No .env.example found - skipping .env creation"
    fi
fi


# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true

# Display helpful information
echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Edit .env file with your configuration"
echo "  2. Edit config/artframe-dev.yaml for your setup"
echo "  3. Run tests: pytest tests/"
echo ""
echo "💡 Useful commands:"
echo "  • Add package: uv add <package>"
echo "  • Add dev package: uv add --dev <package>"
echo "  • Sync dependencies: uv sync --dev"
echo "  • Format code: black src/ tests/"
echo "  • Type check: mypy src/artframe"
echo "  • Run tests: pytest tests/ -v"
echo ""

echo "Happy coding! 🎨"
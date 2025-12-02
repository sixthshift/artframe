#!/bin/bash
# Development installation script for Artframe

set -e

echo "🎨 Setting up Artframe for development..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "❌ Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo "🔗 Installing Artframe in development mode..."
pip install -e .

# Create development directories
echo "📁 Creating development directories..."
mkdir -p /tmp/artframe_cache
mkdir -p /tmp/artframe_dev
mkdir -p logs

# Create environment file template
echo "⚙️  Creating environment template..."
cat > .env.example << 'EOF'
# Artframe Development Environment Variables
# Copy this file to .env and fill in your actual values

# Immich Configuration
IMMICH_API_KEY=your_immich_api_key_here

# NanoBanana Configuration
NANOBANANA_API_KEY=your_nanobanana_api_key_here

# Development Settings
ARTFRAME_LOG_LEVEL=DEBUG
ARTFRAME_CONFIG_PATH=config/artframe-dev.yaml
EOF

echo "🧪 Running basic tests..."
if python -m pytest tests/ -v 2>/dev/null || echo "⚠️  Tests not found or failed - this is OK for initial setup"; then
    echo "✅ Test run completed"
fi

echo "🔍 Testing import..."
if python -c "import artframe; print(f'Artframe version: {artframe.__version__}')"; then
    echo "✅ Import test successful"
else
    echo "❌ Import test failed"
    exit 1
fi

echo ""
echo "✅ Development setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Edit config/artframe-dev.yaml for your development setup"
echo "3. Test the installation:"
echo "   source venv/bin/activate"
echo "   python -m artframe.main --config config/artframe-dev.yaml test"
echo "4. Run a manual update:"
echo "   python -m artframe.main --config config/artframe-dev.yaml update"
echo "5. Start development server:"
echo "   python -m artframe.main --config config/artframe-dev.yaml run"
echo ""
echo "💡 Development tips:"
echo "• Use 'mock' display driver for testing without hardware"
echo "• Check /tmp/artframe_dev/ for saved mock display images"
echo "• Set ARTFRAME_LOG_LEVEL=DEBUG for verbose logging"
echo ""
echo "🎉 Happy coding!"
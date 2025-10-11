#!/bin/bash
# Deploy script for Artframe to Raspberry Pi
# Usage: ./scripts/deploy.sh [pi-hostname-or-ip]

set -e

# Configuration
PI_HOST="${1:-pi@raspberrypi.local}"  # Default hostname, or pass as argument
PI_DIR="/home/pi/artframe"
LOCAL_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Artframe Deployment Script${NC}"
echo "================================"
echo "Target: $PI_HOST:$PI_DIR"
echo ""

# Check if we can connect to Pi
echo -e "${YELLOW}📡 Checking connection to Raspberry Pi...${NC}"
if ! ssh -o ConnectTimeout=5 $PI_HOST "echo 'Connected successfully'" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to $PI_HOST${NC}"
    echo "Please check:"
    echo "  1. Pi is powered on and connected to network"
    echo "  2. SSH is enabled on the Pi"
    echo "  3. Hostname/IP is correct"
    echo ""
    echo "Usage: $0 [pi-hostname-or-ip]"
    echo "Example: $0 pi@192.168.1.100"
    exit 1
fi
echo -e "${GREEN}✅ Connection successful${NC}"

# Check if this is first deployment
echo -e "${YELLOW}🔍 Checking if Artframe exists on Pi...${NC}"
if ssh $PI_HOST "[ -d $PI_DIR ]"; then
    echo -e "${GREEN}✅ Found existing installation${NC}"
    FIRST_DEPLOY=false
else
    echo -e "${YELLOW}📦 First deployment detected${NC}"
    FIRST_DEPLOY=true
fi

# Sync files
echo -e "${YELLOW}📤 Syncing files to Raspberry Pi...${NC}"
rsync -avz --delete \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude '.pytest_cache/' \
    --exclude 'logs/' \
    --exclude '/tmp/' \
    --exclude '.env' \
    --exclude '*.log' \
    --exclude '.DS_Store' \
    --exclude '.idea/' \
    --exclude '.vscode/' \
    $LOCAL_DIR/ $PI_HOST:$PI_DIR/

echo -e "${GREEN}✅ Files synced successfully${NC}"

# Run setup on Pi if first deployment
if [ "$FIRST_DEPLOY" = true ]; then
    echo -e "${YELLOW}🔧 Running initial setup on Pi...${NC}"
    ssh $PI_HOST << 'EOF'
        set -e
        cd /home/pi/artframe

        echo "Creating Python virtual environment..."
        python3 -m venv venv

        echo "Installing dependencies..."
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install -e .

        echo "Creating configuration from template..."
        if [ ! -f config/artframe-pi.yaml ]; then
            cp config/artframe-dev.yaml config/artframe-pi.yaml
            echo "⚠️  Please edit config/artframe-pi.yaml with your settings"
        fi

        echo "Creating necessary directories..."
        mkdir -p logs
        mkdir -p /tmp/artframe_cache

        echo "✅ Initial setup complete!"
EOF
else
    # Update dependencies if requirements.txt changed
    echo -e "${YELLOW}📦 Checking for dependency updates...${NC}"
    ssh $PI_HOST << 'EOF'
        set -e
        cd /home/pi/artframe
        source venv/bin/activate

        # Check if requirements.txt has changed
        if ! pip freeze | diff -q requirements.txt - > /dev/null 2>&1; then
            echo "Installing updated dependencies..."
            pip install -r requirements.txt
            pip install -e .
        else
            echo "Dependencies are up to date"
        fi
EOF
fi

# Test the deployment
echo -e "${YELLOW}🧪 Running deployment tests...${NC}"
ssh $PI_HOST << 'EOF'
    set -e
    cd /home/pi/artframe
    source venv/bin/activate

    echo "Testing import..."
    python -c "import artframe; print(f'✅ Artframe v{artframe.__version__} imported successfully')"

    echo "Testing configuration..."
    if [ -f config/artframe-pi.yaml ]; then
        python -m artframe.main --config config/artframe-pi.yaml test || true
    else
        echo "⚠️  No Pi configuration found, using dev config"
        python -m artframe.main --config config/artframe-dev.yaml test || true
    fi
EOF

# Check if service exists and restart if needed
echo -e "${YELLOW}🔄 Checking for systemd service...${NC}"
ssh $PI_HOST << 'EOF'
    if systemctl list-units --full -all | grep -Fq "artframe.service"; then
        echo "Restarting Artframe service..."
        sudo systemctl restart artframe
        sleep 2
        if systemctl is-active --quiet artframe; then
            echo "✅ Service restarted successfully"
            sudo systemctl status artframe --no-pager | head -10
        else
            echo "⚠️  Service failed to restart"
            sudo journalctl -u artframe -n 20 --no-pager
        fi
    else
        echo "ℹ️  No systemd service found (run setup_artframe.sh to install)"
    fi
EOF

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. SSH into Pi: ssh $PI_HOST"
echo "  2. Navigate to: cd $PI_DIR"
echo "  3. Edit config: nano config/artframe-pi.yaml"
echo "  4. Test manually: source venv/bin/activate && python -m artframe.main update"
echo "  5. Install service: sudo ./scripts/setup_artframe.sh"
echo ""
echo "Quick commands:"
echo "  - Manual update: ssh $PI_HOST 'cd $PI_DIR && source venv/bin/activate && python -m artframe.main update'"
echo "  - View logs: ssh $PI_HOST 'tail -f $PI_DIR/logs/artframe.log'"
echo "  - Service status: ssh $PI_HOST 'sudo systemctl status artframe'"
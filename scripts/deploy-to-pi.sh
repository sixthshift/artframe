#!/bin/bash
# Fast deployment script to Raspberry Pi using rsync
# This syncs code changes to the Pi for testing on real hardware

set -e

# Configuration - CUSTOMIZE THESE
PI_HOST="${PI_HOST:-pi@raspberrypi.local}"  # Set via env or use default
PI_DIR="${PI_DIR:-/home/pi/artframe}"
PI_PASSWORD="${PI_PASSWORD:-}"  # Optional - leave empty to use SSH keys

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Artframe to Raspberry Pi...${NC}"
echo -e "${BLUE}   Target: $PI_HOST:$PI_DIR${NC}"
echo ""

# Check if Pi is reachable
echo -e "${BLUE}📡 Testing connection to Pi...${NC}"
if ! ping -c 1 $(echo $PI_HOST | cut -d@ -f2) &> /dev/null; then
    echo -e "${RED}❌ Cannot reach Raspberry Pi at $PI_HOST${NC}"
    echo -e "${YELLOW}   Check that:${NC}"
    echo -e "${YELLOW}   - Pi is powered on and connected to network${NC}"
    echo -e "${YELLOW}   - Hostname/IP is correct (set PI_HOST env variable)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Pi is reachable${NC}"

# Sync code files (excluding virtual env, cache, logs)
echo ""
echo -e "${BLUE}📦 Syncing code to Pi...${NC}"
rsync -avz --delete \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude 'data/' \
    --exclude 'logs/' \
    --exclude 'tmp/' \
    --exclude '.mypy_cache/' \
    --exclude '.pytest_cache/' \
    --exclude '.vscode/' \
    --exclude '.claude/' \
    --exclude 'sample_outputs/' \
    --progress \
    ./ $PI_HOST:$PI_DIR/

echo -e "${GREEN}✓ Code synced${NC}"

# Install dependencies if requirements.txt changed
echo ""
echo -e "${BLUE}📥 Checking dependencies...${NC}"
ssh $PI_HOST "cd $PI_DIR && \
    if [ ! -d venv ]; then \
        echo 'Creating virtual environment...'; \
        python3 -m venv venv; \
    fi && \
    source venv/bin/activate && \
    pip install -q -r requirements.txt && \
    pip install -q -e ."

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Optional: Restart service if running as systemd
echo ""
echo -e "${BLUE}🔄 Checking for systemd service...${NC}"
if ssh $PI_HOST "systemctl is-active --quiet artframe" 2>/dev/null; then
    echo -e "${YELLOW}   Artframe service is running. Restart? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        ssh $PI_HOST "sudo systemctl restart artframe"
        echo -e "${GREEN}✓ Service restarted${NC}"
    else
        echo -e "${YELLOW}⚠ Service not restarted - you may need to restart manually${NC}"
    fi
else
    echo -e "${YELLOW}   Service not running (this is OK for manual testing)${NC}"
fi

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "   ${YELLOW}Test on Pi:${NC}"
echo -e "   ssh $PI_HOST"
echo -e "   cd $PI_DIR"
echo -e "   source venv/bin/activate"
echo -e "   python3 -m artframe.main --config config/artframe-pi.yaml"
echo ""
echo -e "   ${YELLOW}Or start web dashboard:${NC}"
echo -e "   python3 -m artframe.main --config config/artframe-pi.yaml --host 0.0.0.0 --port 8000"
echo -e "   (Access at http://$(echo $PI_HOST | cut -d@ -f2):8000)"
echo ""

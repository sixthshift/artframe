#!/bin/bash
# Quick test script for Raspberry Pi deployment
# Usage: ./scripts/quick_test.sh [pi-hostname-or-ip]

set -e

# Configuration
PI_HOST="${1:-pi@raspberrypi.local}"
PI_DIR="/home/pi/artframe"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧪 Artframe Quick Test${NC}"
echo "======================="
echo "Target: $PI_HOST"
echo ""

# Test connection
echo -e "${YELLOW}1. Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 $PI_HOST "echo 'SSH OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to $PI_HOST${NC}"
    exit 1
fi

# Test Python environment
echo -e "${YELLOW}2. Testing Python environment...${NC}"
ssh $PI_HOST << 'EOF'
    cd /home/pi/artframe || { echo "❌ Artframe directory not found"; exit 1; }
    source venv/bin/activate || { echo "❌ Virtual environment not found"; exit 1; }
    python -c "import artframe; print('✅ Artframe imported successfully')" || { echo "❌ Artframe import failed"; exit 1; }
    python -c "import sys; print(f'Python version: {sys.version.split()[0]}')"
EOF

# Test configuration
echo -e "${YELLOW}3. Testing configuration...${NC}"
ssh $PI_HOST << 'EOF'
    cd /home/pi/artframe
    source venv/bin/activate

    if [ -f config/artframe-pi.yaml ]; then
        CONFIG_FILE="config/artframe-pi.yaml"
    else
        CONFIG_FILE="config/artframe-dev.yaml"
        echo "⚠️  Using dev config (no Pi config found)"
    fi

    echo "Using config: $CONFIG_FILE"
    python -m artframe.main --config $CONFIG_FILE test || echo "⚠️  Connection tests failed (check API keys)"
EOF

# Test display (mock mode)
echo -e "${YELLOW}4. Testing display (mock mode)...${NC}"
ssh $PI_HOST << 'EOF'
    cd /home/pi/artframe
    source venv/bin/activate

    # Create temporary config with mock display
    cat > /tmp/artframe_test.yaml << 'YAML_EOF'
artframe:
  schedule:
    update_time: "09:00"
  source:
    provider: "immich"
    config:
      server_url: "http://localhost:2283"
      api_key: "dummy_key"
      selection: "random"
  style:
    provider: "nanobanana"
    config:
      api_url: "https://api.nanobanana.com"
      api_key: "dummy_key"
      styles: ["ghibli"]
  display:
    driver: "mock"
    config:
      width: 600
      height: 448
      save_images: true
      output_dir: "/tmp/artframe_test"
  cache:
    directory: "/tmp/artframe_cache_test"
    max_images: 5
    max_size_mb: 50
  logging:
    level: "DEBUG"
YAML_EOF

    mkdir -p /tmp/artframe_test /tmp/artframe_cache_test

    echo "Testing with mock display..."
    python examples/simple_test.py || echo "⚠️  Some tests failed"
EOF

# Test GPIO access (if running with hardware)
echo -e "${YELLOW}5. Testing GPIO access...${NC}"
ssh $PI_HOST << 'EOF'
    echo "Checking GPIO access..."
    if [ -c /dev/gpiomem ]; then
        echo "✅ GPIO device available"
        groups | grep -q gpio && echo "✅ User in gpio group" || echo "⚠️  User not in gpio group (run: sudo usermod -a -G gpio,spi pi)"
    else
        echo "❌ GPIO device not found"
    fi

    echo "Checking SPI access..."
    if ls /dev/spi* > /dev/null 2>&1; then
        echo "✅ SPI devices available:"
        ls -la /dev/spi*
        groups | grep -q spi && echo "✅ User in spi group" || echo "⚠️  User not in spi group"
    else
        echo "⚠️  SPI not enabled (run: sudo raspi-config -> Interface Options -> SPI)"
    fi
EOF

# Check system resources
echo -e "${YELLOW}6. Checking system resources...${NC}"
ssh $PI_HOST << 'EOF'
    echo "System information:"
    echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "  Kernel: $(uname -r)"
    echo "  Uptime: $(uptime -p)"
    echo "  CPU: $(nproc) cores, $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | xargs)"
    echo "  Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2 " used (" $3/$2*100 "%)"}' | xargs printf '%.0f%% used\n')"
    echo "  Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " used (" $5 ")"}')"
    echo "  Temperature: $(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 || echo "N/A")"
EOF

# Check if service exists
echo -e "${YELLOW}7. Checking systemd service...${NC}"
ssh $PI_HOST << 'EOF'
    if systemctl list-units --full -all | grep -Fq "artframe.service"; then
        echo "✅ Artframe service exists"
        if systemctl is-active --quiet artframe; then
            echo "✅ Service is running"
        else
            echo "⚠️  Service is not running"
        fi
        echo "Service status:"
        sudo systemctl status artframe --no-pager -l | head -10
    else
        echo "ℹ️  No systemd service installed"
        echo "   Run: sudo ./scripts/install.sh to install"
    fi
EOF

echo ""
echo -e "${GREEN}🎉 Quick test completed!${NC}"
echo ""
echo "Summary of next steps if needed:"
echo "  • Install dependencies: ssh $PI_HOST 'cd artframe && source venv/bin/activate && pip install -r requirements.txt'"
echo "  • Enable GPIO/SPI: ssh $PI_HOST 'sudo usermod -a -G gpio,spi pi && sudo raspi-config'"
echo "  • Install service: ssh $PI_HOST 'cd artframe && sudo ./scripts/install.sh'"
echo "  • Edit config: ssh $PI_HOST 'nano artframe/config/artframe-pi.yaml'"
echo "  • Test update: ssh $PI_HOST 'cd artframe && source venv/bin/activate && python -m artframe.main update'"
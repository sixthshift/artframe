#!/bin/bash
# Artframe Setup Script for Raspberry Pi
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/sixthshift/artframe/main/backend/scripts/install.sh | sudo bash
#
# Or from cloned repo:
#   sudo ./backend/scripts/install.sh

set -e

echo ""
echo "    ╔═══════════════════════════════════════════════════╗"
echo "    ║                                                   ║"
echo "    ║               █████╗ ██████╗ ████████╗            ║"
echo "    ║              ██╔══██╗██╔══██╗╚══██╔══╝            ║"
echo "    ║              ███████║██████╔╝   ██║               ║"
echo "    ║              ██╔══██║██╔══██╗   ██║               ║"
echo "    ║              ██║  ██║██║  ██║   ██║               ║"
echo "    ║              ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝               ║"
echo "    ║                                                   ║"
echo "    ║     ███████╗██████╗  █████╗ ███╗   ███╗███████╗   ║"
echo "    ║     ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝   ║"
echo "    ║     █████╗  ██████╔╝███████║██╔████╔██║█████╗     ║"
echo "    ║     ██╔══╝  ██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝     ║"
echo "    ║     ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗   ║"
echo "    ║     ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝   ║"
echo "    ║                                                   ║"
echo "    ║             Digital Photo Frame Setup             ║"
echo "    ║                                                   ║"
echo "    ╚═══════════════════════════════════════════════════╝"
echo ""

# Check if running as root for system setup
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root (use sudo)"
   exit 1
fi

# Configuration
ARTFRAME_USER=${ARTFRAME_USER:-pi}
INSTALL_DIR="/opt/artframe"
SERVICE_NAME="artframe"
LOG_DIR="/var/log/artframe"
CACHE_DIR="/var/cache/artframe"
REPO_URL="https://github.com/sixthshift/artframe.git"
REPO_BRANCH="main"
NEEDS_REBOOT=false

# Detect if we're running from within an existing repo clone
detect_repo_location() {
    # Check if we're in the repo root (has both backend and frontend dirs)
    if [ -d "backend" ] && [ -d "frontend" ] && [ -f "backend/pyproject.toml" ]; then
        echo "Running from repository root..."
        REPO_DIR="$(pwd)"
        return 0
    fi

    # Check if we're in the backend directory
    if [ -f "pyproject.toml" ] && grep -q "artframe" pyproject.toml 2>/dev/null; then
        if [ -d "../frontend" ]; then
            echo "Running from backend directory..."
            REPO_DIR="$(cd .. && pwd)"
            return 0
        fi
    fi

    # Check if we're in backend/scripts
    if [ -f "../pyproject.toml" ] && grep -q "artframe" ../pyproject.toml 2>/dev/null; then
        if [ -d "../../frontend" ]; then
            echo "Running from scripts directory..."
            REPO_DIR="$(cd ../.. && pwd)"
            return 0
        fi
    fi

    return 1
}

# Clone or update repository
setup_repository() {
    if detect_repo_location; then
        echo "Using existing repository at: $REPO_DIR"
    else
        echo "Cloning Artframe repository..."

        # Install git if not present
        if ! command -v git &> /dev/null; then
            apt-get update
            apt-get install -y git
        fi

        # Clone or update the repository
        if [ -d "$INSTALL_DIR/.git" ]; then
            echo "Repository exists at $INSTALL_DIR, pulling latest changes..."
            cd "$INSTALL_DIR"
            git pull origin "$REPO_BRANCH"
        else
            rm -rf "$INSTALL_DIR"
            git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
        fi
        REPO_DIR="$INSTALL_DIR"
    fi
}

# Enable SPI for e-ink display (handles both old and new Pi OS)
enable_spi() {
    echo "Enabling SPI interface..."

    # Try new location first (Pi 4/5 with newer OS)
    if [ -f "/boot/firmware/config.txt" ]; then
        BOOT_CONFIG="/boot/firmware/config.txt"
    elif [ -f "/boot/config.txt" ]; then
        BOOT_CONFIG="/boot/config.txt"
    else
        echo "WARNING: Could not find boot config file"
        echo "         You may need to enable SPI manually via raspi-config"
        return
    fi

    if ! grep -q "^dtparam=spi=on" "$BOOT_CONFIG"; then
        echo "dtparam=spi=on" >> "$BOOT_CONFIG"
        echo "SPI enabled in $BOOT_CONFIG"
        NEEDS_REBOOT=true
    else
        echo "SPI already enabled"
    fi
}

# Install Node.js for frontend build
install_nodejs() {
    echo "Setting up Node.js..."

    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo "Node.js already installed: $NODE_VERSION"
        return
    fi

    # Install Node.js via NodeSource (LTS version)
    echo "Installing Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs

    echo "Node.js installed: $(node --version)"
    echo "npm installed: $(npm --version)"
}

# Build frontend
build_frontend() {
    echo "Building frontend..."

    FRONTEND_DIR="$REPO_DIR/frontend"
    BACKEND_STATIC="$REPO_DIR/backend/src/artframe/web/static/dist"

    if [ ! -d "$FRONTEND_DIR" ]; then
        echo "WARNING: Frontend directory not found at $FRONTEND_DIR"
        echo "         Web dashboard may not work correctly"
        return
    fi

    cd "$FRONTEND_DIR"

    # Install dependencies and build
    sudo -u "$ARTFRAME_USER" npm ci 2>/dev/null || sudo -u "$ARTFRAME_USER" npm install
    sudo -u "$ARTFRAME_USER" npm run build

    # Copy built files to backend static directory
    echo "Copying frontend build to backend..."
    rm -rf "$BACKEND_STATIC"
    mkdir -p "$(dirname "$BACKEND_STATIC")"
    cp -r "$FRONTEND_DIR/dist" "$BACKEND_STATIC"

    echo "Frontend built successfully"
}

# Main installation
main() {
    setup_repository

    echo ""
    echo "Step 1/8: Updating system packages..."
    apt-get update
    apt-get upgrade -y

    echo ""
    echo "Step 2/8: Installing system dependencies..."
    apt-get install -y \
        python3 \
        python3-venv \
        python3-dev \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        libffi-dev \
        libssl-dev \
        build-essential \
        curl \
        git

    echo ""
    echo "Step 3/8: Enabling SPI interface..."
    enable_spi

    echo ""
    echo "Step 4/8: Creating directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CACHE_DIR"
    mkdir -p "$CACHE_DIR/photos"
    mkdir -p "$CACHE_DIR/styled"
    mkdir -p "$CACHE_DIR/metadata"
    mkdir -p "$INSTALL_DIR/backend/data"

    # Copy repository to install location if not already there
    if [ "$REPO_DIR" != "$INSTALL_DIR" ]; then
        echo "Copying files to $INSTALL_DIR..."
        cp -r "$REPO_DIR"/* "$INSTALL_DIR/"
    fi

    echo "Setting up permissions..."
    chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$INSTALL_DIR"
    chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$LOG_DIR"
    chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$CACHE_DIR"

    # Add user to required groups for GPIO/SPI access
    usermod -a -G gpio,spi "$ARTFRAME_USER" 2>/dev/null || true

    echo ""
    echo "Step 5/8: Installing Node.js and building frontend..."
    install_nodejs
    build_frontend

    echo ""
    echo "Step 6/8: Setting up Python environment with uv..."

    # Install uv for the artframe user
    ARTFRAME_USER_HOME=$(eval echo ~$ARTFRAME_USER)
    sudo -u "$ARTFRAME_USER" bash -c "
        curl -LsSf https://astral.sh/uv/install.sh | sh
    "

    echo "Installing Python dependencies..."
    # uv sync creates .venv automatically and installs all dependencies
    # Must run from backend directory where pyproject.toml is located
    sudo -u "$ARTFRAME_USER" bash -c "
        export PATH=\"\$HOME/.local/bin:\$HOME/.cargo/bin:\$PATH\"
        cd $INSTALL_DIR/backend
        uv sync
    "

    echo ""
    echo "Step 7/8: Setting up configuration..."

    # Copy Pi-specific configuration if it doesn't exist
    CONFIG_DEST="$INSTALL_DIR/backend/config/artframe.yaml"
    if [ ! -f "$CONFIG_DEST" ]; then
        # Try to find a Pi config template
        if [ -f "$INSTALL_DIR/config/artframe-pi.yaml" ]; then
            cp "$INSTALL_DIR/config/artframe-pi.yaml" "$CONFIG_DEST"
        elif [ -f "$INSTALL_DIR/backend/config/artframe-pi.yaml" ]; then
            cp "$INSTALL_DIR/backend/config/artframe-pi.yaml" "$CONFIG_DEST"
        else
            # Create a minimal default config
            cat > "$CONFIG_DEST" << 'CONFIGEOF'
# Artframe Configuration
# Edit this file with your settings

artframe:
  display:
    driver: "waveshare"
    config:
      model: "epd5in83"
      width: 600
      height: 448
      rotation: 0
      gpio_pins:
        busy: 24
        reset: 17
        dc: 25
        cs: 8

  storage:
    data_dir: "/opt/artframe/backend/data"
    cache_dir: "/var/cache/artframe"
    cache_max_mb: 1000
    cache_retention_days: 30

  logging:
    level: "INFO"
    dir: "/var/log/artframe"
    max_size_mb: 10
    backup_count: 5

  web:
    host: "0.0.0.0"
    port: 80
    debug: false

  scheduler:
    timezone: "UTC"
CONFIGEOF
        fi
        chown "$ARTFRAME_USER:$ARTFRAME_USER" "$CONFIG_DEST"
        echo "Configuration created at $CONFIG_DEST"
        echo "IMPORTANT: Edit this file to add your API keys and customize settings"
    else
        echo "Configuration already exists at $CONFIG_DEST"
    fi

    echo ""
    echo "Step 8/8: Installing systemd service..."

    SYSTEMD_SRC="$INSTALL_DIR/backend/systemd/artframe.service"
    if [ -f "$SYSTEMD_SRC" ]; then
        # Substitute user-specific paths
        sed -e "s|User=pi|User=$ARTFRAME_USER|g" \
            -e "s|Group=pi|Group=$ARTFRAME_USER|g" \
            -e "s|/opt/artframe/backend|$INSTALL_DIR/backend|g" \
            -e "s|/home/pi|$ARTFRAME_USER_HOME|g" \
            "$SYSTEMD_SRC" > "/etc/systemd/system/$SERVICE_NAME.service"

        # Enable service
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        echo "Systemd service installed and enabled"
    else
        echo "WARNING: Service file not found at $SYSTEMD_SRC"
        echo "         You'll need to start Artframe manually"
        SYSTEMD_SKIPPED=true
    fi

    # Create log rotation config
    cat > "/etc/logrotate.d/artframe" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 $ARTFRAME_USER $ARTFRAME_USER
    postrotate
        systemctl reload-or-restart artframe 2>/dev/null || true
    endscript
}
EOF

    # Print completion message
    echo ""
    echo "========================================"
    echo "  Installation Complete!"
    echo "========================================"
    echo ""
    echo "Configuration file: $CONFIG_DEST"
    echo ""

    if [ "$NEEDS_REBOOT" = true ]; then
        echo "IMPORTANT: SPI was enabled. You must reboot before starting Artframe:"
        echo "  sudo reboot"
        echo ""
        echo "After reboot:"
    fi

    if [ "$SYSTEMD_SKIPPED" != true ]; then
        echo "Start the service:"
        echo "  sudo systemctl start $SERVICE_NAME"
        echo ""
        echo "Check status:"
        echo "  sudo systemctl status $SERVICE_NAME"
        echo ""
        echo "View logs:"
        echo "  sudo journalctl -u $SERVICE_NAME -f"
        echo ""
        echo "Web dashboard will be available at:"
        echo "  http://$(hostname -I | awk '{print $1}')"
    else
        echo "Run manually:"
        echo "  cd $INSTALL_DIR/backend"
        echo "  sudo -u $ARTFRAME_USER ~/.local/bin/uv run artframe --config config/artframe.yaml"
    fi

    echo ""
    echo "Happy photo framing!"
}

# Run main installation
main "$@"
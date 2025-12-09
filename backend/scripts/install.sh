#!/bin/bash
# Artframe Setup Script for Raspberry Pi
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/sixthshift/artframe/main/backend/scripts/install.sh | sudo bash
#
# Or from cloned repo:
#   sudo ./backend/scripts/install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Output helpers
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }
step()    { echo -e "\n${CYAN}${BOLD}>>> $1${NC}"; }

# Spinner for long-running operations
spinner() {
    local pid=$1
    local message=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r${BLUE}[%s]${NC} %s" "${spin:i++%${#spin}:1}" "$message"
        sleep 0.1
    done
    printf "\r"
}

# Run command with spinner
run_with_spinner() {
    local message=$1
    shift
    "$@" > /tmp/artframe_install.log 2>&1 &
    local pid=$!
    spinner $pid "$message"
    wait $pid
    local status=$?
    if [ $status -eq 0 ]; then
        success "$message"
    else
        error "$message - see /tmp/artframe_install.log for details"
        return $status
    fi
}

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

# Configuration
ARTFRAME_USER=${ARTFRAME_USER:-pi}
INSTALL_DIR="/opt/artframe"
SERVICE_NAME="artframe"
LOG_DIR="/var/log/artframe"
CACHE_DIR="/var/cache/artframe"
REPO_URL="https://github.com/sixthshift/artframe.git"
REPO_BRANCH="main"
NEEDS_REBOOT=false
SWAP_CREATED=false
MIN_DISK_SPACE_MB=500

# Pre-flight checks
preflight_checks() {
    local checks_passed=true

    step "Running pre-flight checks"

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
    success "Running as root"

    # Check internet connectivity
    if ping -c 1 -W 3 github.com &> /dev/null; then
        success "Internet connectivity OK"
    else
        warn "Cannot reach github.com - installation may fail"
        checks_passed=false
    fi

    # Check available disk space
    local available_mb=$(df -m /opt 2>/dev/null | awk 'NR==2 {print $4}')
    if [ -z "$available_mb" ]; then
        available_mb=$(df -m / | awk 'NR==2 {print $4}')
    fi
    if [ "$available_mb" -ge "$MIN_DISK_SPACE_MB" ]; then
        success "Disk space OK (${available_mb}MB available)"
    else
        error "Insufficient disk space: ${available_mb}MB available, ${MIN_DISK_SPACE_MB}MB required"
        checks_passed=false
    fi

    # Detect Raspberry Pi
    if [ -f /proc/device-tree/model ]; then
        local pi_model=$(cat /proc/device-tree/model | tr -d '\0')
        success "Detected: $pi_model"
    elif grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        success "Detected: Raspberry Pi"
    else
        warn "Raspberry Pi not detected - e-ink display may not work"
    fi

    # Check if user exists
    if id "$ARTFRAME_USER" &>/dev/null; then
        success "User '$ARTFRAME_USER' exists"
    else
        error "User '$ARTFRAME_USER' does not exist. Set ARTFRAME_USER env var or create the user."
        checks_passed=false
    fi

    if [ "$checks_passed" = false ]; then
        echo ""
        warn "Some pre-flight checks failed. Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            error "Installation aborted"
            exit 1
        fi
    fi

    echo ""
}

# Uninstall function
uninstall() {
    echo ""
    echo -e "${RED}${BOLD}Uninstalling Artframe...${NC}"
    echo ""

    # Stop and disable service
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        info "Stopping $SERVICE_NAME service..."
        systemctl stop "$SERVICE_NAME"
    fi
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        info "Disabling $SERVICE_NAME service..."
        systemctl disable "$SERVICE_NAME"
    fi
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
        success "Removed systemd service"
    fi

    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        success "Removed $INSTALL_DIR"
    fi

    # Remove log directory
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        success "Removed $LOG_DIR"
    fi

    # Remove cache directory
    if [ -d "$CACHE_DIR" ]; then
        rm -rf "$CACHE_DIR"
        success "Removed $CACHE_DIR"
    fi

    # Remove logrotate config
    if [ -f "/etc/logrotate.d/artframe" ]; then
        rm -f "/etc/logrotate.d/artframe"
        success "Removed logrotate config"
    fi

    echo ""
    success "Artframe has been uninstalled"
    echo ""
    info "Note: User-installed tools (Node.js, uv) were not removed"
    exit 0
}

# Handle command line arguments
case "${1:-}" in
    --uninstall|-u)
        if [[ $EUID -ne 0 ]]; then
            error "This script must be run as root (use sudo)"
            exit 1
        fi
        uninstall
        ;;
    --help|-h)
        echo "Artframe Installation Script"
        echo ""
        echo "Usage:"
        echo "  sudo $0              Install Artframe"
        echo "  sudo $0 --uninstall  Remove Artframe"
        echo "  $0 --help            Show this help"
        echo ""
        echo "Environment variables:"
        echo "  ARTFRAME_USER        User to run Artframe as (default: pi)"
        exit 0
        ;;
esac

# Detect if we're running from within an existing repo clone
detect_repo_location() {
    # Check if we're in the repo root (has both backend and frontend dirs)
    if [ -d "backend" ] && [ -d "frontend" ] && [ -f "backend/pyproject.toml" ]; then
        info "Running from repository root..."
        REPO_DIR="$(pwd)"
        return 0
    fi

    # Check if we're in the backend directory
    if [ -f "pyproject.toml" ] && grep -q "artframe" pyproject.toml 2>/dev/null; then
        if [ -d "../frontend" ]; then
            info "Running from backend directory..."
            REPO_DIR="$(cd .. && pwd)"
            return 0
        fi
    fi

    # Check if we're in backend/scripts
    if [ -f "../pyproject.toml" ] && grep -q "artframe" ../pyproject.toml 2>/dev/null; then
        if [ -d "../../frontend" ]; then
            info "Running from scripts directory..."
            REPO_DIR="$(cd ../.. && pwd)"
            return 0
        fi
    fi

    return 1
}

# Clone or update repository
setup_repository() {
    if detect_repo_location; then
        success "Using existing repository at: $REPO_DIR"
    else
        info "Cloning Artframe repository..."

        # Install git if not present
        if ! command -v git &> /dev/null; then
            apt-get update
            apt-get install -y git
        fi

        # Clone or update the repository
        if [ -d "$INSTALL_DIR/.git" ]; then
            info "Repository exists at $INSTALL_DIR, pulling latest changes..."
            cd "$INSTALL_DIR"
            git pull origin "$REPO_BRANCH"
        else
            rm -rf "$INSTALL_DIR"
            git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
        fi
        REPO_DIR="$INSTALL_DIR"
        success "Repository ready"
    fi
}

# Enable SPI for e-ink display (handles both old and new Pi OS)
enable_spi() {
    info "Enabling SPI interface..."

    # Try new location first (Pi 4/5 with newer OS)
    if [ -f "/boot/firmware/config.txt" ]; then
        BOOT_CONFIG="/boot/firmware/config.txt"
    elif [ -f "/boot/config.txt" ]; then
        BOOT_CONFIG="/boot/config.txt"
    else
        warn "Could not find boot config file"
        info "You may need to enable SPI manually via raspi-config"
        return
    fi

    if ! grep -q "^dtparam=spi=on" "$BOOT_CONFIG"; then
        echo "dtparam=spi=on" >> "$BOOT_CONFIG"
        success "SPI enabled in $BOOT_CONFIG"
        NEEDS_REBOOT=true
    else
        success "SPI already enabled"
    fi
}

# Install Node.js for frontend build
install_nodejs() {
    info "Setting up Node.js..."

    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        success "Node.js already installed: $NODE_VERSION"
        return
    fi

    # Install Node.js via NodeSource (LTS version)
    info "Installing Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - > /tmp/artframe_install.log 2>&1
    apt-get install -y nodejs > /tmp/artframe_install.log 2>&1

    success "Node.js installed: $(node --version)"
    success "npm installed: $(npm --version)"
}

# Ensure adequate swap for npm on low-memory devices
ensure_swap() {
    local total_mem=$(free -m | awk '/^Mem:/{print $2}')
    local swap_size=$(free -m | awk '/^Swap:/{print $2}')

    # If less than 2GB RAM and less than 1GB swap, create temporary swap
    if [ "$total_mem" -lt 2048 ] && [ "$swap_size" -lt 1024 ]; then
        info "Low memory detected (${total_mem}MB RAM, ${swap_size}MB swap). Creating temporary swap..."

        # Use /var/tmp which is always on disk (not tmpfs like /tmp often is)
        SWAP_FILE="/var/tmp/artframe_swap"

        # Create 1GB swap file if it doesn't exist
        if [ ! -f "$SWAP_FILE" ]; then
            info "Allocating 1GB swap file (this may take a moment)..."
            dd if=/dev/zero of="$SWAP_FILE" bs=1M count=1024 2>/dev/null
            chmod 600 "$SWAP_FILE"
            mkswap "$SWAP_FILE" > /dev/null
        fi

        # Enable swap
        if swapon "$SWAP_FILE" 2>/dev/null; then
            SWAP_CREATED=true
            success "Temporary swap enabled (1GB)"
        else
            warn "Could not enable swap file"
        fi
    fi
}

# Clean up temporary swap
cleanup_swap() {
    SWAP_FILE="/var/tmp/artframe_swap"
    if [ "$SWAP_CREATED" = true ] && [ -f "$SWAP_FILE" ]; then
        swapoff "$SWAP_FILE" 2>/dev/null || true
        rm -f "$SWAP_FILE"
        info "Temporary swap removed"
    fi
}

# Build frontend
build_frontend() {
    info "Building frontend..."

    FRONTEND_DIR="$REPO_DIR/frontend"
    BACKEND_STATIC="$REPO_DIR/backend/src/artframe/web/static/dist"

    if [ ! -d "$FRONTEND_DIR" ]; then
        warn "Frontend directory not found at $FRONTEND_DIR"
        info "Web dashboard may not work correctly"
        return
    fi

    # Check if pre-built dist exists (from repo or previous build)
    if [ -d "$FRONTEND_DIR/dist" ]; then
        info "Found pre-built frontend assets"
        rm -rf "$BACKEND_STATIC"
        mkdir -p "$(dirname "$BACKEND_STATIC")"
        cp -r "$FRONTEND_DIR/dist" "$BACKEND_STATIC"
        success "Frontend assets installed from pre-built dist"
        return
    fi

    # Check available memory - npm needs at least 512MB RAM to build
    local total_mem=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$total_mem" -lt 512 ]; then
        error "Insufficient RAM for frontend build (${total_mem}MB available, 512MB minimum)"
        warn "This device has very limited memory. Options:"
        echo "  1. Build frontend on another machine and copy dist/ folder"
        echo "  2. Use a Raspberry Pi with at least 1GB RAM"
        echo "  3. Download pre-built assets (if available in releases)"
        echo ""
        info "Skipping frontend build - web dashboard will not work"
        return
    fi

    cd "$FRONTEND_DIR"

    # Ensure swap is available for low-memory devices
    ensure_swap

    # Install dependencies with memory-constrained settings
    info "Installing npm dependencies..."
    sudo -u "$ARTFRAME_USER" bash -c "
        export NODE_OPTIONS='--max-old-space-size=512'
        npm ci 2>/dev/null || npm install
    " > /tmp/artframe_install.log 2>&1

    info "Building frontend assets..."
    sudo -u "$ARTFRAME_USER" bash -c "
        export NODE_OPTIONS='--max-old-space-size=512'
        npm run build
    " > /tmp/artframe_install.log 2>&1

    # Clean up swap if we created it
    cleanup_swap

    # Copy built files to backend static directory
    info "Copying frontend build to backend..."
    rm -rf "$BACKEND_STATIC"
    mkdir -p "$(dirname "$BACKEND_STATIC")"
    cp -r "$FRONTEND_DIR/dist" "$BACKEND_STATIC"

    success "Frontend built successfully"
}

# Main installation
main() {
    preflight_checks
    setup_repository

    step "Step 1/8: Updating system packages"
    run_with_spinner "Updating package lists" apt-get update
    run_with_spinner "Upgrading packages" apt-get upgrade -y

    step "Step 2/8: Installing system dependencies"
    run_with_spinner "Installing system packages" apt-get install -y \
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

    step "Step 3/8: Enabling SPI interface"
    enable_spi

    step "Step 4/8: Creating directories"
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CACHE_DIR"
    mkdir -p "$CACHE_DIR/photos"
    mkdir -p "$CACHE_DIR/styled"
    mkdir -p "$CACHE_DIR/metadata"
    mkdir -p "$INSTALL_DIR/backend/data"
    success "Created directories"

    # Copy repository to install location if not already there
    if [ "$REPO_DIR" != "$INSTALL_DIR" ]; then
        info "Copying files to $INSTALL_DIR..."
        cp -r "$REPO_DIR"/* "$INSTALL_DIR/"
    fi

    info "Setting up permissions..."
    chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$INSTALL_DIR"
    chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$LOG_DIR"
    chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$CACHE_DIR"

    # Add user to required groups for GPIO/SPI access
    usermod -a -G gpio,spi "$ARTFRAME_USER" 2>/dev/null || true
    success "Permissions configured"

    step "Step 5/8: Installing Node.js and building frontend"
    install_nodejs
    build_frontend

    step "Step 6/8: Setting up Python environment with uv"

    # Install uv for the artframe user
    ARTFRAME_USER_HOME=$(eval echo ~$ARTFRAME_USER)
    info "Installing uv package manager..."
    sudo -u "$ARTFRAME_USER" bash -c "
        curl -LsSf https://astral.sh/uv/install.sh | sh
    " > /tmp/artframe_install.log 2>&1
    success "uv installed"

    info "Installing Python dependencies..."
    # uv sync creates .venv automatically and installs all dependencies
    # Must run from backend directory where pyproject.toml is located
    sudo -u "$ARTFRAME_USER" bash -c "
        export PATH=\"\$HOME/.local/bin:\$HOME/.cargo/bin:\$PATH\"
        cd $INSTALL_DIR/backend
        uv sync
    " > /tmp/artframe_install.log 2>&1
    success "Python dependencies installed"

    step "Step 7/8: Setting up configuration"

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
        success "Configuration created at $CONFIG_DEST"
        warn "Edit this file to add your API keys and customize settings"
    else
        info "Configuration already exists at $CONFIG_DEST"
    fi

    step "Step 8/8: Installing systemd service"

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
        success "Systemd service installed and enabled"
    else
        warn "Service file not found at $SYSTEMD_SRC"
        info "You'll need to start Artframe manually"
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
    echo -e "${GREEN}"
    echo "    ╔═══════════════════════════════════════════════════╗"
    echo "    ║                                                   ║"
    echo "    ║          Installation Complete!                   ║"
    echo "    ║                                                   ║"
    echo "    ╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"

    info "Configuration file: $CONFIG_DEST"
    echo ""

    if [ "$NEEDS_REBOOT" = true ]; then
        warn "SPI was enabled. You must reboot before starting Artframe:"
        echo -e "  ${BOLD}sudo reboot${NC}"
        echo ""
        info "After reboot:"
    fi

    if [ "$SYSTEMD_SKIPPED" != true ]; then
        echo -e "${BOLD}Start the service:${NC}"
        echo "  sudo systemctl start $SERVICE_NAME"
        echo ""
        echo -e "${BOLD}Check status:${NC}"
        echo "  sudo systemctl status $SERVICE_NAME"
        echo ""
        echo -e "${BOLD}View logs:${NC}"
        echo "  sudo journalctl -u $SERVICE_NAME -f"
        echo ""
        echo -e "${BOLD}Web dashboard:${NC}"
        echo -e "  ${CYAN}http://$(hostname -I | awk '{print $1}')${NC}"
    else
        echo -e "${BOLD}Run manually:${NC}"
        echo "  cd $INSTALL_DIR/backend"
        echo "  sudo -u $ARTFRAME_USER ~/.local/bin/uv run artframe --config config/artframe.yaml"
    fi

    echo ""
    echo -e "${GREEN}Happy photo framing!${NC}"
}

# Run main installation
main "$@"
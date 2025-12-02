#!/bin/bash
# Artframe Setup Script for Raspberry Pi

set -e

echo "🎨 Setting up Artframe Digital Photo Frame..."

# Check if running as root for system setup
if [[ $EUID -ne 0 ]]; then
   echo "This script should be run as root (use sudo)"
   exit 1
fi

# Configuration
ARTFRAME_USER=${ARTFRAME_USER:-pi}
INSTALL_DIR="/opt/artframe"
SERVICE_NAME="artframe"
LOG_DIR="/var/log/artframe"
CACHE_DIR="/var/cache/artframe"
REPO_URL="https://github.com/yourusername/artframe.git"
REPO_BRANCH="main"

# Check if we're running from within the repo or need to clone it
if [ -f "pyproject.toml" ] && grep -q "artframe" pyproject.toml 2>/dev/null; then
    echo "📂 Running from existing repository..."
    REPO_DIR="$(pwd)"
else
    echo "📥 Cloning Artframe repository..."

    # Install git if not present
    if ! command -v git &> /dev/null; then
        apt-get update
        apt-get install -y git
    fi

    # Clone or update the repository
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "   Repository exists, pulling latest changes..."
        cd "$INSTALL_DIR"
        git pull origin "$REPO_BRANCH"
    else
        rm -rf "$INSTALL_DIR"
        git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    REPO_DIR="$INSTALL_DIR"
fi

echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

echo "🔧 Installing system dependencies..."
apt-get install -y \
    python3 \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    curl

# Enable SPI for e-ink display
echo "🖥️  Enabling SPI interface..."
if ! grep -q "dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" >> /boot/config.txt
    echo "SPI enabled - system will need reboot after installation"
fi

echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$CACHE_DIR"
mkdir -p "$CACHE_DIR/photos"
mkdir -p "$CACHE_DIR/styled"
mkdir -p "$CACHE_DIR/metadata"

echo "🔐 Setting up permissions..."
chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$INSTALL_DIR"
chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$LOG_DIR"
chown -R "$ARTFRAME_USER:$ARTFRAME_USER" "$CACHE_DIR"

echo "🐍 Setting up Python environment with uv..."
cd "$INSTALL_DIR"

# Install uv for the artframe user
sudo -u "$ARTFRAME_USER" bash -c "
    curl -LsSf https://astral.sh/uv/install.sh | sh
"

echo "📥 Installing Artframe with uv..."
# uv sync creates .venv automatically and installs all dependencies
sudo -u "$ARTFRAME_USER" bash -c "
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    cd $INSTALL_DIR
    uv sync
"

echo "⚙️  Creating configuration..."
mkdir -p "$INSTALL_DIR/config"

# Copy example configuration if it doesn't exist
if [ ! -f "$INSTALL_DIR/config/artframe.yaml" ] && [ -f "$REPO_DIR/config/artframe.yaml" ]; then
    cp "$REPO_DIR/config/artframe.yaml" "$INSTALL_DIR/config/"
    chown "$ARTFRAME_USER:$ARTFRAME_USER" "$INSTALL_DIR/config/artframe.yaml"
    echo "📝 Example configuration copied to $INSTALL_DIR/config/artframe.yaml"
    echo "⚠️  Please edit the configuration file with your API keys and settings"
fi

echo "🔧 Installing systemd service..."
# Copy service file from repository
if [ -f "$REPO_DIR/systemd/artframe.service" ]; then
    # Use template and substitute variables
    ARTFRAME_USER_HOME=$(eval echo ~$ARTFRAME_USER)
    sed -e "s|User=pi|User=$ARTFRAME_USER|g" \
        -e "s|Group=pi|Group=$ARTFRAME_USER|g" \
        -e "s|WorkingDirectory=/opt/artframe|WorkingDirectory=$INSTALL_DIR|g" \
        -e "s|ReadWritePaths=/var/log/artframe /var/cache/artframe|ReadWritePaths=$LOG_DIR $CACHE_DIR $INSTALL_DIR/data|g" \
        -e "s|/home/pi/.local/bin|$ARTFRAME_USER_HOME/.local/bin|g" \
        "$REPO_DIR/systemd/artframe.service" > "/etc/systemd/system/$SERVICE_NAME.service"

    echo "✓ Service file installed from systemd/artframe.service"

    # Enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    echo "✓ Systemd service enabled"
else
    echo "⚠️  Warning: $REPO_DIR/systemd/artframe.service not found"
    echo "   Systemd service not installed. You'll need to:"
    echo "   1. Ensure systemd/artframe.service exists in the repository at $REPO_DIR"
    echo "   2. Manually install the service, or"
    echo "   3. Run Artframe manually without systemd"
    SYSTEMD_SKIPPED=true
fi

echo "📋 Creating maintenance scripts..."

# Log rotation
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
        systemctl reload-or-restart artframe
    endscript
}
EOF

# Backup script
cat > "$INSTALL_DIR/backup_config.sh" << 'EOF'
#!/bin/bash
# Backup Artframe configuration

BACKUP_DIR="/home/pi/artframe_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_DIR/artframe_config_$TIMESTAMP.tar.gz" \
    -C /opt/artframe config/ \
    -C /var/cache artframe/ \
    2>/dev/null

echo "Configuration backed up to: $BACKUP_DIR/artframe_config_$TIMESTAMP.tar.gz"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t artframe_config_*.tar.gz | tail -n +11 | xargs -r rm
EOF

chmod +x "$INSTALL_DIR/backup_config.sh"
chown "$ARTFRAME_USER:$ARTFRAME_USER" "$INSTALL_DIR/backup_config.sh"

echo "✅ Artframe setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Edit the configuration file: $INSTALL_DIR/config/artframe.yaml"

if [ "$SYSTEMD_SKIPPED" = true ]; then
    echo ""
    echo "⚠️  Systemd service was not installed (service file missing)"
    echo "   To run manually:"
    echo "   cd $INSTALL_DIR && sudo -u $ARTFRAME_USER uv run artframe"
    echo ""
    echo "   Or install systemd service manually (see $REPO_DIR/systemd/README.md)"
else
    echo "2. Start the service: systemctl start $SERVICE_NAME"
    echo "3. Check service status: systemctl status $SERVICE_NAME"
    echo "4. View logs: journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "   To stop: systemctl stop $SERVICE_NAME"
    echo "   To restart: systemctl restart $SERVICE_NAME"
fi

echo ""
echo "⚠️  If you enabled SPI, please reboot the system before starting Artframe"
echo ""
echo "🎉 Happy photo framing!"
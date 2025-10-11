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

echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

echo "🔧 Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libffi-dev \
    libssl-dev

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

echo "🐍 Setting up Python environment..."
cd "$INSTALL_DIR"

# Create virtual environment
sudo -u "$ARTFRAME_USER" python3 -m venv venv

# Activate virtual environment and install packages
sudo -u "$ARTFRAME_USER" bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install wheel setuptools
"

echo "📥 Installing Artframe (assuming source is available)..."
# Note: In production, this would clone from a repository
# For now, we'll assume the source is copied to the install directory

if [ -f "requirements.txt" ]; then
    sudo -u "$ARTFRAME_USER" bash -c "
        source venv/bin/activate
        pip install -r requirements.txt
    "
fi

if [ -f "setup.py" ]; then
    sudo -u "$ARTFRAME_USER" bash -c "
        source venv/bin/activate
        pip install -e .
    "
fi

echo "⚙️  Creating configuration..."
mkdir -p "$INSTALL_DIR/config"

# Copy example configuration if it doesn't exist
if [ ! -f "$INSTALL_DIR/config/artframe.yaml" ] && [ -f "config/artframe.yaml" ]; then
    cp config/artframe.yaml "$INSTALL_DIR/config/"
    chown "$ARTFRAME_USER:$ARTFRAME_USER" "$INSTALL_DIR/config/artframe.yaml"
    echo "📝 Example configuration copied to $INSTALL_DIR/config/artframe.yaml"
    echo "⚠️  Please edit the configuration file with your API keys and settings"
fi

echo "🔧 Installing systemd service..."
# Copy service file from repository
if [ -f "systemd/artframe.service" ]; then
    # Use template and substitute variables
    sed -e "s|User=pi|User=$ARTFRAME_USER|g" \
        -e "s|Group=pi|Group=$ARTFRAME_USER|g" \
        -e "s|WorkingDirectory=/opt/artframe|WorkingDirectory=$INSTALL_DIR|g" \
        -e "s|ReadWritePaths=/var/log/artframe /var/cache/artframe|ReadWritePaths=$LOG_DIR $CACHE_DIR $INSTALL_DIR/data|g" \
        systemd/artframe.service > "/etc/systemd/system/$SERVICE_NAME.service"

    echo "✓ Service file installed from systemd/artframe.service"
else
    echo "⚠️  Warning: systemd/artframe.service not found, using default configuration"
    # Fallback to basic service file
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Artframe Digital Photo Frame
After=network.target

[Service]
Type=simple
User=$ARTFRAME_USER
Group=$ARTFRAME_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python -m artframe
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
fi

echo "🔄 Enabling systemd service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

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
echo "2. Set your API keys as environment variables or in the config"
echo "3. Test the installation: sudo -u $ARTFRAME_USER $INSTALL_DIR/venv/bin/python -m artframe.main test"
echo "4. Start the service: systemctl start $SERVICE_NAME"
echo "5. Check service status: systemctl status $SERVICE_NAME"
echo "6. View logs: journalctl -u $SERVICE_NAME -f"
echo ""
echo "⚠️  If you enabled SPI, please reboot the system before starting Artframe"
echo ""
echo "🎉 Happy photo framing!"
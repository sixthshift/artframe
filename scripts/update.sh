#!/bin/bash
# Simple update script - pulls latest code and restarts Artframe
# Usage: ./scripts/update.sh [pi-hostname]

PI_HOST="${1:-pi@raspberrypi.local}"

echo "🚀 Updating Artframe on $PI_HOST..."

ssh $PI_HOST << 'EOF'
set -e

cd /opt/artframe

# Pull latest code
echo "📥 Pulling latest changes..."
git pull

# Update dependencies if needed
echo "📦 Checking dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet --upgrade

# Restart service
echo "🔄 Restarting Artframe..."
sudo systemctl restart artframe

# Show status
echo "✅ Update complete!"
echo ""
sudo systemctl status artframe --no-pager -l | head -15

EOF

echo ""
echo "Done! Artframe is updated and running."

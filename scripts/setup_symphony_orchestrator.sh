#!/bin/bash
# setup_symphony_orchestrator.sh - One-time setup for Symphony Orchestrator

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_NAME="symphony_orchestrator.py"
SERVICE_NAME="symphony-orchestrator"

echo "🎼 Setting up Symphony Orchestrator..."

# 1. Install required Python packages
echo "📦 Installing dependencies..."
pip install schedule croniter

# 2. Make scripts executable
echo "🔧 Setting permissions..."
chmod +x "$PROJECT_ROOT/scripts/$SCRIPT_NAME"
chmod +x "$PROJECT_ROOT/scripts/comprehensive_inventory.sh"
chmod +x "$PROJECT_ROOT/scripts/cleanup_engine.py"
chmod +x "$PROJECT_ROOT/scripts/automation_manager.py"
chmod +x "$PROJECT_ROOT/scripts/quick_health_check.sh"

# 3. Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/status/automation_health"
mkdir -p "$PROJECT_ROOT/config"

# 4. Create systemd service file
echo "🚀 Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Symphony Orchestrator - Automated AI Optimization Framework
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$PATH"
ExecStart=/usr/bin/python3 $PROJECT_ROOT/scripts/$SCRIPT_NAME start
ExecStop=/usr/bin/python3 $PROJECT_ROOT/scripts/$SCRIPT_NAME stop
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_ROOT/logs/orchestrator_systemd.log
StandardError=append:$PROJECT_ROOT/logs/orchestrator_systemd.log

[Install]
WantedBy=multi-user.target
EOF

# 5. Create default configuration if it doesn't exist
if [ ! -f "$PROJECT_ROOT/config/orchestrator_config.json" ]; then
    echo "📝 Creating default configuration..."
    python3 -c "
import sys
sys.path.append('$PROJECT_ROOT')
from scripts.symphony_orchestrator import SymphonyOrchestrator
orchestrator = SymphonyOrchestrator()
print('Default configuration created at config/orchestrator_config.json')
"
fi

# 6. Enable and start the service
echo "🎯 Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# 7. Wait a moment and check status
sleep 2
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Symphony Orchestrator is running!"
    echo ""
    echo "📊 Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager | head -10
    echo ""
    echo "🎵 Symphony Orchestrator is now running automatically!"
    echo ""
    echo "Useful commands:"
    echo "  - View status: sudo systemctl status $SERVICE_NAME"
    echo "  - View logs: tail -f $PROJECT_ROOT/logs/symphony_orchestrator.log"
    echo "  - Stop service: sudo systemctl stop $SERVICE_NAME"
    echo "  - Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  - Check tasks: python3 $PROJECT_ROOT/scripts/$SCRIPT_NAME status"
    echo "  - Run task manually: python3 $PROJECT_ROOT/scripts/$SCRIPT_NAME run --task <task_name>"
    echo ""
    echo "The orchestrator will automatically:"
    echo "  ✓ Run inventory scans daily at 2 AM"
    echo "  ✓ Analyze cleanup candidates daily at 2:30 AM"
    echo "  ✓ Execute cleanup weekly on Sundays at 3 AM"
    echo "  ✓ Check system health every 30 minutes"
    echo "  ✓ Monitor automation scripts hourly"
    echo "  ✓ Clean expired files daily at 4 AM"
    echo "  ✓ Perform git maintenance monthly"
else
    echo "❌ Failed to start Symphony Orchestrator"
    echo "Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi
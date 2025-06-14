#!/bin/bash

# Orchestra AI Autostart Installation Script
# Installs the autostart manager as a system service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/orchestra_autostart.py"

log "🎼 Installing Orchestra AI Autostart Service"
log "==========================================="

# Check if running as root (for systemd)
if [[ "$OSTYPE" == "linux-gnu"* ]] && [[ $EUID -eq 0 ]]; then
   error "Please run this script as a normal user, not root"
   exit 1
fi

# Make the autostart script executable
chmod +x "$SCRIPT_PATH"

# Detect OS and install appropriate service
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - Install LaunchAgent
    log "Detected macOS - Installing LaunchAgent..."
    
    PLIST_NAME="com.orchestra.ai.autostart"
    PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$HOME/Library/LaunchAgents"
    
    # Create plist file
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/venv/bin/python</string>
        <string>$SCRIPT_PATH</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/autostart-stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/autostart-stderr.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PROJECT_DIR/venv/bin</string>
        <key>PYTHONPATH</key>
        <string>$PROJECT_DIR:$PROJECT_DIR/api</string>
    </dict>
</dict>
</plist>
EOF
    
    # Load the LaunchAgent
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    
    success "LaunchAgent installed successfully!"
    log ""
    log "Commands:"
    log "  Start:   launchctl start $PLIST_NAME"
    log "  Stop:    launchctl stop $PLIST_NAME"
    log "  Status:  launchctl list | grep $PLIST_NAME"
    log "  Logs:    tail -f $PROJECT_DIR/logs/autostart-*.log"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - Install systemd service
    log "Detected Linux - Installing systemd service..."
    
    SERVICE_NAME="orchestra-ai-autostart"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"
    
    # Create service file
    cat > "/tmp/$SERVICE_NAME.service" << EOF
[Unit]
Description=Orchestra AI Autostart Manager
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin:$PROJECT_DIR/venv/bin"
Environment="PYTHONPATH=$PROJECT_DIR:$PROJECT_DIR/api"
ExecStart=$PROJECT_DIR/venv/bin/python $SCRIPT_PATH
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Install the service
    sudo mv "/tmp/$SERVICE_NAME.service" "$SERVICE_PATH"
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    
    success "Systemd service installed successfully!"
    log ""
    log "Commands:"
    log "  Start:   sudo systemctl start $SERVICE_NAME"
    log "  Stop:    sudo systemctl stop $SERVICE_NAME"
    log "  Status:  sudo systemctl status $SERVICE_NAME"
    log "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
    
else
    error "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Create a convenience script to manually run the autostart
cat > "$PROJECT_DIR/orchestra-autostart" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python scripts/orchestra_autostart.py
EOF
chmod +x "$PROJECT_DIR/orchestra-autostart"

log ""
success "🎉 Orchestra AI Autostart installation complete!"
log ""
log "The autostart manager will:"
log "  • Run AI context updates (setup_ai_agents.py)"
log "  • Start the API server"
log "  • Start the frontend"
log "  • Start MCP memory server"
log "  • Monitor all services and restart if needed"
log ""
log "To run manually: ./orchestra-autostart"
log "" 
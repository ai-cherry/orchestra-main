#!/bin/bash
# Orchestra Intelligent Automation Control Script
# Simple interface for the intelligent automation system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOMATION_SCRIPT="$SCRIPT_DIR/orchestra_intelligent_automation.py"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure logs directory exists
mkdir -p logs

case "$1" in
    start)
        echo -e "${GREEN}🚀 Starting Orchestra Intelligent Automation...${NC}"
        python3 "$AUTOMATION_SCRIPT" start
        
        # Also ensure Docker services are running
        if [ -f docker-compose.production.yml ]; then
            docker-compose -f docker-compose.production.yml up -d
        elif [ -f docker-compose.local.yml ]; then
            docker-compose -f docker-compose.local.yml up -d
        fi
        
        echo -e "${GREEN}✅ Automation system started!${NC}"
        echo "   Monitor logs: tail -f logs/orchestra_automation.log"
        ;;
        
    stop)
        echo -e "${YELLOW}🛑 Stopping Orchestra Intelligent Automation...${NC}"
        python3 "$AUTOMATION_SCRIPT" stop
        echo -e "${GREEN}✅ Automation system stopped${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}🔄 Restarting Orchestra Intelligent Automation...${NC}"
        python3 "$AUTOMATION_SCRIPT" restart
        echo -e "${GREEN}✅ Automation system restarted${NC}"
        ;;
        
    status)
        echo -e "${GREEN}📊 Orchestra Automation Status${NC}"
        echo "================================"
        python3 "$AUTOMATION_SCRIPT" status
        
        echo ""
        echo "Docker Services:"
        if [ -f docker-compose.production.yml ]; then
            docker-compose -f docker-compose.production.yml ps
        elif [ -f docker-compose.local.yml ]; then
            docker-compose -f docker-compose.local.yml ps
        fi
        ;;
        
    logs)
        echo -e "${GREEN}📜 Orchestra Automation Logs${NC}"
        echo "================================"
        tail -f logs/orchestra_automation.log
        ;;
        
    install)
        echo -e "${GREEN}📦 Installing Orchestra Automation as System Service${NC}"
        
        # Create systemd service file
        sudo tee /etc/systemd/system/orchestra-automation.service > /dev/null <<EOF
[Unit]
Description=Orchestra Intelligent Automation System
After=network.target docker.service
Requires=docker.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=/usr/local/bin:/usr/bin:/bin:$(pwd)/venv/bin"
ExecStart=$(pwd)/scripts/orchestra_auto_control.sh start
ExecStop=$(pwd)/scripts/orchestra_auto_control.sh stop
Restart=on-failure
RestartSec=30
StandardOutput=append:$(pwd)/logs/orchestra_automation.log
StandardError=append:$(pwd)/logs/orchestra_automation.log

[Install]
WantedBy=multi-user.target
EOF
        
        # Reload systemd and enable service
        sudo systemctl daemon-reload
        sudo systemctl enable orchestra-automation.service
        
        echo -e "${GREEN}✅ Automation installed as system service${NC}"
        echo "   Start on boot: enabled"
        echo "   Manual control: sudo systemctl {start|stop|status} orchestra-automation"
        ;;
        
    uninstall)
        echo -e "${YELLOW}🗑️  Uninstalling Orchestra Automation Service${NC}"
        
        sudo systemctl stop orchestra-automation.service || true
        sudo systemctl disable orchestra-automation.service || true
        sudo rm -f /etc/systemd/system/orchestra-automation.service
        sudo systemctl daemon-reload
        
        echo -e "${GREEN}✅ Service uninstalled${NC}"
        ;;
        
    *)
        echo "Orchestra Intelligent Automation Control"
        echo "======================================"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|install|uninstall}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the automation system"
        echo "  stop       - Stop the automation system"
        echo "  restart    - Restart the automation system"
        echo "  status     - Show system status"
        echo "  logs       - Follow automation logs"
        echo "  install    - Install as system service (auto-start on boot)"
        echo "  uninstall  - Remove system service"
        echo ""
        echo "The automation system provides:"
        echo "  • Automatic service health monitoring"
        echo "  • Self-healing capabilities"
        echo "  • Smart resource optimization"
        echo "  • Pattern-based predictive scaling"
        echo "  • Zero-maintenance operation"
        exit 1
        ;;
esac
#!/bin/bash
# 🔧 Setup SystemD Services for Always-On Production
# Ensures all Orchestra AI services start automatically and restart on failure

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="/home/ubuntu/orchestra-main"
SERVICE_USER="ubuntu"

echo -e "${BLUE}🔧 Setting up SystemD services for Orchestra AI...${NC}"

# Create Zapier MCP service
cat > /tmp/orchestra-zapier-mcp.service << EOF
[Unit]
Description=Orchestra AI Zapier MCP Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_ROOT/zapier-mcp
Environment=MCP_SERVER_PORT=80
Environment=NODE_ENV=production
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=orchestra-zapier-mcp

# Resource limits
LimitNOFILE=65536
MemoryMax=1G

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$PROJECT_ROOT

[Install]
WantedBy=multi-user.target
EOF

# Create Personas API service
cat > /tmp/orchestra-personas-api.service << EOF
[Unit]
Description=Orchestra AI Personas API
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
Environment=ENABLE_ADVANCED_MEMORY=true
Environment=PERSONA_SYSTEM=enabled
Environment=CROSS_DOMAIN_ROUTING=enabled
ExecStart=/usr/bin/python3 personas_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=orchestra-personas-api

# Resource limits
LimitNOFILE=65536
MemoryMax=2G

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$PROJECT_ROOT

[Install]
WantedBy=multi-user.target
EOF

# Create Infrastructure service
cat > /tmp/orchestra-infrastructure.service << EOF
[Unit]
Description=Orchestra AI Infrastructure Services
After=docker.service
Wants=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/docker-compose -f docker-compose.production.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.production.yml down
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

# Create main monitoring service
cat > /tmp/orchestra-monitor.service << EOF
[Unit]
Description=Orchestra AI Service Monitor
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/scripts/production_manager.sh ensure
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal
SyslogIdentifier=orchestra-monitor

[Install]
WantedBy=multi-user.target
EOF

# Install services
echo -e "${BLUE}📝 Installing SystemD services...${NC}"

sudo mv /tmp/orchestra-*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable services
services=("orchestra-zapier-mcp" "orchestra-personas-api" "orchestra-infrastructure" "orchestra-monitor")

for service in "${services[@]}"; do
    echo -e "${BLUE}🔧 Enabling $service...${NC}"
    sudo systemctl enable "$service"
    
    echo -e "${BLUE}🚀 Starting $service...${NC}"
    sudo systemctl start "$service"
    
    sleep 5
    
    if sudo systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✅ $service is running${NC}"
    else
        echo -e "${RED}❌ $service failed to start${NC}"
        sudo systemctl status "$service"
    fi
done

# Create timer for health checks
cat > /tmp/orchestra-health-check.timer << EOF
[Unit]
Description=Orchestra AI Health Check Timer
Requires=orchestra-health-check.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Unit=orchestra-health-check.service

[Install]
WantedBy=timers.target
EOF

cat > /tmp/orchestra-health-check.service << EOF
[Unit]
Description=Orchestra AI Health Check
After=network.target

[Service]
Type=oneshot
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/scripts/daily_health_check.sh
StandardOutput=journal
StandardError=journal
SyslogIdentifier=orchestra-health-check
EOF

sudo mv /tmp/orchestra-health-check.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable orchestra-health-check.timer
sudo systemctl start orchestra-health-check.timer

echo -e "${GREEN}🎉 SystemD services setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Management commands:${NC}"
echo "  sudo systemctl status orchestra-zapier-mcp"
echo "  sudo systemctl restart orchestra-personas-api" 
echo "  sudo journalctl -u orchestra-monitor -f"
echo "  sudo systemctl list-timers orchestra-*" 
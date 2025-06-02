#!/bin/bash
# MCP Auto-Start Setup Script
# This script creates systemd services for all MCP servers

set -e

echo "=== MCP Auto-Start Setup ==="

# First, fix PostgreSQL permissions
echo "Fixing PostgreSQL permissions..."
sudo -u postgres psql << EOF
CREATE USER orchestrator WITH PASSWORD 'orch3str4_2024' CREATEDB;
ALTER USER orchestrator WITH PASSWORD 'orch3str4_2024';
GRANT ALL PRIVILEGES ON DATABASE orchestrator TO orchestrator;
\q
EOF

# Create systemd service for Memory MCP
echo "Creating Memory MCP service..."
sudo tee /etc/systemd/system/mcp-memory.service > /dev/null << 'EOF'
[Unit]
Description=Orchestra MCP Memory Server
After=postgresql.service network.target
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="POSTGRES_HOST=localhost"
Environment="POSTGRES_PORT=5432"
Environment="POSTGRES_DB=orchestrator"
Environment="POSTGRES_USER=orchestrator"
Environment="POSTGRES_PASSWORD=orch3str4_2024"
Environment="WEAVIATE_HOST=localhost"
Environment="WEAVIATE_PORT=8080"
Environment="MCP_MEMORY_PORT=8003"
ExecStart=/root/orchestra-main/venv/bin/python /root/orchestra-main/mcp_server/servers/memory_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Orchestrator MCP
echo "Creating Orchestrator MCP service..."
sudo tee /etc/systemd/system/mcp-orchestrator.service > /dev/null << 'EOF'
[Unit]
Description=Orchestra MCP Orchestrator Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="API_URL=http://localhost:8080"
Environment="API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
Environment="MCP_ORCHESTRATOR_PORT=8002"
ExecStart=/root/orchestra-main/venv/bin/python /root/orchestra-main/mcp_server/servers/orchestrator_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Tools MCP
echo "Creating Tools MCP service..."
sudo tee /etc/systemd/system/mcp-tools.service > /dev/null << 'EOF'
[Unit]
Description=Orchestra MCP Tools Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="MCP_TOOLS_PORT=8006"
ExecStart=/root/orchestra-main/venv/bin/python /root/orchestra-main/mcp_server/servers/tools_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Weaviate Direct MCP
echo "Creating Weaviate Direct MCP service..."
sudo tee /etc/systemd/system/mcp-weaviate.service > /dev/null << 'EOF'
[Unit]
Description=Orchestra MCP Weaviate Direct Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="MCP_WEAVIATE_DIRECT_PORT=8001"
Environment="WEAVIATE_HOST=localhost"
Environment="WEAVIATE_PORT=8080"
Environment="WEAVIATE_GRPC_PORT=50051"
ExecStart=/root/orchestra-main/venv/bin/python /root/orchestra-main/mcp_server/servers/weaviate_direct_mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable all services
echo "Enabling MCP services..."
sudo systemctl enable mcp-memory.service
sudo systemctl enable mcp-orchestrator.service
sudo systemctl enable mcp-tools.service
sudo systemctl enable mcp-weaviate.service

# Start all services
echo "Starting MCP services..."
sudo systemctl start mcp-memory.service
sudo systemctl start mcp-orchestrator.service
sudo systemctl start mcp-tools.service
sudo systemctl start mcp-weaviate.service

echo ""
echo "=== MCP Auto-Start Setup Complete ==="
echo ""
echo "Services created:"
echo "  - mcp-memory.service"
echo "  - mcp-orchestrator.service"
echo "  - mcp-tools.service"
echo "  - mcp-weaviate.service"
echo ""
echo "Useful commands:"
echo "  Check status:  systemctl status mcp-*.service"
echo "  View logs:     journalctl -u mcp-memory -f"
echo "  Restart all:   systemctl restart mcp-*.service"
echo "  Stop all:      systemctl stop mcp-*.service"
echo "" 
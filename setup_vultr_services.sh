#!/bin/bash
# Setup systemd services for cherry_ai on Vultr

# Create cherry_ai API service
sudo tee /etc/systemd/system/cherry_ai-api.service > /dev/null << 'EOF'
[Unit]
Description=cherry_ai API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cherry_ai
Environment="PATH=/opt/cherry_ai/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/opt/cherry_ai"
EnvironmentFile=/opt/cherry_ai/.env
ExecStart=/opt/cherry_ai/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create cherry_ai MCP service
sudo tee /etc/systemd/system/conductor-mcp.service > /dev/null << 'EOF'
[Unit]
Description=cherry_ai MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cherry_ai
Environment="PATH=/opt/cherry_ai/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/opt/cherry_ai"
EnvironmentFile=/opt/cherry_ai/.env
ExecStart=/opt/cherry_ai/venv/bin/python -m mcp_server.servers.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
sudo tee /usr/local/bin/cherry_ai-monitor > /dev/null << 'EOF'
#!/bin/bash
echo "cherry_ai System Status"
echo "====================="
echo
echo "Services:"
systemctl status cherry_ai-api conductor-mcp --no-pager
echo
echo "Docker:"
docker ps
echo
echo "API Health:"
curl -s http://localhost:8000/health | jq . || echo "API not responding"
echo
echo "Weaviate Health:"
curl -s http://localhost:8080/v1/.well-known/ready || echo "Weaviate not ready"
EOF

chmod +x /usr/local/bin/cherry_ai-monitor

# Reload systemd
systemctl daemon-reload

# Enable and start services
systemctl enable cherry_ai-api conductor-mcp
systemctl start cherry_ai-api conductor-mcp

echo "Services configured and started!"

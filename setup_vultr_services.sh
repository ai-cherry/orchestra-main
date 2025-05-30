#!/bin/bash
# Setup systemd services for Orchestra on Vultr

# Create Orchestra API service
sudo tee /etc/systemd/system/orchestra-api.service > /dev/null << 'EOF'
[Unit]
Description=Orchestra API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/orchestra
Environment="PATH=/opt/orchestra/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/opt/orchestra"
EnvironmentFile=/opt/orchestra/.env
ExecStart=/opt/orchestra/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Orchestra MCP service
sudo tee /etc/systemd/system/orchestra-mcp.service > /dev/null << 'EOF'
[Unit]
Description=Orchestra MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/orchestra
Environment="PATH=/opt/orchestra/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/opt/orchestra"
EnvironmentFile=/opt/orchestra/.env
ExecStart=/opt/orchestra/venv/bin/python -m mcp_server.servers.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
sudo tee /usr/local/bin/orchestra-monitor > /dev/null << 'EOF'
#!/bin/bash
echo "Orchestra System Status"
echo "====================="
echo
echo "Services:"
systemctl status orchestra-api orchestra-mcp --no-pager
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

chmod +x /usr/local/bin/orchestra-monitor

# Reload systemd
systemctl daemon-reload

# Enable and start services
systemctl enable orchestra-api orchestra-mcp
systemctl start orchestra-api orchestra-mcp

echo "Services configured and started!"

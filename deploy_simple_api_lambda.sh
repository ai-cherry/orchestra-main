#!/bin/bash

echo "🚀 Deploying Simple Cherry AI API to Lambda Labs"
echo "=============================================="

SERVER_IP="150.136.94.139"
USERNAME="ubuntu"

# Copy the API server file
echo "1. Copying API server to Lambda Labs..."
scp simple_cherry_api.py $USERNAME@$SERVER_IP:/opt/orchestra/

# Deploy and configure
echo -e "\n2. Setting up API server..."
ssh $USERNAME@$SERVER_IP << 'EOF'
cd /opt/orchestra

# Install dependencies if needed
echo "Installing dependencies..."
sudo pip3 install fastapi uvicorn pydantic

# Stop any existing API server
echo "Stopping existing API server if running..."
sudo pkill -f "simple_cherry_api.py" || true
sudo pkill -f "cherry_api_server.py" || true

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/cherry-api.service > /dev/null << 'SERVICE'
[Unit]
Description=Cherry AI API Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/orchestra
Environment="PYTHONPATH=/opt/orchestra"
ExecStart=/usr/bin/python3 /opt/orchestra/simple_cherry_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Update nginx configuration to proxy API requests
echo "Updating nginx configuration..."
sudo tee /etc/nginx/sites-available/orchestra > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;
    
    # Serve the orchestrator UI
    location /orchestrator {
        alias /opt/orchestra;
        try_files $uri $uri/ /cherry-ai-orchestrator-final.html;
    }
    
    # Proxy API requests
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Root serves the orchestrator
    location / {
        alias /opt/orchestra/;
        try_files /cherry-ai-orchestrator-final.html =404;
    }
}
NGINX

# Enable and start the service
echo "Starting Cherry API service..."
sudo systemctl daemon-reload
sudo systemctl enable cherry-api
sudo systemctl restart cherry-api

# Reload nginx
echo "Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

# Wait for service to start
sleep 3

# Check if it's running
if sudo systemctl is-active cherry-api > /dev/null; then
    echo "✅ API Server started successfully"
else
    echo "❌ Failed to start API server"
    sudo journalctl -u cherry-api -n 20
fi

# Test the API
echo -e "\nTesting API endpoints..."
curl -s http://localhost:8000/api/health | jq '.' || echo "API not responding"
EOF

echo -e "\n3. Testing from local machine..."
echo "Testing health endpoint..."
curl -s http://$SERVER_IP/api/health | jq '.' || echo "Cannot reach API from local"

echo -e "\nTesting search endpoint..."
curl -s "http://$SERVER_IP/api/search?q=test&type=internal" | jq '.' || echo "Search API not working"

echo -e "\n=============================================="
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access Points:"
echo "  • Orchestrator UI: http://$SERVER_IP/orchestrator/"
echo "  • API Health: http://$SERVER_IP/api/health"
echo "  • Direct API: http://$SERVER_IP:8000/"
echo ""
echo "📝 The API now provides:"
echo "  • /api/health - Health check"
echo "  • /api/search - Search functionality"
echo "  • /api/agents - Agent list"
echo "  • /api/orchestrations - Orchestration list"
echo "  • /api/workflows - Workflow list"
echo "=============================================="
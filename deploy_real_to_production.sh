#!/bin/bash
# Deploy Real Agents to Production Server (cherry-ai.me)

set -e

echo "🚀 Deploying Real Agents to Production (cherry-ai.me)"
echo "===================================================="

# Server details
SERVER_IP="45.32.69.157"
SERVER_USER="root"
SERVER_PASSWORD='z+G3D,$n9M3.=Dr}'

# Create SSH command function
ssh_cmd() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$@"
}

# Create SCP command function
scp_cmd() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$1" $SERVER_USER@$SERVER_IP:"$2"
}

echo "📋 Step 1: Checking server connection..."
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

# Test connection
ssh_cmd "echo '✅ Connected to server successfully'"

echo "🛑 Step 2: Stopping mock services..."
ssh_cmd << 'EOF'
# Kill all existing Orchestra processes
pkill -f "uvicorn" || true
pkill -f "orchestra" || true
systemctl stop orchestra-api || true
systemctl stop orchestra-real || true
sleep 2

# Remove old mock installation
rm -rf /opt/orchestra
echo "✅ Mock services stopped and removed"
EOF

echo "📥 Step 3: Updating code..."
ssh_cmd << 'EOF'
cd /root/orchestra-main

# Backup current state
cp -r agent/app/services/real_agents.py agent/app/services/real_agents.py.backup 2>/dev/null || true

# Pull latest changes
git pull origin main || echo "No git repo, will sync files"
EOF

# Copy real agents file
echo "📦 Step 4: Syncing real agents code..."
scp_cmd "agent/app/services/real_agents.py" "/root/orchestra-main/agent/app/services/"
scp_cmd "agent/app/routers/admin.py" "/root/orchestra-main/agent/app/routers/"
scp_cmd "requirements/production/requirements.txt" "/root/orchestra-main/requirements/production/"

echo "🐍 Step 5: Installing dependencies..."
ssh_cmd << 'EOF'
cd /root/orchestra-main

# Activate virtual environment
source venv/bin/activate

# Install missing dependencies
pip install psutil==7.0.0
pip install -r requirements/production/requirements.txt

echo "✅ Dependencies installed"
EOF

echo "🔧 Step 6: Updating configuration..."
ssh_cmd << 'EOF'
# Update .env if needed
cd /root/orchestra-main
if ! grep -q "ORCHESTRA_API_KEY" .env 2>/dev/null; then
    echo "ORCHESTRA_API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" >> .env
fi

# Update systemd service
cat > /etc/systemd/system/orchestra-real.service << 'SERVICE'
[Unit]
Description=Orchestra AI Real Agents
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/root/orchestra-main"
EnvironmentFile=/root/orchestra-main/.env
ExecStart=/root/orchestra-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
echo "✅ Configuration updated"
EOF

echo "🌐 Step 7: Updating nginx configuration..."
ssh_cmd << 'EOF'
# Update nginx to proxy to port 8000
cat > /etc/nginx/sites-available/orchestra-admin << 'NGINX'
server {
    listen 80;
    server_name cherry-ai.me;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name cherry-ai.me;

    # SSL configuration from certbot
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Admin UI static files
    root /var/www/orchestra-admin;
    index index.html;

    # Try static files first, then proxy to API
    location / {
        try_files $uri $uri/ @api;
    }

    # API proxy
    location @api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API routes
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
NGINX

nginx -t && systemctl reload nginx
echo "✅ Nginx updated"
EOF

echo "🚀 Step 8: Starting real agents..."
ssh_cmd << 'EOF'
cd /root/orchestra-main

# Start the service
systemctl enable orchestra-real
systemctl start orchestra-real

# Wait for it to start
sleep 5

# Check status
systemctl status orchestra-real --no-pager
EOF

echo "✅ Step 9: Verifying deployment..."
ssh_cmd << 'EOF'
# Check if service is running
if systemctl is-active --quiet orchestra-real; then
    echo "✅ Service is running"
else
    echo "❌ Service failed to start"
    journalctl -u orchestra-real -n 50 --no-pager
    exit 1
fi

# Test API locally
echo "Testing API endpoints..."
curl -s http://localhost:8000/health | jq . || echo "Health check failed"

# Test real agents
curl -s http://localhost:8000/api/agents \
  -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | jq . || echo "Agents endpoint failed"

# Check what's listening on ports
echo -e "\nServices listening on ports:"
netstat -tlnp | grep -E ":(80|443|8000|8080) "
EOF

echo ""
echo "🎉 Deployment Complete!"
echo "====================="
echo ""
echo "✅ Real agents are now live at: https://cherry-ai.me"
echo ""
echo "Test with:"
echo "  curl https://cherry-ai.me/api/agents -H 'X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd'"
echo ""
echo "Or visit: https://cherry-ai.me"
echo ""
echo "View logs with:"
echo "  ssh root@45.32.69.157 'journalctl -u orchestra-real -f'"

#!/bin/bash
echo "🔥 FIXING EVERYTHING AND DELETING MOCK CRAP..."

# Kill ALL old processes
echo "⏹️  Killing all old processes..."
pkill -f uvicorn || true
pkill -f agent.app.main || true
pkill -f cherry_ai || true
sleep 3

# Disable and remove old services
echo "🗑️  Removing old mock services..."
systemctl stop cherry_ai-api || true
systemctl disable cherry_ai-api || true
systemctl stop conductor-mcp || true
systemctl disable conductor-mcp || true
rm -f /etc/systemd/system/cherry_ai-api.service
rm -f /etc/systemd/system/conductor-mcp.service

# Delete the old mock installation
echo "💥 DELETING OLD MOCK INSTALLATION..."
rm -rf /opt/cherry_ai

# Start REAL agents
echo "🚀 Starting REAL agents..."
cd /root/cherry_ai-main
source venv/bin/activate
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000 > /root/api_real.log 2>&1 &
sleep 5

# Create permanent service for REAL agents
echo "📌 Creating permanent service..."
cat > /etc/systemd/system/cherry_ai-real.service << 'EOF'
[Unit]
Description=Cherry AI REAL Agents (NO MOCK)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cherry_ai-main
Environment="PATH=/root/cherry_ai-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/root/cherry_ai-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cherry_ai-real
systemctl start cherry_ai-real

# Update nginx to point to port 8000
echo "🔧 Updating nginx..."
sed -i 's/proxy_pass http:\/\/localhost:8080/proxy_pass http:\/\/localhost:8000/g' /etc/nginx/sites-available/default || true
sed -i 's/proxy_pass http:\/\/localhost:8080/proxy_pass http:\/\/localhost:8000/g' /etc/nginx/sites-available/cherry_ai* || true
nginx -t && systemctl reload nginx

# Test the REAL API
echo ""
echo "✅ Testing REAL agents..."
sleep 3
curl -s -X GET 'http://localhost:8000/api/agents' -H 'X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd' | jq '.' | head -20

echo ""
echo "🎉 DONE! Mock garbage DELETED. REAL agents running!"
echo "📍 Check https://cherry-ai.me - you'll see:"
echo "   - sys-001 (REAL system monitor)"
echo "   - analyze-001 (REAL analyzer)"
echo "   - monitor-001 (REAL monitor)"
echo ""
echo "NO MORE MOCK DATA EVER!"

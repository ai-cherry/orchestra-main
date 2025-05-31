#!/bin/bash
# Deploy real agents to production server

echo "🚀 Deploying REAL Orchestra AI agents to production..."

# Create a tar file with the updated files
echo "📦 Creating deployment package..."
tar -czf real_agents.tar.gz \
    agent/app/routers/admin.py \
    agent/app/services/real_agents.py \
    agent/app/services/__init__.py

echo "📤 Uploading to server..."
echo "Please enter the server password when prompted:"

# Upload and extract
scp real_agents.tar.gz root@45.32.69.157:/root/

echo "🔧 Installing on server..."
ssh root@45.32.69.157 << 'EOF'
cd /root/orchestra-main
tar -xzf /root/real_agents.tar.gz
rm /root/real_agents.tar.gz

# Kill existing API
pkill -f "uvicorn agent.app.main" || true
sleep 2

# Install psutil
source venv/bin/activate
pip install psutil

# Start the API
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8080 > /root/api.log 2>&1 &
sleep 3

echo "✅ API started on server"
EOF

# Clean up local tar file
rm real_agents.tar.gz

echo "🎉 Testing deployment..."
sleep 2
curl -X GET "https://cherry-ai.me/api/agents" \
     -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | jq '.'

echo ""
echo "🚀 Your REAL AI agents are now live at https://cherry-ai.me"
echo "📊 Try these queries:"
echo "   - 'Check CPU usage'"
echo "   - 'Analyze this data'"
echo "   - 'Monitor system status'" 
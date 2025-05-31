#!/bin/bash
# Deploy real agents to production server

SERVER="45.32.69.157"
SSH_USER="root"

echo "🚀 Deploying REAL Orchestra AI agents to production..."

# Kill any existing API process on server
echo "⏹️  Stopping existing API..."
sshpass -p 'vultr-server-password' ssh -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER} "pkill -f 'uvicorn agent.app.main' || true"

# Copy the updated files
echo "📦 Copying agent files..."
sshpass -p 'vultr-server-password' scp -o StrictHostKeyChecking=no agent/app/routers/admin.py ${SSH_USER}@${SERVER}:/root/orchestra-main/agent/app/routers/
sshpass -p 'vultr-server-password' scp -o StrictHostKeyChecking=no agent/app/services/real_agents.py ${SSH_USER}@${SERVER}:/root/orchestra-main/agent/app/services/
sshpass -p 'vultr-server-password' scp -o StrictHostKeyChecking=no agent/app/services/__init__.py ${SSH_USER}@${SERVER}:/root/orchestra-main/agent/app/services/

# Install psutil on server
echo "📦 Installing dependencies..."
sshpass -p 'vultr-server-password' ssh -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER} "cd /root/orchestra-main && source venv/bin/activate && pip install psutil"

# Start the API
echo "🔥 Starting REAL Orchestra AI API..."
sshpass -p 'vultr-server-password' ssh -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER} "cd /root/orchestra-main && source venv/bin/activate && nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8080 > /root/api.log 2>&1 &"

sleep 3

# Test the API
echo "✅ Testing API..."
curl -X GET "https://cherry-ai.me/api/agents" -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | jq '.'

echo "🎉 Deployment complete! Your REAL AI agents are now live at https://cherry-ai.me" 
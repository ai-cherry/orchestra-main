#!/bin/bash
# Direct deployment instructions

echo "🚀 REAL Agent Deployment - Manual Steps"
echo "======================================="
echo ""
echo "Since SSH is having issues, here's what you need to do:"
echo ""
echo "1. First, let's create the files locally and test:"

# Test locally first
echo "Testing real agents locally..."
cd /home/paperspace/orchestra-main
pkill -f "uvicorn" || true
sleep 1

source venv/bin/activate
pip install psutil > /dev/null 2>&1
python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8001 &
API_PID=$!

sleep 3

echo ""
echo "Local test:"
curl -s -X GET "http://localhost:8001/api/agents" \
     -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | jq '.[0]'

echo ""
echo "✅ If you see real agent data above (with agent IDs like sys-001), it's working!"
echo ""
echo "2. Now copy these commands and run them on your server:"
echo ""
echo "ssh root@45.32.69.157"
echo ""
echo "Then run:"
echo "----------------------------------------"
cat << 'REMOTE_COMMANDS'
cd /root/orchestra-main

# Create the services directory if it doesn't exist
mkdir -p agent/app/services

# Kill old API
pkill -f "uvicorn agent.app.main" || true
sleep 2

# Install psutil
source venv/bin/activate
pip install psutil

# You'll need to manually copy the content of these files:
# - agent/app/routers/admin.py
# - agent/app/services/real_agents.py
# - agent/app/services/__init__.py

# Start the new API
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8080 > /root/api_real.log 2>&1 &

# Test it
sleep 3
curl -X GET "http://localhost:8080/api/agents" -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
REMOTE_COMMANDS
echo "----------------------------------------"

kill $API_PID 2>/dev/null 
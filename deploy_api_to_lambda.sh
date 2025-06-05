#!/bin/bash

echo "🚀 Deploying Cherry AI API Server to Lambda Labs"
echo "=============================================="

SERVER_IP="150.136.94.139"
USERNAME="ubuntu"

# Copy the API server file
echo "1. Copying API server to Lambda Labs..."
scp cherry_api_server.py $USERNAME@$SERVER_IP:/opt/orchestra/

# Install dependencies and start the server
echo -e "\n2. Installing dependencies and starting API server..."
ssh $USERNAME@$SERVER_IP << 'EOF'
cd /opt/orchestra

# Install FastAPI and uvicorn if not already installed
echo "Installing dependencies..."
sudo pip3 install fastapi uvicorn pydantic

# Stop any existing API server
echo "Stopping existing API server if running..."
sudo pkill -f "cherry_api_server.py" || true

# Start the API server in the background
echo "Starting Cherry AI API Server..."
nohup sudo python3 cherry_api_server.py > /var/log/cherry_api.log 2>&1 &

# Wait a moment for the server to start
sleep 3

# Check if it's running
if pgrep -f "cherry_api_server.py" > /dev/null; then
    echo "✅ API Server started successfully"
else
    echo "❌ Failed to start API server"
    echo "Check logs at: /var/log/cherry_api.log"
fi

# Test the API
echo -e "\nTesting API endpoints..."
curl -s http://localhost:8000/ | jq '.' || echo "API not responding"
EOF

echo -e "\n3. Testing from local machine..."
curl -s http://$SERVER_IP:8000/api/agents | jq '.' || echo "Cannot reach API from local"

echo -e "\n=============================================="
echo "✅ Deployment complete!"
echo "API Server: http://$SERVER_IP:8000"
echo "Orchestrator UI: http://$SERVER_IP/orchestrator/"
echo "=============================================="
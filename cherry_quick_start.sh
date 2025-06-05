#!/bin/bash
# Cherry AI Quick Start - Deploy MCP servers and Cherry interface

echo "🍒 Cherry AI Quick Start - Lambda Labs Deployment"

# Check if we're on Lambda Labs
if [[ $HOSTNAME == *"lambda-"* ]] || [[ -d "/opt/cherry-ai" ]]; then
    echo "✅ Running on Lambda Labs"
    cd /opt/cherry-ai
else
    echo "ℹ️  Running locally"
fi

# Set environment variables
export POSTGRES_URL="postgresql://cherry_ai:CherryAI2024!@localhost:5432/cherry_ai"
export REDIS_URL="redis://localhost:6379"
export WEAVIATE_URL="http://localhost:8080"
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Install dependencies if needed
echo "📦 Installing minimal dependencies..."
pip install -q fastapi uvicorn asyncio mcp

# Start databases if not running
echo "🗄️  Starting databases..."
sudo systemctl start postgresql redis-server || true

# Check if Weaviate is running, start if needed
if ! curl -s http://localhost:8080/v1/meta >/dev/null 2>&1; then
    echo "🚀 Starting Weaviate..."
    docker run -d --name weaviate -p 8080:8080 \
        -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        semitechnologies/weaviate:latest || true
fi

# Kill any existing MCP processes
echo "🔄 Stopping existing MCP servers..."
pkill -f "memory_server\|tools_server" || true

# Create logs directory
mkdir -p logs

# Start Memory MCP Server
echo "🧠 Starting Memory MCP Server on port 8003..."
nohup python3 -m mcp_server.servers.memory_server > logs/memory_server.log 2>&1 &
echo $! > logs/memory_server.pid
sleep 2

# Start Tools MCP Server
echo "🛠️  Starting Tools MCP Server on port 8006..."
nohup python3 -m mcp_server.servers.tools_server > logs/tools_server.log 2>&1 &
echo $! > logs/tools_server.pid
sleep 2

# Start Enhanced Cherry Interface
echo "🍒 Starting Cherry AI Interface..."
python3 main.py &
echo $! > logs/cherry_interface.pid

echo ""
echo "🎉 Cherry AI is starting up!"
echo ""
echo "📍 Access Points:"
echo "   Cherry Interface: http://cherry-ai.me"
echo "   Memory MCP:       http://localhost:8003"
echo "   Tools MCP:        http://localhost:8006"
echo ""
echo "📋 Quick Commands:"
echo "   Check status:     curl http://localhost:8003/health"
echo "   View logs:        tail -f logs/*.log"
echo "   Stop all:         pkill -f 'memory_server|tools_server|main.py'"
echo ""

# Test MCP servers
sleep 5
echo "🧪 Testing MCP servers..."
if curl -s http://localhost:8003/health >/dev/null 2>&1; then
    echo "   ✅ Memory MCP Server: Running"
else
    echo "   ❌ Memory MCP Server: Failed"
    echo "      Check logs: tail logs/memory_server.log"
fi

if curl -s http://localhost:8006/health >/dev/null 2>&1; then
    echo "   ✅ Tools MCP Server: Running"
else
    echo "   ❌ Tools MCP Server: Failed"
    echo "      Check logs: tail logs/tools_server.log"
fi

echo ""
echo "🍒 Cherry AI is ready! Visit http://cherry-ai.me" 
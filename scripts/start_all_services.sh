#!/bin/bash
# Start all Orchestra AI services

echo "🎼 Starting Orchestra AI Services..."
echo "=================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "✓ Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start MCP servers in background
echo ""
echo "🚀 Starting MCP servers..."

# Function to start a server
start_server() {
    local name=$1
    local script=$2
    local port=$3
    
    echo -n "  Starting $name server on port $port... "
    
    # Use python3 explicitly
    nohup python3 $script > logs/mcp_${name}.log 2>&1 &
    local pid=$!
    
    # Check if process started
    sleep 1
    if ps -p $pid > /dev/null; then
        echo "✓ (PID: $pid)"
        echo $pid > logs/mcp_${name}.pid
    else
        echo "✗ Failed"
    fi
}

# Create logs directory
mkdir -p logs

# Start each server
start_server "orchestrator" "mcp_server/servers/orchestrator_server.py" "${MCP_ORCHESTRATOR_PORT:-8002}"
start_server "memory" "mcp_server/servers/memory_server.py" "${MCP_MEMORY_PORT:-8003}"
start_server "tools" "mcp_server/servers/tools_server.py" "${MCP_TOOLS_PORT:-8006}"
start_server "weaviate" "mcp_server/servers/weaviate_direct_mcp_server.py" "${MCP_WEAVIATE_DIRECT_PORT:-8001}"

# Wait for services to start
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 3

# Check service health
echo ""
echo "🔍 Checking service health..."
python3 scripts/health_check.py

echo ""
echo "=================================="
echo "✅ Orchestra AI services started!"
echo ""
echo "📋 Quick Commands:"
echo "  • Check status: ./scripts/check_services.sh"
echo "  • View logs: tail -f logs/mcp_*.log"
echo "  • Stop all: ./scripts/stop_all_services.sh"
echo "  • Use CLI: python3 ai_components/orchestrator_cli_enhanced.py"
echo ""
echo "🎯 The Orchestra is ready to play! 🎵"
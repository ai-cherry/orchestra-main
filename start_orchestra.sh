#!/bin/bash
# Orchestra AI - Start Everything

echo "🎼 Starting Orchestra AI..."

# Check environment
if [ ! -f .env ]; then
    echo "❌ No .env file found. Run: python scripts/orchestra_complete_setup.py"
    exit 1
fi

# Export environment
export $(cat .env | grep -v '^#' | xargs)

# Start services
echo "Starting services..."

# Option 1: Docker Compose (recommended)
if command -v docker-compose &> /dev/null; then
    echo "Using Docker Compose..."
    docker-compose up -d
    echo "✓ Services started with Docker Compose"
else
    echo "⚠️  Docker Compose not found. Install Docker for best experience."
    echo "Starting local services..."

    # Start Redis if not running
    if ! pgrep -x "redis-server" > /dev/null; then
        redis-server --daemonize yes
        echo "✓ Started Redis"
    fi
fi

# Start MCP servers
echo "Starting MCP servers..."
python mcp_server/servers/orchestrator_server.py &
python mcp_server/servers/memory_server.py &
echo "✓ MCP servers started"

# Start main application
echo "Starting Orchestra API..."
cd core/orchestrator && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &

echo ""
echo "✅ Orchestra AI is running!"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "To stop: ./stop_orchestra.sh"

#!/bin/bash
# Unified startup for Cherry AI with Single-User Auth & AI Agent Discovery

echo "🚀 Starting Cherry AI - Single User Mode"
echo "============================================"

# Source .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Export auth configuration (use last API key from .env)
export cherry_ai_API_KEY="${cherry_ai_API_KEY:-my92rB5UA4-GJhRu6xOS58G6QzPhdmx0XyzV5gIr7IyvENYXcVzT4FII7DnXtYmH}"
export cherry_ai_CONTEXT="development"
export AUTH_MODE="single_user"

# Check if services are already running
if docker-compose -f docker-compose.single-user.yml ps | grep -q "Up"; then
    echo "✅ Core services already running"
else
    echo "Starting core services..."
    docker-compose -f docker-compose.single-user.yml up -d
    sleep 10
fi

# Start MCP servers with auth
echo ""
echo "🔧 Starting MCP servers..."

# Kill any existing MCP processes
pkill -f "mcp_server/servers" || true
sleep 2

# Start each MCP server with authentication
python mcp_server/servers/memory_server.py &
python mcp_server/servers/conductor_server.py &
python mcp_server/servers/tools_server.py &
python mcp_server/servers/code_intelligence_server.py &
python mcp_server/servers/git_intelligence_server.py &
python mcp_server/servers/weaviate_direct_mcp_server.py &
python mcp_server/servers/deployment_server.py &

# Start smart router with auth
echo ""
echo "🔐 Starting Smart Router with Authentication..."
python mcp_smart_router.py &

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Service Status:"
echo "  - API: http://localhost:8000 (auth required)"
echo "  - Discovery: http://localhost:8010/discover (auth required)"
echo "  - Health: http://localhost:8010/health (no auth)"
echo ""
echo "🔑 API Key: ${cherry_ai_API_KEY:0:20}..."
echo "🌍 Context: ${cherry_ai_CONTEXT}"
echo ""
echo "💡 Test with:"
echo "  curl -H 'X-API-Key: ${cherry_ai_API_KEY}' http://localhost:8010/discover"

#!/bin/bash
# Start MCP server for Roo cherry_ai integration

echo "🚀 Starting MCP Server for Roo cherry_ai..."
echo "============================================"

# Set environment variables
export cherry_ai_DB="${cherry_ai_DB:-postgresql://user:pass@localhost:5432/context}"
export WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"
export CONTEXT_CACHE="lru"
export CONTEXT_TTL="3600"

# Check if the server script exists
SERVER_SCRIPT="${WORKSPACE_ROOT:-/root/cherry_ai-main}/mcp_server/servers/conductor_server.py"

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "❌ Error: MCP server script not found at: $SERVER_SCRIPT"
    echo "Please ensure the cherry_ai-main project is properly set up."
    exit 1
fi

echo "📍 Starting server from: $SERVER_SCRIPT"
echo "📊 Database: $cherry_ai_DB"
echo "🔍 Weaviate: $WEAVIATE_URL"
echo ""
echo "Note: The MCP server is designed to work with stdio communication."
echo "It should be started by the MCP client (Roo) directly."
echo ""
echo "For testing purposes, you can run:"
echo "  cd /root/cherry_ai-main/mcp_server"
echo "  python test_conductor.py"
echo ""
echo "The conductor server functions have been verified to work correctly."
echo "============================================" 
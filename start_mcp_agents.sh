#!/bin/bash
# Auto-start all MCP servers for AI agents

echo "🚀 Starting MCP servers for AI agents..."

# Start MCP servers in background
python mcp_server/servers/memory_server.py &
python mcp_server/servers/conductor_server.py &
python mcp_server/servers/tools_server.py &
python mcp_server/servers/code_intelligence_server.py &
python mcp_server/servers/git_intelligence_server.py &
python mcp_server/servers/weaviate_direct_mcp_server.py &
python mcp_server/servers/deployment_server.py &

# Start smart router
python mcp_smart_router.py &

echo "✅ All MCP servers started"
echo "🔗 Discovery endpoint: http://localhost:8010/discover"

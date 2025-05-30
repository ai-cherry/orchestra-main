#!/bin/bash
# Stop Orchestra AI System on DigitalOcean Droplet

echo "🛑 Stopping Orchestra AI System..."

# Stop API server
if [ -f /var/run/orchestra-api.pid ]; then
    API_PID=$(cat /var/run/orchestra-api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "Stopping API server (PID: $API_PID)..."
        kill $API_PID
        rm /var/run/orchestra-api.pid
    fi
fi

# Stop MCP server
if [ -f /var/run/orchestra-mcp.pid ]; then
    MCP_PID=$(cat /var/run/orchestra-mcp.pid)
    if kill -0 $MCP_PID 2>/dev/null; then
        echo "Stopping MCP server (PID: $MCP_PID)..."
        kill $MCP_PID
        rm /var/run/orchestra-mcp.pid
    fi
fi

# Optional: Stop Weaviate (comment out if you want to keep it running)
# echo "Stopping Weaviate..."
# cd /opt && docker-compose -f weaviate-compose.yml down

echo "✅ Orchestra AI System stopped"

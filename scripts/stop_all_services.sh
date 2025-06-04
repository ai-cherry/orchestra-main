#!/bin/bash
# Stop all Cherry AI services

echo "🛑 Stopping Cherry AI Services..."
echo "=================================="

# Stop MCP servers
echo "Stopping MCP servers..."

for pidfile in logs/mcp_*.pid; do
    if [ -f "$pidfile" ]; then
        service=$(basename "$pidfile" .pid | sed 's/mcp_//')
        pid=$(cat "$pidfile")
        
        if ps -p $pid > /dev/null 2>&1; then
            echo "  Stopping $service server (PID: $pid)..."
            kill $pid
            rm "$pidfile"
        else
            echo "  $service server not running"
            rm "$pidfile"
        fi
    fi
done

# Also kill any remaining python processes running MCP servers
echo ""
echo "Cleaning up any remaining processes..."
pkill -f "mcp_server/servers" 2>/dev/null

echo ""
echo "✅ All services stopped"
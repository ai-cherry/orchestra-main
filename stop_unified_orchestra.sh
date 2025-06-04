#!/bin/bash
# Stop Unified Orchestra System

echo "🛑 Stopping Unified Orchestra System..."
echo "=================================="

# Stop MCP servers
echo "Stopping MCP servers..."

for pidfile in logs/mcp_*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping process $pid..."
            kill $pid
            rm "$pidfile"
        fi
    fi
done

# Stop Docker services
if [ -f docker-compose.production.yml ]; then
    COMPOSE_FILE="docker-compose.production.yml"
else
    COMPOSE_FILE="docker-compose.local.yml"
fi

echo "Stopping Docker services..."
docker-compose -f $COMPOSE_FILE down

echo "✅ All services stopped"
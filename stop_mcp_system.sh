#!/bin/bash
# MCP System Stop Script - PostgreSQL + Weaviate ONLY

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log directory
LOG_DIR="$HOME/.mcp/logs"

echo -e "${YELLOW}Stopping MCP System Components...${NC}"

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file="$LOG_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            echo -e "${GREEN}✓ Stopped $name (PID: $pid)${NC}"
        else
            echo -e "${YELLOW}$name not running (stale PID file)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}$name not running (no PID file)${NC}"
    fi
}

# Stop all MCP services
stop_service "Memory MCP"
stop_service "Orchestrator MCP"
stop_service "Tools MCP"
stop_service "Weaviate Direct MCP"

# Clean up any orphaned processes on MCP ports
for port in 8001 8002 8003 8006; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}Cleaning up process on port $port${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}MCP System stopped${NC}"

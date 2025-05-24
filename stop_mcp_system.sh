#!/bin/bash
# Stop all MCP System Components

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_DIR="/var/log/mcp"

echo -e "${BLUE}Stopping MCP System Components...${NC}"

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file="$LOG_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill $pid
            rm -f "$pid_file"
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${YELLOW}$name not running (stale PID file)${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}$name not running (no PID file)${NC}"
    fi
}

# Stop all services
stop_service "MCP Gateway"
stop_service "Cloud Run MCP"
stop_service "Secrets MCP"
stop_service "Memory MCP"
stop_service "Orchestrator MCP"

# Also check for any processes on the known ports
for port in 8000 8001 8002 8003 8004; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}Cleaning up process on port $port${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}MCP System stopped${NC}"
#!/bin/bash

# Stop MCP Servers
# This script stops all running MCP servers

echo "🛑 Stopping cherry_ai MCP Servers..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to stop server by PID file
stop_server() {
    local name=$1
    local pidfile=$2
    
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo -e "${GREEN}✅ Stopped $name (PID: $PID)${NC}"
            rm "$pidfile"
        else
            echo -e "${BLUE}ℹ️  $name was not running${NC}"
            rm "$pidfile"
        fi
    else
        echo -e "${BLUE}ℹ️  No PID file found for $name${NC}"
    fi
}

# Stop all servers
stop_server "conductor Server" "/tmp/mcp_conductor.pid"
stop_server "Memory Server" "/tmp/mcp_memory.pid"
stop_server "Tools Server" "/tmp/mcp_tools.pid"

# Also kill any remaining python processes running MCP servers
echo -e "\n${BLUE}Checking for any remaining MCP processes...${NC}"
pkill -f "mcp_server/servers/conductor_server.py" 2>/dev/null && echo -e "${GREEN}✅ Killed remaining conductor processes${NC}"
pkill -f "mcp_server/servers/memory_server.py" 2>/dev/null && echo -e "${GREEN}✅ Killed remaining memory processes${NC}"
pkill -f "mcp_server/servers/tools_server.py" 2>/dev/null && echo -e "${GREEN}✅ Killed remaining tools processes${NC}"

echo -e "\n${GREEN}🎯 All MCP servers stopped${NC}" 
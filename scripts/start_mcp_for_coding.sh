#!/bin/bash

# Start MCP Servers for AI Coding Assistance
# This script starts all necessary MCP servers for use with Cursor/AI coders

echo "🚀 Starting Orchestra MCP Servers for AI Coding..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

# Check required ports
echo -e "${BLUE}Checking ports...${NC}"
PORTS=(8002 8003 8006)
for port in "${PORTS[@]}"; do
    if ! check_port $port; then
        echo "Please free up port $port before running this script"
        exit 1
    fi
done

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if databases are accessible
echo -e "${BLUE}Checking database connections...${NC}"
python -c "from shared.database import UnifiedDatabase; db = UnifiedDatabase(); print('✅ Database connections OK') if db.health_check()['overall'] else print('❌ Database connection failed')" 2>/dev/null || {
    echo -e "${RED}⚠️  Warning: Database connections might not be configured${NC}"
    echo "Please ensure PostgreSQL and Weaviate are running and configured in .env"
}

# Start MCP servers in background
echo -e "${GREEN}Starting MCP servers...${NC}"

# Orchestrator Server
echo -e "${BLUE}Starting Orchestrator Server (port 8002)...${NC}"
nohup python mcp_server/servers/orchestrator_server.py > /tmp/mcp_orchestrator.log 2>&1 &
echo $! > /tmp/mcp_orchestrator.pid
sleep 2

# Memory Server
echo -e "${BLUE}Starting Memory Server (port 8003)...${NC}"
nohup python mcp_server/servers/memory_server.py > /tmp/mcp_memory.log 2>&1 &
echo $! > /tmp/mcp_memory.pid
sleep 2

# Tools Server
echo -e "${BLUE}Starting Tools Server (port 8006)...${NC}"
nohup python mcp_server/servers/tools_server.py > /tmp/mcp_tools.log 2>&1 &
echo $! > /tmp/mcp_tools.pid
sleep 2

# Verify servers are running
echo -e "${BLUE}Verifying servers...${NC}"
sleep 3

SERVERS_OK=true
if ! lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Orchestrator Server failed to start${NC}"
    SERVERS_OK=false
else
    echo -e "${GREEN}✅ Orchestrator Server running on port 8002${NC}"
fi

if ! lsof -Pi :8003 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Memory Server failed to start${NC}"
    SERVERS_OK=false
else
    echo -e "${GREEN}✅ Memory Server running on port 8003${NC}"
fi

if ! lsof -Pi :8006 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Tools Server failed to start${NC}"
    SERVERS_OK=false
else
    echo -e "${GREEN}✅ Tools Server running on port 8006${NC}"
fi

if [ "$SERVERS_OK" = true ]; then
    echo -e "\n${GREEN}🎉 All MCP servers started successfully!${NC}"
    echo -e "\n${BLUE}Server logs available at:${NC}"
    echo "  - Orchestrator: /tmp/mcp_orchestrator.log"
    echo "  - Memory: /tmp/mcp_memory.log"
    echo "  - Tools: /tmp/mcp_tools.log"
    echo -e "\n${BLUE}To stop servers, run:${NC}"
    echo "  ./scripts/stop_mcp_servers.sh"
    echo -e "\n${GREEN}Ready for AI coding assistance! 🤖${NC}"
else
    echo -e "\n${RED}⚠️  Some servers failed to start. Check logs for details.${NC}"
    exit 1
fi 
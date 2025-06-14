#!/bin/bash

# Simple Orchestra AI Startup Script
# This script starts the essential services without complex dependency checks

echo "🎼 Starting Orchestra AI (Simple Mode)"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to find an available port
find_available_port() {
    local base_port=$1
    local port=$base_port
    while check_port $port; do
        echo -e "${YELLOW}Port $port is in use, trying $((port+1))...${NC}"
        port=$((port+1))
    done
    echo $port
}

# Kill any existing processes using our ports
echo -e "${BLUE}Checking for existing processes...${NC}"
for port in 8000 3000 8003; do
    if check_port $port; then
        echo -e "${YELLOW}Killing process on port $port...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
done

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Virtual environment not found! Please run: python3 -m venv venv${NC}"
    exit 1
fi

# Start API server in development mode
echo -e "${BLUE}Starting API server (simplified)...${NC}"
if [ -f "api/main_simple.py" ]; then
    cd api
    python main_simple.py &
    API_PID=$!
    cd ..
    echo -e "${GREEN}✅ API server started (PID: $API_PID)${NC}"
else
    echo -e "${YELLOW}⚠️  No simple API server found, skipping...${NC}"
fi

# Start frontend
echo -e "${BLUE}Starting frontend...${NC}"
if [ -d "web" ]; then
    cd web
    # Find available port starting from 3000
    FRONTEND_PORT=$(find_available_port 3000)
    PORT=$FRONTEND_PORT npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Frontend started on port $FRONTEND_PORT (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${YELLOW}⚠️  No frontend found, skipping...${NC}"
fi

# Start MCP memory server (if it exists)
if [ -f "mcp_servers/memory_management_server.py" ]; then
    echo -e "${BLUE}Starting MCP memory server...${NC}"
    cd mcp_servers
    MCP_PORT=$(find_available_port 8003)
    uvicorn memory_management_server:app --host 0.0.0.0 --port $MCP_PORT &
    MCP_PID=$!
    cd ..
    echo -e "${GREEN}✅ MCP server started on port $MCP_PORT (PID: $MCP_PID)${NC}"
fi

# Create a stop script
cat > stop_orchestra_simple.sh << 'EOF'
#!/bin/bash
echo "Stopping Orchestra AI services..."

# Kill processes by port
for port in 8000 8001 8002 3000 3001 3002 3003 8003 8004; do
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
done

echo "✅ All services stopped"
EOF
chmod +x stop_orchestra_simple.sh

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Orchestra AI Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services running:"
echo "  - API: http://localhost:8000"
echo "  - Frontend: http://localhost:$FRONTEND_PORT"
if [ ! -z "$MCP_PORT" ]; then
    echo "  - MCP Server: http://localhost:$MCP_PORT"
fi
echo ""
echo "To stop all services, run: ./stop_orchestra_simple.sh"
echo ""
echo -e "${YELLOW}Note: This is a simplified startup without database connections.${NC}"
echo -e "${YELLOW}For full functionality, ensure PostgreSQL and Redis are running.${NC}" 
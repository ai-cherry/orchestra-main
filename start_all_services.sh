#!/bin/bash

# Orchestra AI - Start All Services
# This script starts all required services for the AI-optimized platform

echo "🎼 Starting Orchestra AI Services..."
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Kill existing processes on our ports
echo "🔧 Cleaning up existing processes..."
for port in 8000 8003 8004 8005 3000; do
    if check_port $port; then
        echo "   Killing process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null
    fi
done

sleep 2

# Start API Server
echo -e "${YELLOW}Starting API Server on port 8000...${NC}"
python main_simple.py > logs/api.log 2>&1 &
API_PID=$!
sleep 3

# Start AI Context Service
echo -e "${YELLOW}Starting AI Context Service on port 8005...${NC}"
cd .ai-context
python context_service.py > ../logs/context_service.log 2>&1 &
CONTEXT_PID=$!
cd ..
sleep 2

# Start Portkey MCP Server
echo -e "${YELLOW}Starting Portkey MCP Server on port 8004...${NC}"
cd packages/mcp-enhanced
python portkey_mcp.py > ../../logs/portkey_mcp.log 2>&1 &
PORTKEY_PID=$!
cd ../..
sleep 2

# Start MCP Memory Server
echo -e "${YELLOW}Starting MCP Memory Server on port 8003...${NC}"
cd mcp_servers
python memory_management_server.py > ../logs/mcp_memory.log 2>&1 &
MEMORY_PID=$!
cd ..
sleep 2

# Start Frontend
echo -e "${YELLOW}Starting Frontend on port 3000...${NC}"
cd web
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="

# Function to check service
check_service() {
    local name=$1
    local port=$2
    local pid=$3
    
    if check_port $port && kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $name (port $port) - Running (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ $name (port $port) - Failed${NC}"
        return 1
    fi
}

# Check all services
SERVICES_OK=true
check_service "API Server" 8000 $API_PID || SERVICES_OK=false
check_service "AI Context Service" 8005 $CONTEXT_PID || SERVICES_OK=false
check_service "Portkey MCP Server" 8004 $PORTKEY_PID || SERVICES_OK=false
check_service "MCP Memory Server" 8003 $MEMORY_PID || SERVICES_OK=false
check_service "Frontend" 3000 $FRONTEND_PID || SERVICES_OK=false

echo ""

# Test endpoints
if [ "$SERVICES_OK" = true ]; then
    echo "🧪 Testing Endpoints:"
    echo "===================="
    
    # Test API
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo -e "${GREEN}✅ API Health Check - OK${NC}"
    else
        echo -e "${RED}❌ API Health Check - Failed${NC}"
    fi
    
    # Test Context Service
    if curl -s http://localhost:8005/health > /dev/null; then
        echo -e "${GREEN}✅ Context Service Health Check - OK${NC}"
    else
        echo -e "${RED}❌ Context Service Health Check - Failed${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 All services started successfully!${NC}"
    echo ""
    echo "📝 Service URLs:"
    echo "  - API:             http://localhost:8000"
    echo "  - Frontend:        http://localhost:3000"
    echo "  - Context Service: http://localhost:8005"
    echo "  - Portkey MCP:     http://localhost:8004"
    echo "  - MCP Memory:      http://localhost:8003"
    echo ""
    echo "📋 Logs available in: ./logs/"
    echo ""
    echo "To stop all services, run: pkill -f 'python|node'"
else
    echo -e "${RED}⚠️ Some services failed to start. Check logs for details.${NC}"
    exit 1
fi 
#!/bin/bash

# 🎼 Orchestra AI Complete Startup Script
# Starts all services and verifies deployment

echo "🎼 Starting Orchestra AI Complete System..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service (port $port) - Running${NC}"
        return 0
    else
        echo -e "${RED}❌ $service (port $port) - Not running${NC}"
        return 1
    fi
}

# Function to start a service and wait
start_service() {
    local command=$1
    local service_name=$2
    local port=$3
    local wait_time=${4:-10}
    
    echo -e "${YELLOW}🚀 Starting $service_name...${NC}"
    eval "$command" &
    local pid=$!
    
    # Wait for service to start
    for i in $(seq 1 $wait_time); do
        if lsof -i :$port > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name started successfully${NC}"
            return 0
        fi
        echo "⏳ Waiting for $service_name... ($i/$wait_time)"
        sleep 1
    done
    
    echo -e "${RED}❌ $service_name failed to start${NC}"
    return 1
}

# Kill any existing services
echo "🔄 Stopping existing services..."
pkill -f "uvicorn\|node.*dev" > /dev/null 2>&1

# Activate virtual environment
echo "🐍 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi

# Start MCP Memory Server
start_service "cd mcp_servers && uvicorn memory_management_server:app --host 0.0.0.0 --port 8003" "MCP Memory Server" 8003 15

# Start API Server
start_service "cd api && uvicorn main:app --host 0.0.0.0 --port 8000" "API Server" 8000 15

# Start Frontend
start_service "cd web && npm run dev" "Frontend" 3002 20

echo ""
echo "🎯 Verifying all services..."
echo "=========================="

# Check all services
all_running=true

if ! check_port 8003 "MCP Memory Server"; then
    all_running=false
fi

if ! check_port 8000 "API Server"; then
    all_running=false
fi

if ! check_port 3002 "Frontend"; then
    all_running=false
fi

echo ""
if [ "$all_running" = true ]; then
    echo -e "${GREEN}🎉 All services running successfully!${NC}"
    echo ""
    echo "🌐 Access Points:"
    echo "  Admin Interface: http://localhost:3002/real-admin.html"
    echo "  API Health:      http://localhost:8000/api/health"
    echo "  MCP Memory:      http://localhost:8003/health"
    echo "  Frontend:        http://localhost:3002"
    echo ""
    echo "🧠 Cursor Integration:"
    echo "  MCP Memory Server is active on port 8003"
    echo "  Your conversations and code context are being stored"
    echo "  Check claude_mcp_config.json for configuration"
    echo ""
    echo -e "${YELLOW}📖 See ORCHESTRA_AI_CURSOR_INTEGRATION.md for complete guide${NC}"
    
    # Test API health
    echo ""
    echo "🔍 Quick health check..."
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API Server responding${NC}"
    else
        echo -e "${YELLOW}⚠️  API Server starting up...${NC}"
    fi
    
    if curl -s http://localhost:8003/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ MCP Memory Server responding${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP Memory Server starting up...${NC}"
    fi
    
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    echo "Check the logs above for details"
    exit 1
fi

echo ""
echo -e "${GREEN}🎼 Orchestra AI is ready for development!${NC}" 
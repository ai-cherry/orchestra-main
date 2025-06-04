#!/bin/bash
# Test Local Deployment Script

echo "🚀 Testing Local Cherry AI Deployment"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check PostgreSQL
echo -e "\n📊 Checking PostgreSQL..."
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL is running"
else
    echo -e "${RED}✗${NC} PostgreSQL is not running"
    echo "Please start PostgreSQL: sudo systemctl start postgresql"
    exit 1
fi

# Check Redis
echo -e "\n💾 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is running"
else
    echo -e "${RED}✗${NC} Redis is not running"
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Create logs directory
mkdir -p logs

# Start MCP servers
echo -e "\n🔌 Starting MCP Servers..."

# Start each MCP server
for server in conductor memory weaviate_direct tools deployment; do
    server_file="mcp_server/servers/${server}_server.py"
    if [ -f "$server_file" ]; then
        echo "Starting ${server} server..."
        nohup venv/bin/python3 "$server_file" > "logs/mcp_${server}.log" 2>&1 &
        echo $! > "logs/mcp_${server}.pid"
        echo -e "${GREEN}✓${NC} Started ${server} server"
    else
        echo -e "${YELLOW}⚠${NC} ${server}_server.py not found"
    fi
done

# Wait for services to start
echo -e "\n⏳ Waiting for services to start..."
sleep 5

# Check if services are running
echo -e "\n🔍 Verifying Services..."

# Function to check service
check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding"
        return 1
    fi
}

# Check each service
all_good=true

check_service "MCP conductor" "http://localhost:8002/health" || all_good=false
check_service "MCP Memory" "http://localhost:8003/health" || all_good=false

# Summary
echo -e "\n========================================"
if $all_good; then
    echo -e "${GREEN}✅ Local deployment is working!${NC}"
    echo -e "\n📝 Services are running. To stop them:"
    echo "pkill -f 'mcp_server/servers'"
    echo -e "\nView logs in: ./logs/"
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    echo "Check logs in ./logs/ for details"
fi

echo -e "\n🎯 To deploy to Vultr:"
echo "1. Set environment variables:"
echo "   export VULTR_API_KEY='your-key'"
echo "   export PULUMI_ACCESS_TOKEN='your-token'"
echo "2. Run: cd infrastructure && pulumi up"
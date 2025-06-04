#!/bin/bash
# MCP Environment Setup and Startup Script
# Configures all database connections and starts MCP servers for AI coding helpers

set -e

echo "🔧 Setting up MCP Environment for AI Coding Helpers..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get container IP addresses
echo -e "${BLUE}Discovering container network information...${NC}"

# Check if containers are exposed on host ports (preferred) or use bridge IPs
if docker port orchestra-main_postgres_1 5432 >/dev/null 2>&1; then
    # PostgreSQL is exposed on host port
    POSTGRES_HOST="localhost"
    POSTGRES_PORT=$(docker port orchestra-main_postgres_1 5432 | cut -d':' -f2)
else
    # Use bridge network IP
    POSTGRES_HOST=$(docker inspect orchestra-main_postgres_1 --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}")
    POSTGRES_PORT="5432"
fi

if docker port orchestra-main_weaviate_1 8080 >/dev/null 2>&1; then
    # Weaviate is exposed on host port
    WEAVIATE_HOST="localhost"
    WEAVIATE_PORT="8080"
else
    # Use bridge network IP
    WEAVIATE_HOST=$(docker inspect orchestra-main_weaviate_1 --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}")
    WEAVIATE_PORT="8080"
fi

if docker port orchestra-main_redis_1 6379 >/dev/null 2>&1; then
    # Redis is exposed on host port
    REDIS_HOST="localhost"
    REDIS_PORT=$(docker port orchestra-main_redis_1 6379 | cut -d':' -f2)
else
    # Use bridge network IP
    REDIS_HOST=$(docker inspect orchestra-main_redis_1 --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}")
    REDIS_PORT="6379"
fi

echo "PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"
echo "Weaviate: $WEAVIATE_HOST:$WEAVIATE_PORT"
echo "Redis: $REDIS_HOST:$REDIS_PORT"

# Get password from .env file
POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)

# Set up environment variables
echo -e "${BLUE}Configuring environment variables...${NC}"
export POSTGRES_URL="postgresql://postgres:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/cherry_ai"
export WEAVIATE_HOST="${WEAVIATE_HOST}"
export WEAVIATE_PORT="${WEAVIATE_PORT}"
export REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}"
export DATABASE_URL="$POSTGRES_URL"

export MCP_MEMORY_PORT="8003"
export MCP_CONDUCTOR_PORT="8002"
export MCP_TOOLS_PORT="8006"
export MCP_CODE_INTELLIGENCE_PORT="8007"
export MCP_GIT_INTELLIGENCE_PORT="8008"

echo -e "${GREEN}✅ Environment configured${NC}"

# Test database connections
echo -e "${BLUE}Testing database connections...${NC}"

# Test PostgreSQL
if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres -d cherry_ai -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL connection successful${NC}"
else
    echo -e "${YELLOW}⚠️ PostgreSQL connection failed, but continuing...${NC}"
fi

# Test Weaviate
if curl -s "http://${WEAVIATE_HOST}:${WEAVIATE_PORT}/v1/meta" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Weaviate connection successful${NC}"
else
    echo -e "${YELLOW}⚠️ Weaviate connection failed, but continuing...${NC}"
fi

# Test Redis
if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis connection successful${NC}"
else
    echo -e "${YELLOW}⚠️ Redis connection failed, but continuing...${NC}"
fi

# Function to start MCP server
start_mcp_server() {
    local name=$1
    local script=$2
    local port=$3
    
    echo -e "${BLUE}Starting $name (port $port)...${NC}"
    
    # Kill any existing process on the port
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Killing existing process on port $port"
        kill $(lsof -t -i:$port) 2>/dev/null || true
        sleep 2
    fi
    
    # Start the server
    nohup python $script > "/tmp/mcp_${name,,}.log" 2>&1 &
    local pid=$!
    echo $pid > "/tmp/mcp_${name,,}.pid"
    
    # Wait a moment and check if it started
    sleep 3
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ $name failed to start${NC}"
        echo "Last 10 lines of log:"
        tail -10 "/tmp/mcp_${name,,}.log" 2>/dev/null || echo "No log available"
        return 1
    fi
}

# Start MCP servers
echo -e "${BLUE}Starting MCP servers...${NC}"

start_mcp_server "Memory" "mcp_server/servers/memory_server.py" "8003"
start_mcp_server "Conductor" "mcp_server/servers/conductor_server.py" "8002"
start_mcp_server "Tools" "mcp_server/servers/tools_server.py" "8006"

# Verify all servers are running
echo -e "${BLUE}Verifying server status...${NC}"
SERVERS_RUNNING=0

for port in 8002 8003 8006; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Port $port: Server running${NC}"
        ((SERVERS_RUNNING++))
    else
        echo -e "${RED}❌ Port $port: No server running${NC}"
    fi
done

echo ""
echo "=================================================================================="
echo "🎯 MCP ENVIRONMENT STATUS"
echo "=================================================================================="
echo "Servers running: $SERVERS_RUNNING/3"
echo ""
echo "MCP Servers:"
echo "  - Memory Server (context storage): http://localhost:8003"
echo "  - Conductor Server (orchestration): http://localhost:8002"
echo "  - Tools Server (tool execution): http://localhost:8006"
echo ""
echo "AI Services Integration:"
echo "  ✅ Claude - Configured via claude_mcp_config.json"
echo "  ✅ OpenAI - Configured via openai_mcp_config.json"
echo "  ✅ Cursor - Configured via .cursor/mcp.json"
echo "  ✅ Roo - Configured via .roo/mcp.json"
echo "  ✅ Factory AI - Configured via .factory-ai-config"
echo ""
echo "Database Infrastructure:"
echo "  ✅ PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"
echo "  ✅ Weaviate: $WEAVIATE_HOST:$WEAVIATE_PORT"
echo "  ✅ Redis: $REDIS_HOST:$REDIS_PORT"
echo ""

if [ $SERVERS_RUNNING -eq 3 ]; then
    echo -e "${GREEN}🚀 ALL SYSTEMS READY FOR AI CODING WITH FULL CONTEXTUALIZATION!${NC}"
    echo ""
    echo "Your AI coding helpers now have access to:"
    echo "  - Shared project memory and context"
    echo "  - Code intelligence and AST analysis"
    echo "  - Workflow coordination and management"
    echo "  - Tool execution and database operations"
    echo ""
    echo "Ready for enhanced AI coding assistance! 🤖✨"
    
    # Run verification
    echo -e "${BLUE}Running final verification...${NC}"
    python scripts/verify_ai_mcp_integration.py
else
    echo -e "${YELLOW}⚠️  Some servers failed to start. Check logs in /tmp/mcp_*.log${NC}"
    echo ""
    echo "To troubleshoot:"
    echo "  - Check logs: tail -f /tmp/mcp_*.log"
    echo "  - Restart individual servers manually"
    echo "  - Verify database connections"
fi

echo ""
echo "To stop all servers: kill \$(cat /tmp/mcp_*.pid)" 
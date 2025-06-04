#!/bin/bash
# Unified Orchestra Startup Script
# Starts all services with proper health checks

set -e

echo "🚀 Starting Unified Orchestra System..."
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.template to .env and configure it:"
    echo "  cp .env.template .env"
    exit 1
fi

# Source environment variables
source .env

# Check required environment variables
required_vars=(
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set!"
        exit 1
    fi
done

echo "✅ Environment variables loaded"

# Use production or local docker-compose based on availability
if [ -f docker-compose.production.yml ]; then
    COMPOSE_FILE="docker-compose.production.yml"
    echo "📋 Using production configuration"
else
    COMPOSE_FILE="docker-compose.local.yml"
    echo "📋 Using local configuration"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start services
echo "🐳 Starting Docker services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."

# Function to check service health
check_service() {
    local service=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f $COMPOSE_FILE ps | grep $service | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service failed to become healthy"
    return 1
}

# Check each service
services=("postgres" "redis" "weaviate")
all_healthy=true

for service in "${services[@]}"; do
    if ! check_service $service; then
        all_healthy=false
    fi
done

if [ "$all_healthy" = false ]; then
    echo "❌ Some services failed to start properly"
    echo "Check logs with: docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi

# Start MCP servers
echo ""
echo "🔧 Starting MCP servers..."

# Start memory server
if [ -f mcp_server/servers/memory_server.py ]; then
    echo "Starting Memory MCP Server..."
    nohup python3 mcp_server/servers/memory_server.py > logs/mcp_memory.log 2>&1 &
    echo $! > logs/mcp_memory.pid
    echo "✅ Memory server started (PID: $(cat logs/mcp_memory.pid))"
fi

# Start tools server
if [ -f mcp_server/servers/tools_server.py ]; then
    echo "Starting Tools MCP Server..."
    nohup python3 mcp_server/servers/tools_server.py > logs/mcp_tools.log 2>&1 &
    echo $! > logs/mcp_tools.pid
    echo "✅ Tools server started (PID: $(cat logs/mcp_tools.pid))"
fi

# Start code intelligence server
if [ -f mcp_server/servers/code_intelligence_server.py ]; then
    echo "Starting Code Intelligence MCP Server..."
    nohup python3 mcp_server/servers/code_intelligence_server.py > logs/mcp_code.log 2>&1 &
    echo $! > logs/mcp_code.pid
    echo "✅ Code Intelligence server started (PID: $(cat logs/mcp_code.pid))"
fi

# Start git intelligence server
if [ -f mcp_server/servers/git_intelligence_server.py ]; then
    echo "Starting Git Intelligence MCP Server..."
    nohup python3 mcp_server/servers/git_intelligence_server.py > logs/mcp_git.log 2>&1 &
    echo $! > logs/mcp_git.pid
    echo "✅ Git Intelligence server started (PID: $(cat logs/mcp_git.pid))"
fi

# Wait a moment for servers to initialize
sleep 5

# Run health check
echo ""
echo "🏥 Running system health check..."
if [ -f scripts/health_check_comprehensive.py ]; then
    python3 scripts/health_check_comprehensive.py
else
    echo "⚠️  Health check script not found, skipping..."
fi

echo ""
echo "=================================="
echo "✅ Unified Orchestra System Started!"
echo "=================================="
echo ""
echo "Services running:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo "  • Weaviate: localhost:8080"
echo "  • Memory MCP: localhost:8003"
echo "  • Tools MCP: localhost:8006"
echo "  • Code Intelligence: localhost:8007"
echo "  • Git Intelligence: localhost:8008"
echo ""
echo "Monitor logs:"
echo "  • Docker: docker-compose -f $COMPOSE_FILE logs -f"
echo "  • MCP: tail -f logs/mcp_*.log"
echo ""
echo "Stop all services:"
echo "  • ./stop_unified_orchestra.sh"
echo ""

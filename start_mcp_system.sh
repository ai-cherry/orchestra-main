#!/bin/bash
# MCP System Startup Script - PostgreSQL + Weaviate ONLY
# NO Lambda, NO Redis, NO Firestore, NO MongoDB, NO DragonflyDB!

set -e  # Exit on any error

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log directory
LOG_DIR="$HOME/.mcp/logs"
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/mcp_system_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    echo -e "$1" | tee -a $LOG_FILE
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for a service to be healthy
wait_for_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=0

    log "${BLUE}Waiting for $service_name to be healthy...${NC}"

    while [ $attempt -lt $max_attempts ]; do
        if curl -s $health_url > /dev/null 2>&1; then
            log "${GREEN}✓ $service_name is healthy${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log "${RED}✗ $service_name failed to start${NC}"
    return 1
}

# Function to start a server in the background
start_server() {
    local name=$1
    local command=$2
    local port=$3
    local health_endpoint=$4

    log "${BLUE}Starting $name on port $port...${NC}"

    # Check if port is already in use
    if check_port $port; then
        log "${YELLOW}⚠ Port $port is already in use. Attempting to stop existing process...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # Start the server
    nohup $command > "$LOG_DIR/${name}.log" 2>&1 &
    local pid=$!
    echo $pid > "$LOG_DIR/${name}.pid"

    # Wait for health check
    if wait_for_health "$name" "$health_endpoint"; then
        log "${GREEN}✓ $name started successfully (PID: $pid)${NC}"
        return 0
    else
        log "${RED}✗ Failed to start $name${NC}"
        kill $pid 2>/dev/null || true
        return 1
    fi
}

# Main execution
log "${BLUE}========================================${NC}"
log "${BLUE}Starting MCP System (PostgreSQL + Weaviate)${NC}"
log "${BLUE}========================================${NC}"

# Export ONLY the required environment variables for PostgreSQL + Weaviate
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_DB="${POSTGRES_DB:-cherry_ai}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

export WEAVIATE_HOST="${WEAVIATE_HOST:-localhost}"
export WEAVIATE_PORT="${WEAVIATE_PORT:-8080}"
export WEAVIATE_API_KEY="${WEAVIATE_API_KEY:-}"

export API_URL="${API_URL:-http://localhost:8080}"
export API_KEY="${API_KEY:-4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd}"

# Only start the MCP servers that use PostgreSQL + Weaviate
# 1. Start Memory Server (uses PostgreSQL + Weaviate)
start_server "Memory MCP" \
    "./venv/bin/python -m mcp_server.servers.memory_server" \
    8003 \
    "http://localhost:8003/health"

# 2. Start conductor Server (uses PostgreSQL)
start_server "conductor MCP" \
    "./venv/bin/python -m mcp_server.servers.conductor_server" \
    8002 \
    "http://localhost:8002/health"

# 3. Start Tools Server (database agnostic)
start_server "Tools MCP" \
    "./venv/bin/python -m mcp_server.servers.tools_server" \
    8006 \
    "http://localhost:8006/health"

# 4. Start Weaviate Direct Server
start_server "Weaviate Direct MCP" \
    "./venv/bin/python -m mcp_server.servers.weaviate_direct_mcp_server" \
    8001 \
    "http://localhost:8001/health"

# Summary
log "${BLUE}========================================${NC}"
log "${GREEN}MCP System Startup Complete${NC}"
log "${BLUE}========================================${NC}"
log ""
log "Services running (PostgreSQL + Weaviate ONLY):"
log "  - Memory MCP: http://localhost:8003"
log "  - conductor MCP: http://localhost:8002"  
log "  - Tools MCP: http://localhost:8006"
log "  - Weaviate Direct MCP: http://localhost:8001"
log ""
log "Database connections:"
log "  - PostgreSQL: ${POSTGRES_HOST}:${POSTGRES_PORT}"
log "  - Weaviate: ${WEAVIATE_HOST}:${WEAVIATE_PORT}"
log ""
log "Logs available at: $LOG_DIR"
log ""
log "${YELLOW}To stop all services, run: ./stop_mcp_system.sh${NC}"

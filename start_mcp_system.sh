#!/bin/bash
# Unified MCP System Startup Script
# This script starts all MCP servers with health monitoring and error handling

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Prefer system log dir, fall back to user home if not writable
SYSTEM_LOG_DIR="/var/log/mcp"
USER_LOG_DIR="$HOME/.mcp/logs"

if mkdir -p "$SYSTEM_LOG_DIR" 2>/dev/null; then
  LOG_DIR="$SYSTEM_LOG_DIR"
else
  echo "WARNING: No permission for /var/log, using $USER_LOG_DIR instead."
  mkdir -p "$USER_LOG_DIR"
  LOG_DIR="$USER_LOG_DIR"
fi

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
log "${BLUE}Starting MCP System Components${NC}"
log "${BLUE}========================================${NC}"

# Export required environment variables
export GCP_PROJECT_ID="${GCP_PROJECT_ID:-cherry-ai-project}"
export GCP_REGION="${GCP_REGION:-us-central1}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export FIRESTORE_PROJECT="${FIRESTORE_PROJECT:-$GCP_PROJECT_ID}"
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"

# 1. Start Cloud Run MCP Server
start_server "Cloud Run MCP" \
    "python -m mcp_server.servers.gcp_cloud_run_server" \
    8001 \
    "http://localhost:8001/health"

# 2. Start Secrets Manager MCP Server
start_server "Secrets MCP" \
    "python -m mcp_server.servers.gcp_secrets_server" \
    8002 \
    "http://localhost:8002/health"

# 3. Start Memory Management MCP Server (disabled until dependencies resolved)
# echo -e "${YELLOW}Skipping Memory MCP (dependencies not ready)${NC}"

# 4. Start Orchestrator MCP Server
start_server "Orchestrator MCP" \
    "python -m mcp_server.servers.orchestrator_mcp_server" \
    8004 \
    "http://localhost:8004/health"

# 5. Start MCP Gateway (unified interface)
start_server "MCP Gateway" \
    "python -m mcp_server.gateway" \
    8000 \
    "http://localhost:8000/health"

# Summary
log "${BLUE}========================================${NC}"
log "${GREEN}MCP System Startup Complete${NC}"
log "${BLUE}========================================${NC}"
log ""
log "Services running:"
log "  - MCP Gateway: http://localhost:8000"
log "  - Cloud Run MCP: http://localhost:8001"
log "  - Secrets MCP: http://localhost:8002"
log "  - Memory MCP: http://localhost:8003"
log "  - Orchestrator MCP: http://localhost:8004"
log ""
log "Logs available at: $LOG_DIR"
log ""
log "${YELLOW}To stop all services, run: ./stop_mcp_system.sh${NC}"
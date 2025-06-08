#!/bin/bash
# 🚀 Minimal MCP Server Startup - Just the Unified Server
# Start only the working MCP unified server for immediate testing

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

# Create directories
mkdir -p ~/.mcp/logs ~/.mcp/pids

log "🚀 Starting Orchestra AI Unified MCP Server"
log "=========================================="

# Activate virtual environment if not active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log "Activating virtual environment..."
    source venv/bin/activate
fi

# Export environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export POSTGRES_HOST="${POSTGRES_HOST:-45.77.87.106}"
export REDIS_HOST="${REDIS_HOST:-45.77.87.106}"

log "Environment: PYTHONPATH=$PYTHONPATH"

# Stop any existing unified server
PID_FILE="$HOME/.mcp/pids/unified.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log "Stopping existing unified server (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# Start the unified MCP server
log "Starting unified MCP server on port 8000..."
LOG_FILE="$HOME/.mcp/logs/unified.log"

nohup python mcp_unified_server.py > "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# Wait and check if it started
sleep 3
if kill -0 "$PID" 2>/dev/null; then
    log "✅ Unified MCP Server started successfully!"
    log "   PID: $PID"
    log "   Endpoint: http://localhost:8000"
    log "   Log: $LOG_FILE"
    log "   Health: http://localhost:8000/health"
    
    # Test the server
    log ""
    log "🔍 Testing server health..."
    if curl -s http://localhost:8000/health > /dev/null; then
        log "✅ Server is responding to health checks"
    else
        log "⚠️ Server may still be starting up"
    fi
else
    error "❌ Unified MCP Server failed to start"
    if [ -f "$LOG_FILE" ]; then
        echo "Last 10 lines of log:"
        tail -10 "$LOG_FILE"
    fi
    rm -f "$PID_FILE"
    exit 1
fi

log ""
log "🎯 MCP Server Commands:"
log "   Status: ./check_mcp_status.sh"
log "   Stop:   ./stop_mcp_servers.sh"
log "   Full:   ./start_mcp_servers_working.sh"

log ""
log "✅ Minimal MCP setup complete!" 
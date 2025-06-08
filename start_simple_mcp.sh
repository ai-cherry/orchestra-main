#!/bin/bash
# 🚀 Start Simple Working MCP Server
# Quick deployment for immediate testing

set -e

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

log "🚀 Starting Simple Orchestra MCP Server"
log "======================================"

# Activate virtual environment if not active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log "Activating virtual environment..."
    source venv/bin/activate
fi

# Stop any existing server
PID_FILE="$HOME/.mcp/pids/simple.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log "Stopping existing server (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# Start the simple MCP server
log "Starting simple MCP server on port 8000..."
LOG_FILE="$HOME/.mcp/logs/simple.log"

nohup python mcp_simple_server.py > "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# Wait and check if it started
sleep 2
if kill -0 "$PID" 2>/dev/null; then
    log "✅ Simple MCP Server started successfully!"
    log "   PID: $PID"
    log "   Log: $LOG_FILE"
    log ""
    log "🎯 Available MCP Tools:"
    log "   - register_tool: Register coding tools"
    log "   - get_context: Get shared context"
    log "   - route_task: Route tasks to optimal tool"
    log "   - health_check: Check system status"
    log ""
    log "🔗 Integration Ready:"
    log "   - Cursor: Native AI integration"
    log "   - Roo: 10 specialized modes via OpenRouter"
    log "   - Continue: UI-GPT-4O via OpenAI"
else
    error "❌ Simple MCP Server failed to start"
    if [ -f "$LOG_FILE" ]; then
        echo "Last 10 lines of log:"
        tail -10 "$LOG_FILE"
    fi
    rm -f "$PID_FILE"
    exit 1
fi

log ""
log "✅ Simple MCP setup complete!"
log "🎯 Next: Test with your coding assistants" 
#!/bin/bash
# 🚀 Working MCP Server Startup Script
# Starts the actual MCP servers that exist in the Orchestra AI project

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Log function
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

# Create log and PID directories
mkdir -p ~/.mcp/logs ~/.mcp/pids

log "🚀 Starting Orchestra AI MCP Servers"
log "======================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log "Activating virtual environment..."
    source venv/bin/activate
fi

# Export required environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export POSTGRES_HOST="${POSTGRES_HOST:-45.77.87.106}"
export REDIS_HOST="${REDIS_HOST:-45.77.87.106}"
export WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"

log "Environment configured:"
log "  PYTHONPATH: $PYTHONPATH"
log "  POSTGRES_HOST: $POSTGRES_HOST"
log "  REDIS_HOST: $REDIS_HOST"
log "  WEAVIATE_URL: $WEAVIATE_URL"

# Function to start a server
start_server() {
    local name=$1
    local script=$2
    local port=$3
    local pid_file="$HOME/.mcp/pids/${name}.pid"
    local log_file="$HOME/.mcp/logs/${name}.log"
    
    log "Starting $name server on port $port..."
    
    # Kill existing process if running
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            warn "$name server already running (PID: $old_pid), stopping it..."
            kill "$old_pid" 2>/dev/null || true
            sleep 2
        fi
        rm -f "$pid_file"
    fi
    
    # Check if script exists
    if [ ! -f "$script" ]; then
        error "Server script not found: $script"
        return 1
    fi
    
    # Start the server
    nohup python3 "$script" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait a moment and check if it's still running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        log "✅ $name server started successfully (PID: $pid)"
        return 0
    else
        error "❌ $name server failed to start"
        cat "$log_file" | tail -5
        rm -f "$pid_file"
        return 1
    fi
}

# Start available servers
log "\n🔧 Starting available MCP servers..."

# 1. Unified MCP Server (main orchestrator)
start_server "unified" "mcp_unified_server.py" 8000

# 2. Weaviate Direct Server (if exists)
if [ -f "legacy/mcp_server/servers/weaviate_direct_mcp_server.py" ]; then
    start_server "weaviate-direct" "legacy/mcp_server/servers/weaviate_direct_mcp_server.py" 8001
fi

# 3. Web Scraping Server (if exists)
if [ -f "legacy/mcp_server/servers/web_scraping_mcp_server.py" ]; then
    start_server "web-scraping" "legacy/mcp_server/servers/web_scraping_mcp_server.py" 8012
fi

# 4. Lambda Infrastructure Server
if [ -f "lambda_infrastructure_mcp_server.py" ]; then
    start_server "infrastructure" "lambda_infrastructure_mcp_server.py" 8009
fi

# 5. Pay Ready Server (Sophia domain)
if [ -f "src/pay_ready_mcp_server.py" ]; then
    start_server "sophia-payready" "src/pay_ready_mcp_server.py" 8014
fi

# Display status
log "\n📊 MCP Server Status:"
log "===================="

for pid_file in ~/.mcp/pids/*.pid; do
    if [ -f "$pid_file" ]; then
        server_name=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "✅ $server_name: Running (PID: $pid)"
        else
            error "❌ $server_name: Not running"
        fi
    fi
done

log "\n🔗 Available Endpoints:"
log "====================="
log "  Unified MCP:        http://localhost:8000"
log "  Weaviate Direct:    http://localhost:8001"  
log "  Web Scraping:       http://localhost:8012"
log "  Infrastructure:     http://localhost:8009"
log "  Sophia Pay Ready:   http://localhost:8014"

log "\n📝 Logs available in: ~/.mcp/logs/"
log "📝 PIDs available in: ~/.mcp/pids/"

log "\n🎯 To stop servers: ./stop_mcp_servers.sh"
log "🎯 To check status: ./check_mcp_status.sh"

log "\n✅ MCP Server startup complete!" 
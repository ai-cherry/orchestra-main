#!/bin/bash

# 🎼 Orchestra AI - Memory Management MCP Server Startup Script
# Port: 8003

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_PATH="$PROJECT_ROOT/venv"
MCP_SERVERS_DIR="$PROJECT_ROOT/mcp_servers"
SERVER_SCRIPT="memory_management_server.py"
SERVER_PORT=8003
LOG_FILE="$PROJECT_ROOT/logs/mcp_memory_server.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Function to check if port is in use
check_port() {
    if lsof -ti :$SERVER_PORT >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port available
    fi
}

# Function to stop existing server
stop_server() {
    log "Checking for existing Memory Management MCP Server on port $SERVER_PORT..."
    
    if check_port; then
        warning "Port $SERVER_PORT is in use. Stopping existing process..."
        lsof -ti :$SERVER_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
        
        if check_port; then
            error "Failed to stop existing server on port $SERVER_PORT"
            exit 1
        else
            success "Existing server stopped"
        fi
    else
        log "Port $SERVER_PORT is available"
    fi
}

# Function to start server
start_server() {
    log "Starting Memory Management MCP Server..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found at $VENV_PATH"
        error "Please run ./setup_dev_environment.sh first"
        exit 1
    fi
    
    # Check if server script exists
    if [ ! -f "$MCP_SERVERS_DIR/$SERVER_SCRIPT" ]; then
        error "Server script not found at $MCP_SERVERS_DIR/$SERVER_SCRIPT"
        exit 1
    fi
    
    # Activate virtual environment and start server
    cd "$MCP_SERVERS_DIR"
    
    log "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    log "Installing/checking dependencies..."
    pip install -q fastapi uvicorn structlog pydantic
    
    log "Starting server on port $SERVER_PORT..."
    uvicorn memory_management_server:app \
        --host 0.0.0.0 \
        --port $SERVER_PORT \
        --log-level info \
        --access-log \
        --reload \
        > "$LOG_FILE" 2>&1 &
    
    SERVER_PID=$!
    echo $SERVER_PID > "$PROJECT_ROOT/logs/mcp_memory_server.pid"
    
    # Wait for server to start
    log "Waiting for server to start..."
    sleep 3
    
    # Check if server is responding
    for i in {1..10}; do
        if curl -s -f http://localhost:$SERVER_PORT/health >/dev/null 2>&1; then
            success "Memory Management MCP Server started successfully!"
            success "Server PID: $SERVER_PID"
            success "Health check: http://localhost:$SERVER_PORT/health"
            success "API docs: http://localhost:$SERVER_PORT/docs"
            success "Log file: $LOG_FILE"
            return 0
        fi
        
        log "Attempt $i/10: Waiting for server to respond..."
        sleep 2
    done
    
    error "Server failed to start or is not responding"
    error "Check log file: $LOG_FILE"
    return 1
}

# Function to check server status
status_server() {
    if check_port; then
        PID_FILE="$PROJECT_ROOT/logs/mcp_memory_server.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                success "Memory Management MCP Server is running (PID: $PID)"
                log "Health check: $(curl -s http://localhost:$SERVER_PORT/health 2>/dev/null || echo 'Failed')"
            else
                warning "PID file exists but process is not running"
            fi
        else
            warning "Server is running but PID file not found"
        fi
    else
        warning "Memory Management MCP Server is not running"
    fi
}

# Function to test server
test_server() {
    log "Testing Memory Management MCP Server..."
    
    if ! check_port; then
        error "Server is not running on port $SERVER_PORT"
        return 1
    fi
    
    # Health check
    log "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:$SERVER_PORT/health)
    if [ $? -eq 0 ]; then
        success "Health check passed"
        echo "Response: $HEALTH_RESPONSE"
    else
        error "Health check failed"
        return 1
    fi
    
    # Test memory storage
    log "Testing memory storage..."
    STORE_RESPONSE=$(curl -s -X POST http://localhost:$SERVER_PORT/memory \
        -H "Content-Type: application/json" \
        -d '{"memory_type": "test", "content": {"test": "data"}, "metadata": {"source": "startup_test"}}')
    
    if [ $? -eq 0 ]; then
        success "Memory storage test passed"
        echo "Response: $STORE_RESPONSE"
    else
        error "Memory storage test failed"
        return 1
    fi
    
    success "All tests passed!"
}

# Main execution
case "${1:-start}" in
    "start")
        log "🎼 Starting Orchestra AI Memory Management MCP Server"
        stop_server
        start_server
        ;;
    "stop")
        log "🛑 Stopping Memory Management MCP Server"
        stop_server
        success "Server stopped"
        ;;
    "restart")
        log "🔄 Restarting Memory Management MCP Server"
        stop_server
        start_server
        ;;
    "status")
        log "📊 Checking Memory Management MCP Server status"
        status_server
        ;;
    "test")
        log "🧪 Testing Memory Management MCP Server"
        test_server
        ;;
    "logs")
        log "📋 Showing Memory Management MCP Server logs"
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            error "Log file not found: $LOG_FILE"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Memory Management MCP Server"
        echo "  stop    - Stop the Memory Management MCP Server"
        echo "  restart - Restart the Memory Management MCP Server"
        echo "  status  - Check server status"
        echo "  test    - Run server tests"
        echo "  logs    - Show server logs (tail -f)"
        exit 1
        ;;
esac 
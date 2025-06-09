#!/bin/bash
# Launch Cursor with Claude Code integration

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging configuration
LOG_DIR="$HOME/.claude-code/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cursor_launch_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    local level=$1
    shift
    local msg="$@"
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $msg" | tee -a "$LOG_FILE"
}

# Function to log with color
log_info() {
    echo -e "${BLUE}ℹ${NC} $@"
    log "INFO" "$@"
}

log_success() {
    echo -e "${GREEN}✓${NC} $@"
    log "SUCCESS" "$@"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $@"
    log "WARNING" "$@"
}

log_error() {
    echo -e "${RED}✗${NC} $@"
    log "ERROR" "$@"
}

PROJECT_T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_DIR="$PROJECT_T/mcp_server"

# Ensure environment is loaded
if [ -f ~/.Lambda_env_setup.sh ]; then
    source ~/.Lambda_env_setup.sh
    log_info "Loaded Lambda environment setup"
else
    log_warning "Lambda environment setup not found at ~/.Lambda_env_setup.sh"
fi

# Load server registry if it exists
SERVER_REGISTRY="$MCP_SERVER_DIR/server_registry.json"
if [ -f "$SERVER_REGISTRY" ]; then
    log_info "Loading server registry from $SERVER_REGISTRY"
else
    log_warning "Server registry not found, will scan for available servers"
fi

# Array to store PID and server info
declare -a MCP_PIDS
declare -a MCP_SERVERS

# Function to check if a server file exists and is executable
check_server() {
    local server_path=$1
    if [ -f "$server_path" ]; then
        if python -m py_compile "$server_path" 2>/dev/null; then
            return 0
        else
            log_error "Server file has syntax errors: $server_path"
            return 1
        fi
    else
        log_error "Server file not found: $server_path"
        return 1
    fi
}

# Function to start a server
start_server() {
    local server_name=$1
    local server_path=$2

    log_info "Starting $server_name server..."

    # Check if server exists
    if ! check_server "$server_path"; then
        log_error "Cannot start $server_name - server file issues"
        return 1
    fi

    # Start the server with proper error handling
    python "$server_path" >> "$LOG_FILE" 2>&1 &
    local pid=$!

    # Give server a moment to start
    sleep 1

    # Check if server is still running
    if kill -0 $pid 2>/dev/null; then
        MCP_PIDS+=($pid)
        MCP_SERVERS+=("$server_name")
        log_success "Started $server_name server (PID: $pid)"
        return 0
    else
        log_error "Failed to start $server_name server"
        return 1
    fi
}

# Start MCP servers based on availability
log_info "Starting MCP servers..."

# Define available servers and their paths
declare -A AVAILABLE_SERVERS=(
    ["Lambda-cloud-run"]="$MCP_SERVER_DIR/servers/Lambda_cloud_run_server.py"
    ["Lambda-secrets"]="$MCP_SERVER_DIR/servers/Lambda_secret_manager_server.py"
    ["dragonfly"]="$MCP_SERVER_DIR/servers/dragonfly_server.py"
    ["firestore"]="$MCP_SERVER_DIR/servers/firestore_server.py"
)

# Start each available server
for server_name in "${!AVAILABLE_SERVERS[@]}"; do
    server_path="${AVAILABLE_SERVERS[$server_name]}"
    if [ -f "$server_path" ]; then
        start_server "$server_name" "$server_path" || true
    else
        log_warning "Skipping $server_name - server not found at $server_path"
    fi
done

# Check if any servers were started
if [ ${#MCP_PIDS[@]} -eq 0 ]; then
    log_error "No MCP servers could be started"
    log_info "Please check the log file: $LOG_FILE"
    exit 1
fi

log_success "Started ${#MCP_PIDS[@]} MCP servers"

# Function to cleanup on exit
cleanup() {
    log_info "Stopping MCP servers..."
    for i in "${!MCP_PIDS[@]}"; do
        local pid="${MCP_PIDS[$i]}"
        local server="${MCP_SERVERS[$i]}"
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null || true
            log_info "Stopped $server server (PID: $pid)"
        fi
    done
    log_success "All MCP servers stopped"
}
trap cleanup EXIT INT TERM

# Check if cursor is installed
if ! command -v cursor &> /dev/null; then
    log_error "Cursor is not installed or not in PATH"
    log_info "Please install Cursor from https://cursor.sh"
    exit 1
fi

# Launch Cursor
log_info "Launching Cursor..."
cursor "$PROJECT_T" &
CURSOR_PID=$!

# Show helpful information
log_success "Cursor launched with ${#MCP_PIDS[@]} MCP servers"
log_info "Log file: $LOG_FILE"
log_info "Press Ctrl+C to stop all servers and exit"

# Keep script running and monitor servers
while true; do
    # Check if Cursor is still running
    if ! kill -0 $CURSOR_PID 2>/dev/null; then
        log_info "Cursor has been closed"
        break
    fi

    # Check if servers are still running
    for i in "${!MCP_PIDS[@]}"; do
        local pid="${MCP_PIDS[$i]}"
        local server="${MCP_SERVERS[$i]}"
        if ! kill -0 $pid 2>/dev/null; then
            log_warning "$server server (PID: $pid) has stopped unexpectedly"
            # Attempt to restart
            server_path="${AVAILABLE_SERVERS[$server]}"
            if start_server "$server" "$server_path"; then
                # Update the PID in the array
                MCP_PIDS[$i]=${MCP_PIDS[-1]}
                unset 'MCP_PIDS[-1]'
            fi
        fi
    done

    sleep 5
done

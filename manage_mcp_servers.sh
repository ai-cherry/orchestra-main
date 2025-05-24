#!/bin/bash
# MCP Server Management Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_DIR="$PROJECT_ROOT/mcp_server"
PID_DIR="$HOME/.claude-code/pids"
LOG_DIR="$HOME/.claude-code/logs"

# Create directories if they don't exist
mkdir -p "$PID_DIR" "$LOG_DIR"

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop|restart|status|list} [server-name]"
    echo ""
    echo "Commands:"
    echo "  start [server]    Start a specific server or all servers"
    echo "  stop [server]     Stop a specific server or all servers"
    echo "  restart [server]  Restart a specific server or all servers"
    echo "  status [server]   Show status of a specific server or all servers"
    echo "  list             List all available servers"
    echo ""
    echo "Examples:"
    echo "  $0 start                # Start all servers"
    echo "  $0 start dragonfly      # Start only dragonfly server"
    echo "  $0 status               # Show status of all servers"
    echo "  $0 stop gcp-secrets     # Stop GCP secrets server"
    exit 1
}

# Function to get server list from registry or filesystem
get_server_list() {
    local registry="$MCP_SERVER_DIR/server_registry.json"
    if [ -f "$registry" ] && command -v jq &> /dev/null; then
        jq -r '.servers | keys[]' "$registry" 2>/dev/null
    else
        # Fallback to filesystem scan
        for server_file in "$MCP_SERVER_DIR/servers/"*.py; do
            if [ -f "$server_file" ]; then
                basename "$server_file" .py | sed 's/_server$//' | sed 's/_/-/g'
            fi
        done
    fi
}

# Function to get server path
get_server_path() {
    local server_name=$1
    local server_file=$(echo "$server_name" | sed 's/-/_/g')_server.py
    echo "$MCP_SERVER_DIR/servers/$server_file"
}

# Function to get PID file path
get_pid_file() {
    local server_name=$1
    echo "$PID_DIR/mcp_${server_name}.pid"
}

# Function to check if server is running
is_running() {
    local server_name=$1
    local pid_file=$(get_pid_file "$server_name")
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            # PID file exists but process is not running
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Function to start a server
start_server() {
    local server_name=$1
    local server_path=$(get_server_path "$server_name")
    local pid_file=$(get_pid_file "$server_name")
    local log_file="$LOG_DIR/mcp_${server_name}_$(date +%Y%m%d).log"
    
    if is_running "$server_name"; then
        echo -e "${YELLOW}⚠${NC} $server_name is already running"
        return 1
    fi
    
    if [ ! -f "$server_path" ]; then
        echo -e "${RED}✗${NC} Server file not found: $server_path"
        return 1
    fi
    
    # Check syntax
    if ! python -m py_compile "$server_path" 2>/dev/null; then
        echo -e "${RED}✗${NC} $server_name has syntax errors"
        return 1
    fi
    
    echo -n "Starting $server_name... "
    
    # Load environment if available
    [ -f ~/.gcp_env_setup.sh ] && source ~/.gcp_env_setup.sh
    
    # Start server
    nohup python "$server_path" >> "$log_file" 2>&1 &
    local pid=$!
    
    # Give it a moment to start
    sleep 1
    
    if kill -0 "$pid" 2>/dev/null; then
        echo "$pid" > "$pid_file"
        echo -e "${GREEN}✓${NC} Started (PID: $pid, Log: $log_file)"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to start"
        return 1
    fi
}

# Function to stop a server
stop_server() {
    local server_name=$1
    local pid_file=$(get_pid_file "$server_name")
    
    if ! is_running "$server_name"; then
        echo -e "${YELLOW}⚠${NC} $server_name is not running"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    echo -n "Stopping $server_name (PID: $pid)... "
    
    kill "$pid" 2>/dev/null
    
    # Wait for process to stop
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    if kill -0 "$pid" 2>/dev/null; then
        # Force kill if still running
        kill -9 "$pid" 2>/dev/null
    fi
    
    rm -f "$pid_file"
    echo -e "${GREEN}✓${NC} Stopped"
    return 0
}

# Function to show server status
show_status() {
    local server_name=$1
    local server_path=$(get_server_path "$server_name")
    local pid_file=$(get_pid_file "$server_name")
    
    echo -n "$server_name: "
    
    if [ ! -f "$server_path" ]; then
        echo -e "${RED}✗${NC} Not installed"
        return
    fi
    
    if is_running "$server_name"; then
        local pid=$(cat "$pid_file")
        local log_file="$LOG_DIR/mcp_${server_name}_$(date +%Y%m%d).log"
        echo -e "${GREEN}✓${NC} Running (PID: $pid)"
        if [ -f "$log_file" ]; then
            echo "    Log: $log_file"
            # Show last few log lines
            tail -n 3 "$log_file" 2>/dev/null | sed 's/^/    /'
        fi
    else
        echo -e "${YELLOW}○${NC} Stopped"
    fi
}

# Function to list all servers
list_servers() {
    echo "Available MCP Servers:"
    echo ""
    
    local registry="$MCP_SERVER_DIR/server_registry.json"
    if [ -f "$registry" ] && command -v jq &> /dev/null; then
        # Use registry for detailed info
        jq -r '.servers | to_entries[] | "- \(.key): \(.value.description)"' "$registry"
    else
        # Fallback to simple list
        get_server_list | while read -r server; do
            echo "- $server"
        done
    fi
}

# Main command handling
case "$1" in
    start)
        if [ -z "$2" ]; then
            # Start all servers
            echo "Starting all MCP servers..."
            get_server_list | while read -r server; do
                start_server "$server"
            done
        else
            # Start specific server
            start_server "$2"
        fi
        ;;
        
    stop)
        if [ -z "$2" ]; then
            # Stop all servers
            echo "Stopping all MCP servers..."
            get_server_list | while read -r server; do
                stop_server "$server"
            done
        else
            # Stop specific server
            stop_server "$2"
        fi
        ;;
        
    restart)
        if [ -z "$2" ]; then
            # Restart all servers
            echo "Restarting all MCP servers..."
            get_server_list | while read -r server; do
                stop_server "$server"
                start_server "$server"
            done
        else
            # Restart specific server
            stop_server "$2"
            start_server "$2"
        fi
        ;;
        
    status)
        if [ -z "$2" ]; then
            # Show status of all servers
            echo "MCP Server Status:"
            echo ""
            get_server_list | while read -r server; do
                show_status "$server"
                echo ""
            done
        else
            # Show status of specific server
            show_status "$2"
        fi
        ;;
        
    list)
        list_servers
        ;;
        
    *)
        usage
        ;;
esac
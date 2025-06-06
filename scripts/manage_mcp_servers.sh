#!/bin/bash
# MCP Server Management Script

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_SERVER_DIR="$BASE_DIR/mcp_server/servers"
PID_DIR="$BASE_DIR/.mcp_pids"
LOG_DIR="$BASE_DIR/.mcp_logs"

# Create directories if they don't exist
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

# Server configurations
declare -A SERVERS
SERVERS["secret_manager"]="Lambda_secret_manager_server.py:8002"
SERVERS["firestore"]="firestore_server.py:8080"
SERVERS["dragonfly"]="dragonfly_server.py:8004"
SERVERS["cloud_run"]="Lambda_cloud_run_server.py:8001"

# Function to check if a server is running
is_running() {
    local server_name=$1
    local pid_file="$PID_DIR/$server_name.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Function to start a server
start_server() {
    local server_name=$1
    local server_info=${SERVERS[$server_name]}
    local server_file=$(echo $server_info | cut -d: -f1)
    local server_port=$(echo $server_info | cut -d: -f2)

    if is_running "$server_name"; then
        echo -e "${YELLOW}⚠️  $server_name is already running${NC}"
        return 0
    fi

    if [ ! -f "$MCP_SERVER_DIR/$server_file" ]; then
        echo -e "${RED}❌ Server file not found: $server_file${NC}"
        return 1
    fi

    echo -e "${BLUE}🚀 Starting $server_name on port $server_port...${NC}"

    # Source environment variables
    if [ -f "$BASE_DIR/.env" ]; then
        export $(cat "$BASE_DIR/.env" | grep -v '^#' | xargs)
    fi

    # Start the server
    cd "$BASE_DIR"
    nohup python "$MCP_SERVER_DIR/$server_file" > "$LOG_DIR/$server_name.log" 2>&1 &
    local pid=$!

    # Save PID
    echo $pid > "$PID_DIR/$server_name.pid"

    # Wait a moment and check if it started
    sleep 2
    if is_running "$server_name"; then
        echo -e "${GREEN}✅ $server_name started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start $server_name${NC}"
        tail -n 20 "$LOG_DIR/$server_name.log"
        return 1
    fi
}

# Function to stop a server
stop_server() {
    local server_name=$1
    local pid_file="$PID_DIR/$server_name.pid"

    if ! is_running "$server_name"; then
        echo -e "${YELLOW}⚠️  $server_name is not running${NC}"
        return 0
    fi

    local pid=$(cat "$pid_file")
    echo -e "${BLUE}🛑 Stopping $server_name (PID: $pid)...${NC}"

    kill -TERM "$pid" 2>/dev/null || true

    # Wait for graceful shutdown
    local count=0
    while is_running "$server_name" && [ $count -lt 10 ]; do
        sleep 1
        ((count++))
    done

    # Force kill if still running
    if is_running "$server_name"; then
        kill -KILL "$pid" 2>/dev/null || true
    fi

    rm -f "$pid_file"
    echo -e "${GREEN}✅ $server_name stopped${NC}"
}

# Function to check server status
status_server() {
    local server_name=$1
    local server_info=${SERVERS[$server_name]}
    local server_port=$(echo $server_info | cut -d: -f2)

    if is_running "$server_name"; then
        local pid=$(cat "$PID_DIR/$server_name.pid")
        echo -e "${GREEN}✅ $server_name is running (PID: $pid, Port: $server_port)${NC}"

        # Try to check health endpoint
        if command -v curl &> /dev/null; then
            local health_url="http://localhost:$server_port/health"
            if curl -s -f "$health_url" > /dev/null 2>&1; then
                echo -e "   Health check: ${GREEN}✅ Healthy${NC}"
            else
                echo -e "   Health check: ${YELLOW}⚠️  Not responding${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ $server_name is not running${NC}"
    fi
}

# Function to restart a server
restart_server() {
    local server_name=$1
    echo -e "${BLUE}🔄 Restarting $server_name...${NC}"
    stop_server "$server_name"
    sleep 1
    start_server "$server_name"
}

# Function to show logs
show_logs() {
    local server_name=$1
    local log_file="$LOG_DIR/$server_name.log"

    if [ -f "$log_file" ]; then
        echo -e "${BLUE}📜 Logs for $server_name:${NC}"
        tail -f "$log_file"
    else
        echo -e "${RED}❌ No logs found for $server_name${NC}"
    fi
}

# Main command handler
case "$1" in
    start)
        if [ "$2" == "all" ]; then
            for server in "${!SERVERS[@]}"; do
                start_server "$server"
            done
        elif [ -n "$2" ] && [ -n "${SERVERS[$2]}" ]; then
            start_server "$2"
        else
            echo "Usage: $0 start <server_name|all>"
            echo "Available servers: ${!SERVERS[@]}"
        fi
        ;;
    stop)
        if [ "$2" == "all" ]; then
            for server in "${!SERVERS[@]}"; do
                stop_server "$server"
            done
        elif [ -n "$2" ] && [ -n "${SERVERS[$2]}" ]; then
            stop_server "$2"
        else
            echo "Usage: $0 stop <server_name|all>"
            echo "Available servers: ${!SERVERS[@]}"
        fi
        ;;
    restart)
        if [ "$2" == "all" ]; then
            for server in "${!SERVERS[@]}"; do
                restart_server "$server"
            done
        elif [ -n "$2" ] && [ -n "${SERVERS[$2]}" ]; then
            restart_server "$2"
        else
            echo "Usage: $0 restart <server_name|all>"
            echo "Available servers: ${!SERVERS[@]}"
        fi
        ;;
    status)
        echo -e "${BLUE}🔍 MCP Server Status${NC}"
        echo "===================="
        if [ "$2" == "all" ] || [ -z "$2" ]; then
            for server in "${!SERVERS[@]}"; do
                status_server "$server"
            done
        elif [ -n "${SERVERS[$2]}" ]; then
            status_server "$2"
        else
            echo "Usage: $0 status [server_name|all]"
            echo "Available servers: ${!SERVERS[@]}"
        fi
        ;;
    logs)
        if [ -n "$2" ] && [ -n "${SERVERS[$2]}" ]; then
            show_logs "$2"
        else
            echo "Usage: $0 logs <server_name>"
            echo "Available servers: ${!SERVERS[@]}"
        fi
        ;;
    *)
        echo "MCP Server Management Script"
        echo "============================"
        echo "Usage: $0 {start|stop|restart|status|logs} [server_name|all]"
        echo ""
        echo "Commands:"
        echo "  start   - Start MCP server(s)"
        echo "  stop    - Stop MCP server(s)"
        echo "  restart - Restart MCP server(s)"
        echo "  status  - Show server status"
        echo "  logs    - Show server logs (tail -f)"
        echo ""
        echo "Available servers:"
        for server in "${!SERVERS[@]}"; do
            echo "  - $server"
        done
        echo ""
        echo "Examples:"
        echo "  $0 start all              # Start all servers"
        echo "  $0 stop secret_manager    # Stop specific server"
        echo "  $0 status                 # Show status of all servers"
        echo "  $0 logs firestore         # Show Firestore server logs"
        ;;
esac

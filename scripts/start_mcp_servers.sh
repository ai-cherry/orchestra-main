#!/bin/bash

# MCP Server Management Script for Orchestra AI
# Starts and manages MCP servers with auto-restart functionality

set -e

# Configuration
LOG_DIR="/tmp/mcp_logs"
PID_DIR="/tmp/mcp_pids"
SERVER_DIR="/home/ubuntu/orchestra-main/legacy/mcp_server/servers"

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment variables
export POSTGRES_HOST="45.77.87.106"
export POSTGRES_USER="postgres"
export POSTGRES_DB="cherry_ai"
export REDIS_HOST="45.77.87.106"
export WEAVIATE_URL="http://localhost:8080"

# MCP Servers configuration
declare -A MCP_SERVERS=(
    ["enhanced-memory"]="${SERVER_DIR}/enhanced_memory_server.py"
    ["code-intelligence"]="${SERVER_DIR}/code_intelligence_server.py"
    ["git-intelligence"]="${SERVER_DIR}/git_intelligence_server.py"
    ["infrastructure-manager"]="${SERVER_DIR}/infrastructure_manager.py"
    ["cherry-domain"]="${SERVER_DIR}/enhanced_cherry_domain_server.py"
    ["sophia-payready"]="${SERVER_DIR}/sophia_payready_domain_server.py"
    ["karen-paragonrx"]="${SERVER_DIR}/karen_paragonrx_domain_server.py"
    ["weaviate-direct"]="${SERVER_DIR}/weaviate_direct_mcp_server.py"
    ["web-scraping"]="${SERVER_DIR}/web_scraping_mcp_server.py"
    ["prompt-management"]="${SERVER_DIR}/prompt_management.py"
)

function log_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

function log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

function log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

function log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

function start_server() {
    local server_name="$1"
    local server_path="$2"
    local pid_file="$PID_DIR/${server_name}.pid"
    local log_file="$LOG_DIR/${server_name}.log"
    
    # Check if server is already running
    if [ -f "$pid_file" ] && kill -0 "$(cat $pid_file)" 2>/dev/null; then
        log_warning "Server $server_name is already running (PID: $(cat $pid_file))"
        return 0
    fi
    
    # Check if server file exists
    if [ ! -f "$server_path" ]; then
        log_error "Server file not found: $server_path"
        return 1
    fi
    
    log_message "Starting MCP server: $server_name"
    
    # Start the server in background
    nohup python3 "$server_path" > "$log_file" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$pid_file"
    
    # Give it a moment to start
    sleep 2
    
    # Check if it's still running
    if kill -0 $pid 2>/dev/null; then
        log_success "Server $server_name started successfully (PID: $pid)"
        return 0
    else
        log_error "Server $server_name failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

function stop_server() {
    local server_name="$1"
    local pid_file="$PID_DIR/${server_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log_message "Stopping server: $server_name (PID: $pid)"
            kill "$pid"
            rm -f "$pid_file"
            log_success "Server $server_name stopped"
        else
            log_warning "Server $server_name was not running"
            rm -f "$pid_file"
        fi
    else
        log_warning "No PID file found for server: $server_name"
    fi
}

function check_server() {
    local server_name="$1"
    local pid_file="$PID_DIR/${server_name}.pid"
    
    if [ -f "$pid_file" ] && kill -0 "$(cat $pid_file)" 2>/dev/null; then
        echo -e "${GREEN}✅ $server_name${NC} (PID: $(cat $pid_file))"
        return 0
    else
        echo -e "${RED}❌ $server_name${NC} (not running)"
        return 1
    fi
}

function status_all() {
    log_message "MCP Server Status:"
    echo "========================"
    
    local running=0
    local total=0
    
    for server_name in "${!MCP_SERVERS[@]}"; do
        check_server "$server_name"
        if [ $? -eq 0 ]; then
            ((running++))
        fi
        ((total++))
    done
    
    echo "========================"
    echo -e "${BLUE}Total:${NC} $running/$total servers running"
}

function start_all() {
    log_message "Starting all MCP servers..."
    
    for server_name in "${!MCP_SERVERS[@]}"; do
        start_server "$server_name" "${MCP_SERVERS[$server_name]}"
    done
    
    echo ""
    status_all
}

function stop_all() {
    log_message "Stopping all MCP servers..."
    
    for server_name in "${!MCP_SERVERS[@]}"; do
        stop_server "$server_name"
    done
}

function restart_all() {
    log_message "Restarting all MCP servers..."
    stop_all
    sleep 3
    start_all
}

function monitor_servers() {
    log_message "Starting MCP server monitor (press Ctrl+C to stop)..."
    
    trap 'log_message "Monitor stopped"; exit 0' INT
    
    while true; do
        local restarted=0
        
        for server_name in "${!MCP_SERVERS[@]}"; do
            local pid_file="$PID_DIR/${server_name}.pid"
            
            if [ -f "$pid_file" ] && kill -0 "$(cat $pid_file)" 2>/dev/null; then
                # Server is running, continue
                continue
            else
                # Server is down, restart it
                log_warning "Server $server_name is down, restarting..."
                start_server "$server_name" "${MCP_SERVERS[$server_name]}"
                ((restarted++))
            fi
        done
        
        if [ $restarted -gt 0 ]; then
            log_message "Restarted $restarted servers"
        fi
        
        sleep 30  # Check every 30 seconds
    done
}

function show_logs() {
    local server_name="$1"
    local log_file="$LOG_DIR/${server_name}.log"
    
    if [ -f "$log_file" ]; then
        echo "📋 Logs for $server_name:"
        echo "========================"
        tail -50 "$log_file"
    else
        log_error "No log file found for server: $server_name"
    fi
}

function usage() {
    echo "MCP Server Manager for Orchestra AI"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [server]     Start all servers or specific server"
    echo "  stop [server]      Stop all servers or specific server"
    echo "  restart [server]   Restart all servers or specific server"
    echo "  status             Show status of all servers"
    echo "  monitor            Monitor and auto-restart servers"
    echo "  logs [server]      Show logs for specific server"
    echo "  list               List all available servers"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all servers"
    echo "  $0 start enhanced-memory    # Start specific server"
    echo "  $0 status                   # Show all server status"
    echo "  $0 monitor                  # Auto-restart failed servers"
    echo "  $0 logs cherry-domain       # Show Cherry domain logs"
}

function list_servers() {
    echo "Available MCP Servers:"
    echo "====================="
    for server_name in "${!MCP_SERVERS[@]}"; do
        echo "  $server_name"
    done
}

# Main script logic
case "${1:-}" in
    "start")
        if [ -n "${2:-}" ]; then
            if [[ -v "MCP_SERVERS[$2]" ]]; then
                start_server "$2" "${MCP_SERVERS[$2]}"
            else
                log_error "Unknown server: $2"
                exit 1
            fi
        else
            start_all
        fi
        ;;
    "stop")
        if [ -n "${2:-}" ]; then
            stop_server "$2"
        else
            stop_all
        fi
        ;;
    "restart")
        if [ -n "${2:-}" ]; then
            if [[ -v "MCP_SERVERS[$2]" ]]; then
                stop_server "$2"
                sleep 2
                start_server "$2" "${MCP_SERVERS[$2]}"
            else
                log_error "Unknown server: $2"
                exit 1
            fi
        else
            restart_all
        fi
        ;;
    "status")
        status_all
        ;;
    "monitor")
        monitor_servers
        ;;
    "logs")
        if [ -n "${2:-}" ]; then
            show_logs "$2"
        else
            log_error "Please specify a server name"
            usage
            exit 1
        fi
        ;;
    "list")
        list_servers
        ;;
    "help"|"-h"|"--help")
        usage
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        usage
        exit 1
        ;;
esac 
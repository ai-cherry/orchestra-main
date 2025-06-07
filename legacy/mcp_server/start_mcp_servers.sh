#!/bin/bash
"""
🚀 MCP Server Management Script
Professional-grade server orchestration for AI Orchestra
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVERS_DIR="$SCRIPT_DIR/servers"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Server definitions
declare -A SERVERS=(
    ["enhanced-memory"]="enhanced_memory_server.py"
    ["code-intelligence"]="code_intelligence_server.py"
    ["git-intelligence"]="git_intelligence_server.py"
    ["infrastructure-manager"]="infrastructure_manager.py"
    ["prompt-management"]="prompt_management.py"
    ["weaviate-direct"]="weaviate_direct_mcp_server.py"
    ["web-scraping"]="web_scraping_mcp_server.py"
    ["cherry-domain"]="enhanced_cherry_domain_server.py"
    ["sophia-payready"]="sophia_pay_ready_server.py"
)

# Environment variables
export POSTGRES_HOST="45.77.87.106"
export POSTGRES_USER="postgres"
export POSTGRES_DB="cherry_ai"
export REDIS_HOST="45.77.87.106"
export REDIS_PORT="6379"
export WEAVIATE_URL="http://localhost:8080"

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}🚀 MCP Server Management${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_status() {
    local server=$1
    local status=$2
    local color=$3
    printf "%-25s %s\n" "$server" "${color}$status${NC}"
}

check_server_status() {
    local server=$1
    local pid_file="$PID_DIR/${server}.pid"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "running"
            return 0
        else
            # Clean up stale PID file
            rm -f "$pid_file"
            echo "stopped"
            return 1
        fi
    else
        echo "stopped"
        return 1
    fi
}

start_server() {
    local server=$1
    local script="${SERVERS[$server]}"
    local pid_file="$PID_DIR/${server}.pid"
    local log_file="$LOG_DIR/${server}.log"
    
    if [[ -z "$script" ]]; then
        echo -e "${RED}❌ Unknown server: $server${NC}"
        return 1
    fi
    
    if [[ $(check_server_status "$server") == "running" ]]; then
        echo -e "${YELLOW}⚠️  Server $server is already running${NC}"
        return 0
    fi
    
    echo -e "${BLUE}🚀 Starting $server...${NC}"
    
    # Start server in background
    nohup python3 "$SERVERS_DIR/$script" \
        > "$log_file" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$pid_file"
    
    # Wait a moment and check if it started successfully
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ $server started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start $server${NC}"
        rm -f "$pid_file"
        return 1
    fi
}

stop_server() {
    local server=$1
    local pid_file="$PID_DIR/${server}.pid"
    
    if [[ ! -f "$pid_file" ]]; then
        echo -e "${YELLOW}⚠️  Server $server is not running${NC}"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    echo -e "${BLUE}🛑 Stopping $server (PID: $pid)...${NC}"
    
    # Try graceful shutdown first
    if kill -TERM "$pid" 2>/dev/null; then
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
            sleep 1
            ((count++))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Forcing termination of $server${NC}"
            kill -KILL "$pid" 2>/dev/null
        fi
    fi
    
    rm -f "$pid_file"
    echo -e "${GREEN}✅ $server stopped${NC}"
}

restart_server() {
    local server=$1
    echo -e "${BLUE}🔄 Restarting $server...${NC}"
    stop_server "$server"
    sleep 1
    start_server "$server"
}

show_status() {
    print_header
    echo -e "${BLUE}Server Status:${NC}\n"
    
    printf "%-25s %s\n" "SERVER" "STATUS"
    printf "%-25s %s\n" "------" "------"
    
    for server in "${!SERVERS[@]}"; do
        local status=$(check_server_status "$server")
        if [[ "$status" == "running" ]]; then
            print_status "$server" "RUNNING" "$GREEN"
        else
            print_status "$server" "STOPPED" "$RED"
        fi
    done
    
    echo ""
}

show_logs() {
    local server=$1
    local log_file="$LOG_DIR/${server}.log"
    
    if [[ -z "$server" ]]; then
        echo -e "${RED}❌ Please specify a server name${NC}"
        echo "Available servers: ${!SERVERS[*]}"
        return 1
    fi
    
    if [[ ! -f "$log_file" ]]; then
        echo -e "${YELLOW}⚠️  No log file found for $server${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📋 Showing logs for $server:${NC}\n"
    tail -f "$log_file"
}

health_check() {
    print_header
    echo -e "${BLUE}Health Check Results:${NC}\n"
    
    local total=0
    local running=0
    
    for server in "${!SERVERS[@]}"; do
        local status=$(check_server_status "$server")
        ((total++))
        
        if [[ "$status" == "running" ]]; then
            ((running++))
            print_status "$server" "HEALTHY" "$GREEN"
        else
            print_status "$server" "DOWN" "$RED"
        fi
    done
    
    echo ""
    echo -e "${BLUE}Summary: $running/$total servers running${NC}"
    
    if [[ $running -eq $total ]]; then
        echo -e "${GREEN}🎉 All servers are healthy!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Some servers are down${NC}"
        return 1
    fi
}

start_all() {
    print_header
    echo -e "${BLUE}Starting all MCP servers...${NC}\n"
    
    local started=0
    local failed=0
    
    for server in "${!SERVERS[@]}"; do
        if start_server "$server"; then
            ((started++))
        else
            ((failed++))
        fi
    done
    
    echo ""
    echo -e "${BLUE}Summary: $started started, $failed failed${NC}"
    
    if [[ $failed -eq 0 ]]; then
        echo -e "${GREEN}🎉 All servers started successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some servers failed to start${NC}"
    fi
}

stop_all() {
    print_header
    echo -e "${BLUE}Stopping all MCP servers...${NC}\n"
    
    for server in "${!SERVERS[@]}"; do
        stop_server "$server"
    done
    
    echo -e "${GREEN}🎉 All servers stopped${NC}"
}

restart_all() {
    print_header
    echo -e "${BLUE}Restarting all MCP servers...${NC}\n"
    
    stop_all
    sleep 2
    start_all
}

show_help() {
    print_header
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 [command] [server]"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  start [server]     Start a specific server or all servers"
    echo "  stop [server]      Stop a specific server or all servers"
    echo "  restart [server]   Restart a specific server or all servers"
    echo "  status             Show status of all servers"
    echo "  health             Perform health check"
    echo "  logs [server]      Show logs for a specific server"
    echo "  help               Show this help message"
    echo ""
    echo -e "${BLUE}Available servers:${NC}"
    for server in "${!SERVERS[@]}"; do
        echo "  - $server"
    done
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 start                    # Start all servers"
    echo "  $0 start enhanced-memory    # Start specific server"
    echo "  $0 status                   # Show status"
    echo "  $0 logs sophia-payready     # View logs"
}

# Main script logic
case "$1" in
    "start")
        if [[ -n "$2" ]]; then
            start_server "$2"
        else
            start_all
        fi
        ;;
    "stop")
        if [[ -n "$2" ]]; then
            stop_server "$2"
        else
            stop_all
        fi
        ;;
    "restart")
        if [[ -n "$2" ]]; then
            restart_server "$2"
        else
            restart_all
        fi
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    "logs")
        show_logs "$2"
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        show_status
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 
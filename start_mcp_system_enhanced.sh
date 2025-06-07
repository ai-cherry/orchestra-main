#!/bin/bash
# Enhanced MCP System Startup Script with parallel execution, monitoring, and recovery
# Optimized for performance and stability

set -e  # Exit on any error

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="${MCP_LOG_DIR:-$HOME/.mcp/logs}"
PID_DIR="${MCP_PID_DIR:-$HOME/.mcp/pids}"
PARALLEL_STARTUP="${MCP_PARALLEL_STARTUP:-true}"
MAX_STARTUP_TIME="${MCP_MAX_STARTUP_TIME:-60}"
HEALTH_CHECK_INTERVAL="${MCP_HEALTH_CHECK_INTERVAL:-2}"
AUTO_RESTART="${MCP_AUTO_RESTART:-true}"
MEMORY_LIMIT="${MCP_MEMORY_LIMIT:-1G}"
CPU_QUOTA="${MCP_CPU_QUOTA:-80%}"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Log file with timestamp
LOG_FILE="$LOG_DIR/mcp_system_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)  color=$BLUE ;;
        SUCCESS) color=$GREEN ;;
        WARN)  color=$YELLOW ;;
        ERROR) color=$RED ;;
        *) color=$NC ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $message${NC}" | tee -a "$LOG_FILE"
}

# Function to check system requirements
check_system_requirements() {
    log INFO "Checking system requirements..."
    
    # Check Python version
    if ! python3 --version &>/dev/null; then
        log ERROR "Python 3 is not installed"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "./venv" ]; then
        log ERROR "Virtual environment not found. Please run: python3 -m venv venv"
        return 1
    fi
    
    # Check database connectivity
    if ! nc -z "${POSTGRES_HOST:-localhost}" "${POSTGRES_PORT:-5432}" 2>/dev/null; then
        log WARN "PostgreSQL is not accessible at ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}"
    fi
    
    if ! nc -z "${WEAVIATE_HOST:-localhost}" "${WEAVIATE_PORT:-8080}" 2>/dev/null; then
        log WARN "Weaviate is not accessible at ${WEAVIATE_HOST:-localhost}:${WEAVIATE_PORT:-8080}"
    fi
    
    # Check available memory
    available_memory=$(free -m | awk 'NR==2{print $7}')
    if [ "$available_memory" -lt 1024 ]; then
        log WARN "Low available memory: ${available_memory}MB (recommended: 1024MB+)"
    fi
    
    log SUCCESS "System requirements check completed"
    return 0
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

# Function to wait for a service to be healthy with exponential backoff
wait_for_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts="${3:-30}"
    local attempt=0
    local wait_time=1
    
    log INFO "Waiting for $service_name to be healthy at $health_url..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f -m 5 "$health_url" > /dev/null 2>&1; then
            log SUCCESS "$service_name is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log INFO "Health check attempt $attempt/$max_attempts for $service_name (waiting ${wait_time}s)..."
        sleep $wait_time
        
        # Exponential backoff with max wait time of 10 seconds
        wait_time=$((wait_time * 2))
        if [ $wait_time -gt 10 ]; then
            wait_time=10
        fi
    done
    
    log ERROR "$service_name failed to become healthy after $max_attempts attempts"
    return 1
}

# Function to get process info
get_process_info() {
    local pid=$1
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        echo "Not running"
        return 1
    fi
    
    # Get memory and CPU usage
    local stats=$(ps -p "$pid" -o %mem,%cpu,etime --no-headers 2>/dev/null || echo "0 0 00:00")
    echo "PID: $pid, Mem: $(echo $stats | awk '{print $1}')%, CPU: $(echo $stats | awk '{print $2}')%, Uptime: $(echo $stats | awk '{print $3}')"
}

# Enhanced function to start a server with monitoring
start_server_enhanced() {
    local name=$1
    local command=$2
    local port=$3
    local health_endpoint=$4
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    
    log INFO "Starting $name on port $port..."
    
    # Check if already running
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            log WARN "$name is already running ($(get_process_info $old_pid))"
            return 0
        else
            log INFO "Removing stale PID file for $name"
            rm -f "$pid_file"
        fi
    fi
    
    # Check if port is already in use
    if check_port $port; then
        log WARN "Port $port is already in use. Attempting to stop existing process..."
        lsof -ti:$port | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if check_port $port; then
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
    fi
    
    # Start the server with resource limits if systemd-run is available
    if command -v systemd-run >/dev/null 2>&1 && [ "$USE_SYSTEMD" != "false" ]; then
        log INFO "Starting $name with systemd resource limits..."
        systemd-run \
            --uid=$(id -u) \
            --gid=$(id -g) \
            --setenv=HOME=$HOME \
            --setenv=PATH=$PATH \
            --setenv=PYTHONPATH=$PYTHONPATH \
            --property=MemoryLimit=$MEMORY_LIMIT \
            --property=CPUQuota=$CPU_QUOTA \
            --property=StandardOutput=append:$log_file \
            --property=StandardError=append:$log_file \
            --unit="mcp-${name}-$$" \
            --remain-after-exit=no \
            --collect \
            $command &
        local pid=$!
    else
        # Fallback to nohup
        log INFO "Starting $name with nohup..."
        nohup $command > "$log_file" 2>&1 &
        local pid=$!
    fi
    
    echo $pid > "$pid_file"
    log INFO "$name started with PID: $pid"
    
    # Wait for health check
    if wait_for_health "$name" "$health_endpoint" 15; then
        log SUCCESS "$name started successfully ($(get_process_info $pid))"
        return 0
    else:
        log ERROR "Failed to start $name - killing process"
        kill $pid 2>/dev/null || true
        rm -f "$pid_file"
        return 1
    fi
}

# Function to start all servers
start_all_servers() {
    local failed_servers=()
    
    # Define server configurations
    declare -A servers=(
        ["memory"]="./venv/bin/python -m mcp_server.servers.memory_server|8003|http://localhost:8003/health"
        ["conductor"]="./venv/bin/python -m mcp_server.servers.conductor_server|8002|http://localhost:8002/health"
        ["tools"]="./venv/bin/python -m mcp_server.servers.tools_server|8006|http://localhost:8006/health"
        ["weaviate-direct"]="./venv/bin/python -m mcp_server.servers.weaviate_direct_mcp_server|8001|http://localhost:8001/mcp/weaviate_direct/health"
    )
    
    if [ "$PARALLEL_STARTUP" = "true" ]; then
        log INFO "Starting servers in parallel..."
        
        # Start all servers in background
        for server_name in "${!servers[@]}"; do
            IFS='|' read -r command port health_url <<< "${servers[$server_name]}"
            start_server_enhanced "$server_name" "$command" "$port" "$health_url" &
        done
        
        # Wait for all background jobs to complete
        wait
        
        # Check which servers failed
        for server_name in "${!servers[@]}"; do
            pid_file="$PID_DIR/${server_name}.pid"
            if [ ! -f "$pid_file" ] || ! kill -0 "$(cat $pid_file)" 2>/dev/null; then
                failed_servers+=("$server_name")
            fi
        done
    else
        log INFO "Starting servers sequentially..."
        
        for server_name in "${!servers[@]}"; do
            IFS='|' read -r command port health_url <<< "${servers[$server_name]}"
            if ! start_server_enhanced "$server_name" "$command" "$port" "$health_url"; then
                failed_servers+=("$server_name")
            fi
        done
    fi
    
    # Report results
    if [ ${#failed_servers[@]} -eq 0 ]; then
        return 0
    else
        log ERROR "Failed to start servers: ${failed_servers[*]}"
        return 1
    fi
}

# Function to monitor server health
monitor_servers() {
    log INFO "Starting server health monitoring..."
    
    while true; do
        sleep 30  # Check every 30 seconds
        
        for pid_file in "$PID_DIR"/*.pid; do
            [ -f "$pid_file" ] || continue
            
            server_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            
            if ! kill -0 "$pid" 2>/dev/null; then
                log WARN "Server $server_name (PID: $pid) is not running"
                
                if [ "$AUTO_RESTART" = "true" ]; then
                    log INFO "Attempting to restart $server_name..."
                    # Get server config and restart
                    case $server_name in
                        memory)
                            start_server_enhanced "memory" \
                                "./venv/bin/python -m mcp_server.servers.memory_server" \
                                8003 "http://localhost:8003/health"
                            ;;
                        conductor)
                            start_server_enhanced "conductor" \
                                "./venv/bin/python -m mcp_server.servers.conductor_server" \
                                8002 "http://localhost:8002/health"
                            ;;
                        tools)
                            start_server_enhanced "tools" \
                                "./venv/bin/python -m mcp_server.servers.tools_server" \
                                8006 "http://localhost:8006/health"
                            ;;
                        weaviate-direct)
                            start_server_enhanced "weaviate-direct" \
                                "./venv/bin/python -m mcp_server.servers.weaviate_direct_mcp_server" \
                                8001 "http://localhost:8001/mcp/weaviate_direct/health"
                            ;;
                    esac
                fi
            fi
        done
    done
}

# Function to display status
display_status() {
    log INFO "========================================="
    log SUCCESS "MCP System Status"
    log INFO "========================================="
    
    echo ""
    echo "Services:"
    for pid_file in "$PID_DIR"/*.pid; do
        [ -f "$pid_file" ] || continue
        
        server_name=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")
        
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $server_name: $(get_process_info $pid)"
        else
            echo -e "  ${RED}✗${NC} $server_name: Not running"
        fi
    done
    
    echo ""
    echo "Endpoints:"
    echo "  - Memory MCP: http://localhost:8003"
    echo "  - conductor MCP: http://localhost:8002"
    echo "  - Tools MCP: http://localhost:8006"
    echo "  - Weaviate Direct MCP: http://localhost:8001"
    
    echo ""
    echo "Database connections:"
    echo "  - PostgreSQL: ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}"
    echo "  - Weaviate: ${WEAVIATE_HOST:-localhost}:${WEAVIATE_PORT:-8080}"
    
    echo ""
    echo "Logs: $LOG_DIR"
    echo "PIDs: $PID_DIR"
    echo ""
    echo -e "${YELLOW}To stop all services, run: ./stop_mcp_system_enhanced.sh${NC}"
    echo -e "${CYAN}To monitor services, run: tail -f $LOG_DIR/*.log${NC}"
}

# Main execution
main() {
    log INFO "========================================="
    log INFO "Starting Enhanced MCP System"
    log INFO "========================================="
    
    # Check system requirements
    if ! check_system_requirements; then
        log ERROR "System requirements not met. Exiting."
        exit 1
    fi
    
    # Export required environment variables
    export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
    export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    export POSTGRES_DB="${POSTGRES_DB:-cherry_ai}"
    export POSTGRES_USER="${POSTGRES_USER:-postgres}"
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
    
    export WEAVIATE_HOST="${WEAVIATE_HOST:-localhost}"
    export WEAVIATE_PORT="${WEAVIATE_PORT:-8080}"
    export WEAVIATE_API_KEY="${WEAVIATE_API_KEY:-}"
    
    export API_URL="${API_URL:-http://localhost:8080}"
    export API_KEY="${API_KEY:-4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd}"
    
    # Set Python path
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Start all servers
    if start_all_servers; then
        log SUCCESS "All servers started successfully"
        
        # Start monitoring in background if enabled
        if [ "$AUTO_RESTART" = "true" ]; then
            monitor_servers &
            MONITOR_PID=$!
            echo $MONITOR_PID > "$PID_DIR/monitor.pid"
            log INFO "Server monitoring started (PID: $MONITOR_PID)"
        fi
        
        # Display status
        display_status
    else
        log ERROR "Some servers failed to start"
        display_status
        exit 1
    fi
}

# Run main function
main "$@"
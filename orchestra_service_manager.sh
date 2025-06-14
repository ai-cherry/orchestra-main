#!/bin/bash

# 🎼 Orchestra AI - Production Service Manager
# Comprehensive service management for always-running Orchestra AI platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRA_HOME="$SCRIPT_DIR"
LOG_DIR="$ORCHESTRA_HOME/logs/services"
PID_DIR="$ORCHESTRA_HOME/run"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
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

# Create necessary directories
setup_directories() {
    log "Setting up Orchestra AI directories..."
    
    sudo mkdir -p "$LOG_DIR" "$PID_DIR"
    sudo chown -R ubuntu:ubuntu "$LOG_DIR" "$PID_DIR"
    
    # Create service-specific log directories
    mkdir -p "$LOG_DIR"/{api,frontend,mcp-memory,mcp-task,mcp-agent,mcp-data,mcp-monitor}
    
    success "Directories created successfully"
}

# Check if service is running
is_service_running() {
    local service_name=$1
    local port=$2
    
    if command -v systemctl >/dev/null 2>&1; then
        systemctl is-active --quiet "$service_name" 2>/dev/null
    else
        # Fallback: check if port is in use
        netstat -tlnp 2>/dev/null | grep -q ":$port " 2>/dev/null
    fi
}

# Health check function
health_check() {
    local service_name=$1
    local url=$2
    local max_retries=${3:-3}
    local retry_delay=${4:-5}
    
    log "Performing health check for $service_name..."
    
    for i in $(seq 1 $max_retries); do
        if curl -sf "$url" >/dev/null 2>&1; then
            success "$service_name is healthy"
            return 0
        fi
        
        if [ $i -lt $max_retries ]; then
            warning "Health check failed for $service_name (attempt $i/$max_retries), retrying in ${retry_delay}s..."
            sleep $retry_delay
        fi
    done
    
    error "Health check failed for $service_name after $max_retries attempts"
    return 1
}

# Start API service
start_api() {
    log "Starting Orchestra AI API..."
    
    if is_service_running "orchestra-api" 8000; then
        warning "API service is already running"
        return 0
    fi
    
    cd "$ORCHESTRA_HOME"
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Start API with proper logging
    nohup uvicorn api.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --log-level info \
        --access-log \
        > "$LOG_DIR/api/access.log" 2> "$LOG_DIR/api/error.log" &
    
    echo $! > "$PID_DIR/api.pid"
    
    # Wait for service to start
    sleep 5
    
    if health_check "API" "http://localhost:8000/api/health/"; then
        success "API service started successfully"
    else
        error "Failed to start API service"
        return 1
    fi
}

# Start Frontend service
start_frontend() {
    log "Starting Orchestra AI Frontend..."
    
    if is_service_running "orchestra-frontend" 3000; then
        warning "Frontend service is already running"
        return 0
    fi
    
    cd "$ORCHESTRA_HOME/modern-admin"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log "Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend with proper logging
    nohup npm run dev -- --host 0.0.0.0 --port 3000 \
        > "$LOG_DIR/frontend/access.log" 2> "$LOG_DIR/frontend/error.log" &
    
    echo $! > "$PID_DIR/frontend.pid"
    
    # Wait for service to start
    sleep 10
    
    if health_check "Frontend" "http://localhost:3000" 5 3; then
        success "Frontend service started successfully"
    else
        error "Failed to start frontend service"
        return 1
    fi
}

# Start MCP server
start_mcp_server() {
    local server_name=$1
    local port=$2
    local script_path=$3
    
    log "Starting MCP $server_name server..."
    
    if is_service_running "orchestra-mcp-$server_name" $port; then
        warning "MCP $server_name server is already running"
        return 0
    fi
    
    cd "$ORCHESTRA_HOME"
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Start MCP server with proper logging
    nohup python "$script_path" \
        > "$LOG_DIR/mcp-$server_name/access.log" 2> "$LOG_DIR/mcp-$server_name/error.log" &
    
    echo $! > "$PID_DIR/mcp-$server_name.pid"
    
    # Wait for service to start
    sleep 3
    
    if health_check "MCP $server_name" "http://localhost:$port/health" 3 2; then
        success "MCP $server_name server started successfully"
    else
        warning "MCP $server_name server may not have started properly"
    fi
}

# Start all MCP servers
start_mcp_servers() {
    log "Starting all MCP servers..."
    
    # Define MCP servers (name, port, script)
    declare -a mcp_servers=(
        "memory:8003:start_mcp_memory.py"
        # "task:8006:mcp_task_server.py"
        # "agent:8007:mcp_agent_server.py"
        # "data:8008:mcp_data_server.py"
        # "monitor:8009:mcp_monitor_server.py"
    )
    
    for server_config in "${mcp_servers[@]}"; do
        IFS=':' read -r name port script <<< "$server_config"
        
        # Check if script exists
        if [ -f "$ORCHESTRA_HOME/$script" ]; then
            start_mcp_server "$name" "$port" "$script"
        else
            warning "MCP $name server script not found: $script"
        fi
    done
}

# Stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/$service_name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            
            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                warning "Force killing $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            rm -f "$pid_file"
            success "$service_name stopped"
        else
            warning "$service_name PID file exists but process is not running"
            rm -f "$pid_file"
        fi
    else
        warning "No PID file found for $service_name"
    fi
}

# Stop all services
stop_all() {
    log "Stopping all Orchestra AI services..."
    
    # Stop services in reverse order
    stop_service "mcp-monitor"
    stop_service "mcp-data"
    stop_service "mcp-agent"
    stop_service "mcp-task"
    stop_service "mcp-memory"
    stop_service "frontend"
    stop_service "api"
    
    # Clean up any remaining processes
    pkill -f "uvicorn.*api.main" 2>/dev/null || true
    pkill -f "vite.*--host" 2>/dev/null || true
    pkill -f "mcp.*server" 2>/dev/null || true
    
    success "All services stopped"
}

# Start all services
start_all() {
    log "Starting all Orchestra AI services..."
    
    setup_directories
    
    # Start services in order
    start_api
    sleep 2
    start_frontend
    sleep 2
    start_mcp_servers
    
    success "All services started successfully"
    
    # Display service status
    status
}

# Show service status
status() {
    echo ""
    echo "🎼 Orchestra AI Service Status"
    echo "=============================="
    
    # Check API
    if health_check "API" "http://localhost:8000/api/health/" 1 1 >/dev/null 2>&1; then
        echo -e "API (Port 8000):           ${GREEN}RUNNING${NC}"
    else
        echo -e "API (Port 8000):           ${RED}STOPPED${NC}"
    fi
    
    # Check Frontend
    if health_check "Frontend" "http://localhost:3000" 1 1 >/dev/null 2>&1; then
        echo -e "Frontend (Port 3000):      ${GREEN}RUNNING${NC}"
    else
        echo -e "Frontend (Port 3000):      ${RED}STOPPED${NC}"
    fi
    
    # Check MCP servers
    declare -a mcp_ports=(8003 8006 8007 8008 8009)
    declare -a mcp_names=("Memory" "Task" "Agent" "Data" "Monitor")
    
    for i in "${!mcp_ports[@]}"; do
        local port=${mcp_ports[$i]}
        local name=${mcp_names[$i]}
        
        if health_check "MCP $name" "http://localhost:$port/health" 1 1 >/dev/null 2>&1; then
            echo -e "MCP $name (Port $port):    ${GREEN}RUNNING${NC}"
        else
            echo -e "MCP $name (Port $port):    ${RED}STOPPED${NC}"
        fi
    done
    
    echo ""
    echo "🔗 Service URLs:"
    echo "   Frontend:    http://localhost:3000"
    echo "   API:         http://localhost:8000"
    echo "   API Docs:    http://localhost:8000/docs"
    echo "   Health:      http://localhost:8000/api/health/"
    echo ""
}

# Restart all services
restart() {
    log "Restarting all Orchestra AI services..."
    stop_all
    sleep 3
    start_all
}

# Show logs
logs() {
    local service=${1:-"all"}
    
    if [ "$service" = "all" ]; then
        echo "🎼 Orchestra AI - Recent Logs"
        echo "============================="
        
        for log_file in "$LOG_DIR"/*/*.log; do
            if [ -f "$log_file" ]; then
                echo ""
                echo "=== $(basename "$(dirname "$log_file")")/$(basename "$log_file") ==="
                tail -n 10 "$log_file"
            fi
        done
    else
        if [ -d "$LOG_DIR/$service" ]; then
            echo "🎼 Orchestra AI - $service Logs"
            echo "==============================="
            
            for log_file in "$LOG_DIR/$service"/*.log; do
                if [ -f "$log_file" ]; then
                    echo ""
                    echo "=== $(basename "$log_file") ==="
                    tail -n 20 "$log_file"
                fi
            done
        else
            error "Service '$service' not found. Available services: api, frontend, mcp-memory, mcp-task, mcp-agent, mcp-data, mcp-monitor"
        fi
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "${2:-all}"
        ;;
    api)
        case "${2:-start}" in
            start) start_api ;;
            stop) stop_service "api" ;;
            restart) stop_service "api"; sleep 2; start_api ;;
            *) echo "Usage: $0 api {start|stop|restart}" ;;
        esac
        ;;
    frontend)
        case "${2:-start}" in
            start) start_frontend ;;
            stop) stop_service "frontend" ;;
            restart) stop_service "frontend"; sleep 2; start_frontend ;;
            *) echo "Usage: $0 frontend {start|stop|restart}" ;;
        esac
        ;;
    mcp)
        case "${2:-start}" in
            start) start_mcp_servers ;;
            stop) 
                stop_service "mcp-monitor"
                stop_service "mcp-data"
                stop_service "mcp-agent"
                stop_service "mcp-task"
                stop_service "mcp-memory"
                ;;
            restart) 
                stop_service "mcp-monitor"
                stop_service "mcp-data"
                stop_service "mcp-agent"
                stop_service "mcp-task"
                stop_service "mcp-memory"
                sleep 2
                start_mcp_servers
                ;;
            *) echo "Usage: $0 mcp {start|stop|restart}" ;;
        esac
        ;;
    health)
        log "Performing comprehensive health check..."
        
        # Check all services
        health_check "API" "http://localhost:8000/api/health/"
        health_check "Frontend" "http://localhost:3000" 3 2
        
        # Check MCP servers
        declare -a mcp_ports=(8003 8006 8007 8008 8009)
        declare -a mcp_names=("Memory" "Task" "Agent" "Data" "Monitor")
        
        for i in "${!mcp_ports[@]}"; do
            health_check "MCP ${mcp_names[$i]}" "http://localhost:${mcp_ports[$i]}/health" 2 1
        done
        ;;
    *)
        echo "🎼 Orchestra AI - Production Service Manager"
        echo "==========================================="
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|health}"
        echo ""
        echo "Commands:"
        echo "  start          Start all services"
        echo "  stop           Stop all services"
        echo "  restart        Restart all services"
        echo "  status         Show service status"
        echo "  logs [service] Show logs (all or specific service)"
        echo "  health         Perform health checks"
        echo ""
        echo "Service-specific commands:"
        echo "  api {start|stop|restart}       Manage API service"
        echo "  frontend {start|stop|restart}  Manage Frontend service"
        echo "  mcp {start|stop|restart}       Manage MCP servers"
        echo ""
        echo "Examples:"
        echo "  $0 start                Start all services"
        echo "  $0 status               Show service status"
        echo "  $0 logs api             Show API logs"
        echo "  $0 api restart          Restart only API service"
        echo ""
        exit 1
        ;;
esac


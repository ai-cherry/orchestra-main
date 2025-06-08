#!/bin/bash
# 🎯 Orchestra AI - Roo Code System Manager
# Comprehensive management for 100% stable Roo integration

set -e

# Colors and logging
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

LOG_DIR="$HOME/.roo/logs"
PID_DIR="$HOME/.roo/pids"
CONFIG_DIR=".roo"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$PID_DIR"

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; }

# MCP Server configurations
declare -A MCP_SERVERS=(
    ["roo-main"]="mcp_roo_server.py:8000"
    ["infrastructure"]="mcp_infrastructure_server.py:8009" 
    ["weaviate"]="mcp_weaviate_server.py:8011"
)

# Function to check if server is running
is_server_running() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Function to start a server
start_server() {
    local name=$1
    local config=${MCP_SERVERS[$name]}
    local script=$(echo $config | cut -d: -f1)
    local port=$(echo $config | cut -d: -f2)
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    
    if is_server_running "$name"; then
        log "✅ $name already running"
        return 0
    fi
    
    if [ ! -f "$script" ]; then
        error "❌ Script $script not found"
        return 1
    fi
    
    info "🚀 Starting $name on port $port..."
    
    # Load environment
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Start server
    nohup python "$script" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Health check
    sleep 3
    if is_server_running "$name"; then
        # Test port connectivity
        if curl -s "http://localhost:${port}/health" >/dev/null 2>&1; then
            log "✅ $name started successfully (PID: $pid, Port: $port)"
            return 0
        else
            warn "⚠️ $name started but health check failed"
            return 1
        fi
    else
        error "❌ $name failed to start"
        if [ -f "$log_file" ]; then
            echo "Last 5 log lines:"
            tail -5 "$log_file"
        fi
        return 1
    fi
}

# Function to stop a server
stop_server() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            info "🛑 Stopping $name (PID: $pid)..."
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                warn "Force killing $name..."
                kill -9 "$pid"
            fi
            log "✅ $name stopped"
        fi
        rm -f "$pid_file"
    else
        warn "⚠️ $name not running or PID file missing"
    fi
}

# Function to check system health
health_check() {
    echo -e "${CYAN}🎯 ROO SYSTEM HEALTH CHECK${NC}"
    echo "================================"
    
    local all_healthy=true
    
    # Check MCP servers
    info "🔧 MCP Servers:"
    for name in "${!MCP_SERVERS[@]}"; do
        local config=${MCP_SERVERS[$name]}
        local port=$(echo $config | cut -d: -f2)
        
        if is_server_running "$name"; then
            if curl -s "http://localhost:${port}/health" >/dev/null 2>&1; then
                echo -e "   ${GREEN}✅ $name${NC}: Running & Healthy (Port: $port)"
            else
                echo -e "   ${YELLOW}⚠️ $name${NC}: Running but unhealthy"
                all_healthy=false
            fi
        else
            echo -e "   ${RED}❌ $name${NC}: Not running"
            all_healthy=false
        fi
    done
    
    # Check configurations
    info "📋 Configurations:"
    if [ -f "$CONFIG_DIR/config.json" ]; then
        echo -e "   ${GREEN}✅ Main config${NC}: Present"
    else
        echo -e "   ${RED}❌ Main config${NC}: Missing"
        all_healthy=false
    fi
    
    if [ -f "$CONFIG_DIR/mcp.json" ]; then
        echo -e "   ${GREEN}✅ MCP config${NC}: Present"
    else
        echo -e "   ${RED}❌ MCP config${NC}: Missing"
        all_healthy=false
    fi
    
    local mode_count=$(find "$CONFIG_DIR/modes" -name "*.json" 2>/dev/null | wc -l)
    echo -e "   ${GREEN}✅ Modes${NC}: $mode_count configured"
    
    # Check environment
    info "🌐 Environment:"
    if [ -f .env ]; then
        local env_vars=("OPENROUTER_API_KEY" "OPENAI_API_KEY" "POSTGRES_HOST" "REDIS_HOST" "WEAVIATE_URL")
        for var in "${env_vars[@]}"; do
            if grep -q "^${var}=" .env; then
                echo -e "   ${GREEN}✅ $var${NC}: Configured"
            else
                echo -e "   ${RED}❌ $var${NC}: Missing"
                all_healthy=false
            fi
        done
    else
        echo -e "   ${RED}❌ .env file${NC}: Missing"
        all_healthy=false
    fi
    
    # Check VS Code integration
    info "🖥️ VS Code Integration:"
    local vscode_files=("settings.json" "launch.json" "tasks.json")
    for file in "${vscode_files[@]}"; do
        if [ -f ".vscode/$file" ]; then
            echo -e "   ${GREEN}✅ $file${NC}: Present"
        else
            echo -e "   ${RED}❌ $file${NC}: Missing"
            all_healthy=false
        fi
    done
    
    echo ""
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}🎉 SYSTEM STATUS: EXCELLENT (100% Healthy)${NC}"
        echo -e "${GREEN}🚀 Ready for production Roo Code usage!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ SYSTEM STATUS: NEEDS ATTENTION${NC}"
        echo -e "${YELLOW}Run: $0 repair${NC}"
        return 1
    fi
}

# Function to repair common issues
repair_system() {
    log "🔧 Repairing Roo system..."
    
    # Restart all servers
    for name in "${!MCP_SERVERS[@]}"; do
        stop_server "$name"
        start_server "$name"
    done
    
    # Run health check
    sleep 5
    health_check
}

# Function to show usage
show_usage() {
    echo -e "${CYAN}🪃 Roo System Manager Usage${NC}"
    echo "=============================="
    echo ""
    echo "Commands:"
    echo "  start       - Start all MCP servers"
    echo "  stop        - Stop all MCP servers"
    echo "  restart     - Restart all MCP servers"
    echo "  status      - Show detailed system status"
    echo "  health      - Run comprehensive health check"
    echo "  repair      - Attempt to repair issues"
    echo "  logs [name] - Show logs for specific server"
    echo ""
    echo "Server names: ${!MCP_SERVERS[*]}"
}

# Main command processing
case "${1:-status}" in
    start)
        log "🚀 Starting Roo system..."
        for name in "${!MCP_SERVERS[@]}"; do
            start_server "$name"
        done
        echo ""
        health_check
        ;;
    
    stop)
        log "🛑 Stopping Roo system..."
        for name in "${!MCP_SERVERS[@]}"; do
            stop_server "$name"
        done
        ;;
        
    restart)
        log "🔄 Restarting Roo system..."
        for name in "${!MCP_SERVERS[@]}"; do
            stop_server "$name"
        done
        sleep 2
        for name in "${!MCP_SERVERS[@]}"; do
            start_server "$name"
        done
        echo ""
        health_check
        ;;
        
    status|health)
        health_check
        ;;
        
    repair)
        repair_system
        ;;
        
    logs)
        if [ -n "$2" ]; then
            local log_file="$LOG_DIR/${2}.log"
            if [ -f "$log_file" ]; then
                echo -e "${CYAN}📋 Logs for $2:${NC}"
                tail -50 "$log_file"
            else
                error "Log file for $2 not found"
            fi
        else
            echo "Available logs:"
            ls -1 "$LOG_DIR"/*.log 2>/dev/null | xargs -I {} basename {} .log || echo "No logs found"
        fi
        ;;
        
    *)
        show_usage
        ;;
esac 
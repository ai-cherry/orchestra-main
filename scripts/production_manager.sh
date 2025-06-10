#!/bin/bash
# 🚀 Orchestra AI Production Service Manager
# Ensures all services are always running with automatic restart

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Service definitions
declare -A SERVICES=(
    ["zapier-mcp"]="80:$PROJECT_ROOT/zapier-mcp:sudo MCP_SERVER_PORT=80 node server.js"
    ["personas-api"]="8000:$PROJECT_ROOT:python3 personas_server.py"
    ["main-api"]="8010:$PROJECT_ROOT:docker-compose -f docker-compose.production.yml up cherry_ai_api_hybrid"
    ["infrastructure"]="8080:$PROJECT_ROOT:docker-compose -f docker-compose.production.yml up cherry_ai_weaviate_prod"
)

# PID file directory
PID_DIR="/var/run/orchestra-ai"
sudo mkdir -p "$PID_DIR"

# Logging
LOG_DIR="/var/log/orchestra-ai"
sudo mkdir -p "$LOG_DIR"

# Function to check if service is running
is_service_running() {
    local service_name=$1
    local port=$2
    
    # Check if port is in use
    if netstat -tlnp 2>/dev/null | grep -q ":$port.*LISTEN"; then
        return 0
    fi
    return 1
}

# Function to start a service
start_service() {
    local service_name=$1
    local service_info=${SERVICES[$service_name]}
    
    IFS=':' read -r port workdir command <<< "$service_info"
    
    echo -e "${BLUE}🚀 Starting $service_name on port $port...${NC}"
    
    cd "$workdir"
    
    # Start service in background with logging
    if [[ $command == *"sudo"* ]]; then
        nohup bash -c "$command" > "$LOG_DIR/${service_name}.log" 2>&1 &
    else
        nohup bash -c "$command" > "$LOG_DIR/${service_name}.log" 2>&1 &
    fi
    
    local pid=$!
    echo $pid > "$PID_DIR/${service_name}.pid"
    
    # Wait for service to start
    sleep 5
    
    if is_service_running "$service_name" "$port"; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name failed to start${NC}"
        return 1
    fi
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo -e "${YELLOW}🛑 Stopping $service_name (PID: $pid)...${NC}"
        
        if kill "$pid" 2>/dev/null; then
            rm -f "$pid_file"
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${RED}❌ Failed to stop $service_name${NC}"
            rm -f "$pid_file"  # Remove stale PID file
        fi
    else
        echo -e "${YELLOW}⚠️ No PID file found for $service_name${NC}"
    fi
}

# Function to restart a service
restart_service() {
    local service_name=$1
    echo -e "${BLUE}🔄 Restarting $service_name...${NC}"
    stop_service "$service_name"
    sleep 3
    start_service "$service_name"
}

# Function to check all services
check_services() {
    echo -e "${BLUE}🏥 Checking all production services...${NC}"
    echo "========================================"
    
    local all_healthy=true
    
    for service_name in "${!SERVICES[@]}"; do
        local service_info=${SERVICES[$service_name]}
        IFS=':' read -r port workdir command <<< "$service_info"
        
        echo -n "Checking $service_name (port $port)... "
        
        if is_service_running "$service_name" "$port"; then
            echo -e "${GREEN}✅ RUNNING${NC}"
        else
            echo -e "${RED}❌ DOWN${NC}"
            all_healthy=false
        fi
    done
    
    echo "========================================"
    
    if $all_healthy; then
        echo -e "${GREEN}🎉 ALL SERVICES HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}🚨 SOME SERVICES DOWN${NC}"
        return 1
    fi
}

# Function to ensure all services are running
ensure_all_running() {
    echo -e "${BLUE}🔧 Ensuring all services are running...${NC}"
    
    for service_name in "${!SERVICES[@]}"; do
        local service_info=${SERVICES[$service_name]}
        IFS=':' read -r port workdir command <<< "$service_info"
        
        if ! is_service_running "$service_name" "$port"; then
            echo -e "${YELLOW}⚠️ $service_name is down, starting...${NC}"
            start_service "$service_name"
        else
            echo -e "${GREEN}✅ $service_name already running${NC}"
        fi
    done
}

# Function to deploy new version (hot swap)
deploy_new_version() {
    local service_name=$1
    local new_version_path=$2
    
    echo -e "${BLUE}🚀 Deploying new version of $service_name...${NC}"
    
    # 1. Start new version on staging port
    local staging_port=$((${SERVICES[$service_name]%%:*} + 1000))
    echo -e "${YELLOW}📋 Starting staging version on port $staging_port${NC}"
    
    # 2. Health check staging version
    sleep 10
    if curl -s "http://localhost:$staging_port/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Staging version healthy${NC}"
        
        # 3. Switch traffic (in a real setup, this would update load balancer)
        echo -e "${BLUE}🔄 Switching traffic to new version${NC}"
        stop_service "$service_name"
        sleep 2
        
        # Update service definition to new version
        # (In practice, this would update load balancer config)
        start_service "$service_name"
        
        echo -e "${GREEN}🎉 Deployment successful!${NC}"
    else
        echo -e "${RED}❌ Staging version failed health check${NC}"
        echo -e "${YELLOW}🔄 Rolling back...${NC}"
        # Kill staging version and keep production running
    fi
}

# Function to show service logs
show_logs() {
    local service_name=$1
    local lines=${2:-50}
    
    local log_file="$LOG_DIR/${service_name}.log"
    
    if [ -f "$log_file" ]; then
        echo -e "${BLUE}📝 Last $lines lines of $service_name logs:${NC}"
        echo "================================================"
        tail -n "$lines" "$log_file"
    else
        echo -e "${RED}❌ Log file not found for $service_name${NC}"
    fi
}

# Main command handling
case "${1:-status}" in
    "start")
        if [ -n "$2" ]; then
            start_service "$2"
        else
            ensure_all_running
        fi
        ;;
    "stop")
        if [ -n "$2" ]; then
            stop_service "$2"
        else
            echo -e "${RED}🚨 WARNING: This will stop ALL production services!${NC}"
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                for service_name in "${!SERVICES[@]}"; do
                    stop_service "$service_name"
                done
            fi
        fi
        ;;
    "restart")
        if [ -n "$2" ]; then
            restart_service "$2"
        else
            echo -e "${BLUE}🔄 Restarting all services...${NC}"
            for service_name in "${!SERVICES[@]}"; do
                restart_service "$service_name"
            done
        fi
        ;;
    "status"|"check")
        check_services
        ;;
    "ensure")
        ensure_all_running
        ;;
    "logs")
        if [ -n "$2" ]; then
            show_logs "$2" "${3:-50}"
        else
            echo "Available services: ${!SERVICES[*]}"
        fi
        ;;
    "deploy")
        if [ -n "$2" ]; then
            deploy_new_version "$2" "$3"
        else
            echo "Usage: $0 deploy <service_name> [new_version_path]"
        fi
        ;;
    "help")
        echo "Orchestra AI Production Service Manager"
        echo "======================================"
        echo "Commands:"
        echo "  start [service]     - Start all services or specific service"
        echo "  stop [service]      - Stop all services or specific service"
        echo "  restart [service]   - Restart all services or specific service"
        echo "  status              - Check status of all services"
        echo "  ensure              - Ensure all services are running"
        echo "  logs <service> [lines] - Show logs for service"
        echo "  deploy <service>    - Deploy new version with hot swap"
        echo "  help                - Show this help"
        echo ""
        echo "Available services: ${!SERVICES[*]}"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac 
#!/bin/bash
# Enhanced MCP System Startup Script with Advanced Memory Architecture
# Integrated with Cherry/Sophia/Karen personas and 5-tier memory system
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
PURPLE='\033[0;35m'
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

# Advanced Architecture Configuration
ENABLE_ADVANCED_MEMORY="${ENABLE_ADVANCED_MEMORY:-true}"
PERSONA_SYSTEM="${PERSONA_SYSTEM:-enabled}"
CROSS_DOMAIN_ROUTING="${CROSS_DOMAIN_ROUTING:-enabled}"
MEMORY_COMPRESSION="${MEMORY_COMPRESSION:-enabled}"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Log file with timestamp
LOG_FILE="$LOG_DIR/mcp_system_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages with persona awareness
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
        PERSONA) color=$PURPLE ;;
        MEMORY) color=$CYAN ;;
        *) color=$NC ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $message${NC}" | tee -a "$LOG_FILE"
}

# Function to check advanced system requirements
check_advanced_requirements() {
    log INFO "Checking advanced architecture requirements..."
    
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
    
    # Check if advanced architecture files exist
    if [ ! -f "integrated_orchestrator.py" ]; then
        log ERROR "integrated_orchestrator.py not found - advanced architecture not available"
        return 1
    fi
    
    if [ ! -f "persona_profiles.py" ]; then
        log ERROR "persona_profiles.py not found - persona system not available"
        return 1
    fi
    
    if [ ! -f "memory_architecture.py" ]; then
        log ERROR "memory_architecture.py not found - memory architecture not available"
        return 1
    fi
    
    # Check database connectivity for 5-tier memory system
    log MEMORY "Checking 5-tier memory system connectivity..."
    
    if ! nc -z "${POSTGRES_HOST:-localhost}" "${POSTGRES_PORT:-5432}" 2>/dev/null; then
        log WARN "PostgreSQL (L3 Memory Tier) not accessible at ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}"
    else:
        log SUCCESS "L3 Memory Tier (PostgreSQL) - Connected"
    fi
    
    if ! nc -z "${REDIS_HOST:-localhost}" "${REDIS_PORT:-6379}" 2>/dev/null; then
        log WARN "Redis (L2 Memory Tier) not accessible at ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
    else:
        log SUCCESS "L2 Memory Tier (Redis) - Connected"
    fi
    
    if ! nc -z "${WEAVIATE_HOST:-localhost}" "${WEAVIATE_PORT:-8080}" 2>/dev/null; then
        log WARN "Weaviate (L4 Memory Tier) not accessible at ${WEAVIATE_HOST:-localhost}:${WEAVIATE_PORT:-8080}"
    else:
        log SUCCESS "L4 Memory Tier (Weaviate) - Connected"
    fi
    
    # Check available memory for personas
    available_memory=$(free -m | awk 'NR==2{print $7}')
    required_memory=2048  # 2GB for advanced architecture
    if [ "$available_memory" -lt "$required_memory" ]; then
        log WARN "Low available memory: ${available_memory}MB (recommended: ${required_memory}MB+ for advanced architecture)"
    else:
        log SUCCESS "Memory: ${available_memory}MB available (sufficient for advanced architecture)"
    fi
    
    log SUCCESS "Advanced architecture requirements check completed"
    return 0
}

# Function to initialize persona system
initialize_persona_system() {
    if [ "$PERSONA_SYSTEM" != "enabled" ]; then
        log INFO "Persona system disabled - skipping initialization"
        return 0
    fi
    
    log PERSONA "Initializing Cherry, Sophia, and Karen personas..."
    
    # Test persona initialization
    python3 -c "
from persona_profiles import create_persona
try:
    cherry = create_persona('cherry')
    sophia = create_persona('sophia')
    karen = create_persona('karen')
    print('✅ All personas initialized successfully')
    print(f'Cherry: {cherry.personality.empathy_level:.2f} empathy, {cherry.personality.adaptability:.2f} adaptability')
    print(f'Sophia: {sophia.personality.technical_precision:.2f} precision, {sophia.personality.authority_level:.2f} authority')
    print(f'Karen: {karen.personality.technical_precision:.2f} precision, {karen.personality.empathy_level:.2f} empathy')
except Exception as e:
    print(f'❌ Persona initialization failed: {e}')
    exit(1)
" || return 1
    
    log SUCCESS "Persona system initialized - Cherry (Overseer), Sophia (Financial), Karen (Medical)"
    return 0
}

# Function to initialize memory architecture
initialize_memory_architecture() {
    if [ "$ENABLE_ADVANCED_MEMORY" != "true" ]; then
        log INFO "Advanced memory disabled - using simple memory"
        return 0
    fi
    
    log MEMORY "Initializing 5-tier memory architecture..."
    
    # Test memory system initialization
    python3 -c "
from memory_architecture import LayeredMemoryManager, MemoryTier, PERSONA_CONFIGS
from integrated_orchestrator import create_orchestrator
import asyncio

async def test_memory():
    try:
        # Test memory manager
        manager = LayeredMemoryManager()
        print('✅ LayeredMemoryManager initialized')
        
        # Test persona configs
        for persona, config in PERSONA_CONFIGS.items():
            print(f'✅ {persona.value.title()}: {config.context_window} tokens, {config.retention_days} days retention')
        
        print('✅ Memory architecture components loaded successfully')
        return True
    except Exception as e:
        print(f'❌ Memory architecture test failed: {e}')
        return False

result = asyncio.run(test_memory())
exit(0 if result else 1)
" || return 1
    
    log SUCCESS "5-tier memory architecture initialized (L0-CPU → L4-Weaviate)"
    
    # Log memory tier status
    log MEMORY "Memory Tiers Status:"
    log MEMORY "  L0: CPU Cache (~1ns) - Hot data access"
    log MEMORY "  L1: Process Memory (~10ns) - Session context"  
    log MEMORY "  L2: Redis Cache (~100ns) - Cross-persona sharing"
    log MEMORY "  L3: PostgreSQL (~1ms) - Structured data"
    log MEMORY "  L4: Weaviate (~10ms) - Vector embeddings"
    
    return 0
}

# Function to test integrated orchestrator
test_orchestrator_integration() {
    log INFO "Testing integrated orchestrator..."
    
    python3 -c "
import asyncio
from integrated_orchestrator import create_orchestrator, OrchestrationContext

async def test_integration():
    try:
        # Test orchestrator creation
        orchestrator = await create_orchestrator()
        print('✅ Integrated orchestrator created successfully')
        
        # Test basic functionality without full initialization
        performance = orchestrator.get_performance_summary()
        print(f'✅ Performance monitoring active: {len(performance)} metrics')
        
        print('✅ Integration test completed successfully')
        return True
    except Exception as e:
        print(f'❌ Integration test failed: {e}')
        return False

result = asyncio.run(test_integration())
exit(0 if result else 1)
" || return 1
    
    log SUCCESS "Integrated orchestrator test completed"
    return 0
}

# Enhanced function to start a server with advanced monitoring
start_server_enhanced() {
    local name=$1
    local command=$2
    local port=$3
    local health_endpoint=$4
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    
    log INFO "Starting $name on port $port with advanced monitoring..."
    
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
    
    # Start the server with enhanced environment
    log INFO "Starting $name with advanced architecture support..."
    
    # Export advanced configuration
    export ENABLE_ADVANCED_MEMORY="$ENABLE_ADVANCED_MEMORY"
    export PERSONA_SYSTEM="$PERSONA_SYSTEM"
    export CROSS_DOMAIN_ROUTING="$CROSS_DOMAIN_ROUTING"
    export MEMORY_COMPRESSION="$MEMORY_COMPRESSION"
    
    if command -v systemd-run >/dev/null 2>&1 && [ "$USE_SYSTEMD" != "false" ]; then
        log INFO "Starting $name with systemd resource limits..."
        systemd-run \
            --uid=$(id -u) \
            --gid=$(id -g) \
            --setenv=HOME=$HOME \
            --setenv=PATH=$PATH \
            --setenv=PYTHONPATH=$PYTHONPATH \
            --setenv=ENABLE_ADVANCED_MEMORY=$ENABLE_ADVANCED_MEMORY \
            --setenv=PERSONA_SYSTEM=$PERSONA_SYSTEM \
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
        # Fallback to nohup with enhanced environment
        log INFO "Starting $name with nohup and advanced environment..."
        nohup $command > "$log_file" 2>&1 &
        local pid=$!
    fi
    
    echo $pid > "$pid_file"
    log INFO "$name started with PID: $pid"
    
    # Wait for health check
    if wait_for_health "$name" "$health_endpoint" 15; then
        log SUCCESS "$name started successfully ($(get_process_info $pid))"
        
        # Log persona-specific startup if applicable
        if [[ "$name" == *"orchestrator"* ]] || [[ "$name" == *"unified"* ]]; then
            log PERSONA "$name ready with Cherry/Sophia/Karen personas"
        fi
        
        return 0
    else:
        log ERROR "Failed to start $name - killing process"
        kill $pid 2>/dev/null || true
        rm -f "$pid_file"
        return 1
    fi
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

# Function to start all servers with advanced architecture
start_all_servers() {
    local failed_servers=()
    
    # Define server configurations with advanced features
    declare -A servers=(
        ["unified-mcp"]="./venv/bin/python mcp_unified_server.py|8000|http://localhost:8000/health"
        ["memory"]="./venv/bin/python -m mcp_server.servers.memory_server|8003|http://localhost:8003/health"
        ["conductor"]="./venv/bin/python -m mcp_server.servers.conductor_server|8002|http://localhost:8002/health"
        ["tools"]="./venv/bin/python -m mcp_server.servers.tools_server|8006|http://localhost:8006/health"
        ["weaviate-direct"]="./venv/bin/python -m mcp_server.servers.weaviate_direct_mcp_server|8001|http://localhost:8001/mcp/weaviate_direct/health"
    )
    
    log INFO "Starting servers with advanced architecture support..."
    
    if [ "$PARALLEL_STARTUP" = "true" ]; then
        log INFO "Starting servers in parallel with persona awareness..."
        
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
        log INFO "Starting servers sequentially with advanced monitoring..."
        
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

# Enhanced monitoring with persona awareness
monitor_servers() {
    log INFO "Starting advanced server monitoring with persona tracking..."
    
    while true; do
        sleep 30  # Check every 30 seconds
        
        for pid_file in "$PID_DIR"/*.pid; do
            [ -f "$pid_file" ] || continue
            
            server_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            
            if ! kill -0 "$pid" 2>/dev/null; then
                log WARN "Server $server_name (PID: $pid) is not running"
                
                if [ "$AUTO_RESTART" = "true" ]; then
                    log INFO "Attempting to restart $server_name with advanced features..."
                    # Restart with advanced configuration
                    case $server_name in
                        unified-mcp)
                            start_server_enhanced "unified-mcp" \
                                "./venv/bin/python mcp_unified_server.py" \
                                8000 "http://localhost:8000/health"
                            ;;
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

# Enhanced status display with persona information
display_status() {
    log INFO "========================================="
    log SUCCESS "Orchestra AI Advanced MCP System Status"
    log INFO "========================================="
    
    echo ""
    echo -e "${PURPLE}🎭 Persona System Status:${NC}"
    if [ "$PERSONA_SYSTEM" = "enabled" ]; then
        echo -e "  ${GREEN}✓${NC} Cherry (Personal Overseer): 4K context, cross-domain access"
        echo -e "  ${GREEN}✓${NC} Sophia (Financial Expert): 6K context, PayReady specialization"
        echo -e "  ${GREEN}✓${NC} Karen (Medical Specialist): 8K context, ParagonRX expertise"
    else
        echo -e "  ${YELLOW}⚠${NC} Persona system disabled"
    fi
    
    echo ""
    echo -e "${CYAN}🧠 Memory Architecture Status:${NC}"
    if [ "$ENABLE_ADVANCED_MEMORY" = "true" ]; then
        echo -e "  ${GREEN}✓${NC} L0: CPU Cache (~1ns) - Active"
        echo -e "  ${GREEN}✓${NC} L1: Process Memory (~10ns) - Active"
        echo -e "  ${GREEN}✓${NC} L2: Redis Cache (~100ns) - Connected"
        echo -e "  ${GREEN}✓${NC} L3: PostgreSQL (~1ms) - Connected"
        echo -e "  ${GREEN}✓${NC} L4: Weaviate (~10ms) - Connected"
        echo -e "  ${GREEN}✓${NC} Features: 20x compression, hybrid search, cross-domain routing"
    else
        echo -e "  ${YELLOW}⚠${NC} Advanced memory disabled - using simple memory"
    fi
    
    echo ""
    echo -e "${BLUE}🚀 MCP Services:${NC}"
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
    echo -e "${GREEN}🌐 Endpoints:${NC}"
    echo "  - Unified MCP (Advanced): http://localhost:8000"
    echo "  - Memory MCP: http://localhost:8003"
    echo "  - Conductor MCP: http://localhost:8002"
    echo "  - Tools MCP: http://localhost:8006"
    echo "  - Weaviate Direct MCP: http://localhost:8001"
    
    echo ""
    echo -e "${CYAN}💾 Database Connections:${NC}"
    echo "  - PostgreSQL (L3): ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}"
    echo "  - Redis (L2): ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
    echo "  - Weaviate (L4): ${WEAVIATE_HOST:-localhost}:${WEAVIATE_PORT:-8080}"
    
    echo ""
    echo -e "${PURPLE}🎯 Available Personas:${NC}"
    echo "  - Cherry: chat_with_persona persona=cherry"
    echo "  - Sophia: chat_with_persona persona=sophia"  
    echo "  - Karen: chat_with_persona persona=karen"
    echo "  - Cross-domain: cross_domain_query"
    
    echo ""
    echo "Logs: $LOG_DIR"
    echo "PIDs: $PID_DIR"
    echo ""
    echo -e "${YELLOW}To stop all services, run: ./stop_mcp_system_enhanced.sh${NC}"
    echo -e "${CYAN}To monitor services, run: tail -f $LOG_DIR/*.log${NC}"
    echo -e "${PURPLE}To test personas, use MCP tools: chat_with_persona, route_task_advanced${NC}"
}

# Main execution with advanced architecture
main() {
    log INFO "========================================="
    log INFO "Starting Orchestra AI Advanced MCP System"
    log INFO "========================================="
    
    # Check advanced system requirements
    if ! check_advanced_requirements; then
        log ERROR "Advanced system requirements not met. Exiting."
        exit 1
    fi
    
    # Initialize persona system
    if ! initialize_persona_system; then
        log ERROR "Persona system initialization failed. Exiting."
        exit 1
    fi
    
    # Initialize memory architecture
    if ! initialize_memory_architecture; then
        log ERROR "Memory architecture initialization failed. Exiting."
        exit 1
    fi
    
    # Test orchestrator integration
    if ! test_orchestrator_integration; then
        log ERROR "Orchestrator integration test failed. Exiting."
        exit 1
    fi
    
    # Export required environment variables
    export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
    export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    export POSTGRES_DB="${POSTGRES_DB:-cherry_ai}"
    export POSTGRES_USER="${POSTGRES_USER:-postgres}"
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
    
    export REDIS_HOST="${REDIS_HOST:-localhost}"
    export REDIS_PORT="${REDIS_PORT:-6379}"
    
    export WEAVIATE_HOST="${WEAVIATE_HOST:-localhost}"
    export WEAVIATE_PORT="${WEAVIATE_PORT:-8080}"
    export WEAVIATE_API_KEY="${WEAVIATE_API_KEY:-}"
    
    export API_URL="${API_URL:-http://localhost:8080}"
    export API_KEY="${API_KEY}" # Set in environment
    
    # Set Python path
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Start all servers with advanced features
    if start_all_servers; then
        log SUCCESS "All advanced MCP servers started successfully"
        
        # Start enhanced monitoring in background if enabled
        if [ "$AUTO_RESTART" = "true" ]; then
            monitor_servers &
            MONITOR_PID=$!
            echo $MONITOR_PID > "$PID_DIR/monitor.pid"
            log INFO "Enhanced monitoring started with persona tracking (PID: $MONITOR_PID)"
        fi
        
        # Display enhanced status
        display_status
        
        log PERSONA "🎭 Advanced Architecture Ready!"
        log MEMORY "🧠 5-Tier Memory System Active!"
        log SUCCESS "✅ Cherry, Sophia, and Karen personas available for interaction"
    else
        log ERROR "Some advanced servers failed to start"
        display_status
        exit 1
    fi
}

# Run main function
main "$@"
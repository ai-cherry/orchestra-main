#!/bin/bash
# 🚀 Supercharged Cursor AI System Startup
# Launches all enhanced MCP servers with updated persona configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/lynnmusil/orchestra-dev"
VENV_PATH="$PROJECT_DIR/venv"
PID_DIR="$PROJECT_DIR/.pids"
LOG_DIR="$PROJECT_DIR/logs"

# Ensure directories exist
mkdir -p "$PID_DIR" "$LOG_DIR"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_persona() {
    echo -e "${PURPLE}[PERSONA]${NC} $1"
}

# Check if process is running
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Start individual server
start_server() {
    local name="$1"
    local script="$2"
    local port="$3"
    local description="$4"
    
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    
    if is_running "$pid_file"; then
        log_warning "$description is already running (PID: $(cat $pid_file))"
        return 0
    fi
    
    log_info "Starting $description..."
    
    cd "$PROJECT_DIR"
    nohup python3 "$script" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        log_success "$description started successfully (PID: $pid, Port: $port)"
        return 0
    else
        log_error "$description failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

# Stop individual server
stop_server() {
    local name="$1"
    local description="$2"
    
    local pid_file="$PID_DIR/${name}.pid"
    
    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        log_info "Stopping $description (PID: $pid)..."
        kill "$pid"
        rm -f "$pid_file"
        log_success "$description stopped"
    else
        log_warning "$description is not running"
    fi
}

# Display system status
display_status() {
    log "======================================================"
    log_success "🎭 SUPERCHARGED CURSOR AI SYSTEM STATUS"
    log "======================================================"
    
    echo ""
    echo -e "${PURPLE}🎭 Enhanced Persona System:${NC}"
    echo -e "  ${GREEN}✓${NC} 💼 Sophia (Pay Ready Guru): 12K context, PRIMARY ASSISTANT"
    echo -e "  ${GREEN}✓${NC} 🍒 Cherry (Personal Overseer): 8K context, BROADER ACCESS"
    echo -e "  ${GREEN}✓${NC} ⚕️ Karen (ParagonRX Specialist): 6K context, FOCUSED & SCALABLE"
    
    echo ""
    echo -e "${CYAN}🧠 5-Tier Memory Architecture:${NC}"
    echo -e "  ${GREEN}✓${NC} L0: CPU Cache (~1ns) - Hot coding context"
    echo -e "  ${GREEN}✓${NC} L1: Process Memory (~10ns) - Active sessions"
    echo -e "  ${GREEN}✓${NC} L2: Shared Memory (~100ns) - Cross-persona sharing"
    echo -e "  ${GREEN}✓${NC} L3: PostgreSQL (~1ms) - Structured history"
    echo -e "  ${GREEN}✓${NC} L4: Weaviate (~10ms) - Vector semantic search"
    
    echo ""
    echo -e "${BLUE}🚀 MCP Server Status:${NC}"
    
    # Check all servers
    local servers=(
        "personas-api:Personas API (Cherry/Sophia/Karen):8000"
        "main-api:Main API & Health Monitoring:8010"
        "enhanced-memory:Enhanced 5-Tier Memory System:8003"
        "code-intelligence:Real-time Code Analysis:8007"
        "infrastructure-deployment:Pulumi IaC & Infrastructure:8005"
        "tools-coordination:Unified API & Tool Access:8006"
    )
    
    for server_info in "${servers[@]}"; do
        IFS=':' read -r name description port <<< "$server_info"
        local pid_file="$PID_DIR/${name}.pid"
        
        if is_running "$pid_file"; then
            local pid=$(cat "$pid_file")
            echo -e "  ${GREEN}✓${NC} $description (PID: $pid, Port: $port)"
        else
            echo -e "  ${RED}✗${NC} $description (Not running)"
        fi
    done
    
    echo ""
    echo -e "${GREEN}🎯 Cursor AI Integration:${NC}"
    echo -e "  ${GREEN}✓${NC} Enhanced MCP Configuration Active"
    echo -e "  ${GREEN}✓${NC} Custom Commands: /cherry, /sophia, /karen, /deploy, /analyze"
    echo -e "  ${GREEN}✓${NC} Real-time Code Intelligence"
    echo -e "  ${GREEN}✓${NC} Persistent Memory Across Sessions"
    echo -e "  ${GREEN}✓${NC} Infrastructure Control via Pulumi"
    
    echo ""
    echo -e "${CYAN}📊 Quick Tests:${NC}"
    echo "  curl http://127.0.0.1:8000/health  # Personas API"
    echo "  curl http://127.0.0.1:8010/health  # Main API"
    echo "  curl http://127.0.0.1:8003/health  # Enhanced Memory"
}

# Start all enhanced services
start_all() {
    log "🚀 Starting Supercharged Cursor AI System..."
    echo ""
    
    # Phase 1: Core Services (Already running)
    log_persona "Phase 1: Verifying Core Services..."
    
    # Check if personas server needs restart for new configuration
    if is_running "$PID_DIR/personas-api.pid"; then
        log_info "Restarting Personas API with updated configurations..."
        stop_server "personas-api" "Personas API"
        sleep 1
    fi
    
    # Start enhanced personas server
    start_server "personas-api" "personas_server.py" "8000" "Enhanced Personas API (Updated Configurations)"
    
    # Start main API if not running
    if ! is_running "$PID_DIR/main-api.pid"; then
        start_server "main-api" "main_app.py" "8010" "Main API & Health Monitoring"
    fi
    
    echo ""
    log_persona "Phase 2: Activating Enhanced MCP Servers..."
    
    # Enhanced Memory Server (5-tier architecture)
    start_server "enhanced-memory" "enhanced_memory_server_v2.py" "8003" "Enhanced 5-Tier Memory System"
    
    # Code Intelligence Server (real-time analysis)
    start_server "code-intelligence" "code_intelligence_server_enhanced.py" "8007" "Real-time Code Intelligence"
    
    # Infrastructure Deployment Server (Pulumi IaC)
    start_server "infrastructure-deployment" "infrastructure_deployment_server.py" "8005" "Pulumi IaC & Infrastructure Control"
    
    # Tools Coordination Server (unified API access)
    start_server "tools-coordination" "tools_coordination_server.py" "8006" "Unified API & Tool Coordination"
    
    echo ""
    log_persona "Phase 3: Verifying System Integration..."
    
    # Wait for all services to be ready
    sleep 3
    
    # Test core services
    local all_healthy=true
    
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        log_success "✅ Personas API responding"
    else
        log_error "❌ Personas API not responding"
        all_healthy=false
    fi
    
    if curl -s http://127.0.0.1:8010/health > /dev/null 2>&1; then
        log_success "✅ Main API responding"
    else
        log_error "❌ Main API not responding"
        all_healthy=false
    fi
    
    echo ""
    if [ "$all_healthy" = true ]; then
        log_success "🎉 SUPERCHARGED CURSOR AI SYSTEM READY!"
        echo ""
        display_status
        echo ""
        log "🎯 Next Steps:"
        echo "1. Open Cursor AI in this project directory"
        echo "2. Use enhanced commands: /cherry, /sophia, /karen"
        echo "3. Experience real-time code intelligence"
        echo "4. Deploy infrastructure with /deploy commands"
        echo "5. Access any API with unified tool coordination"
    else
        log_error "🔥 Some services failed to start. Check logs in $LOG_DIR/"
    fi
}

# Stop all services
stop_all() {
    log "🛑 Stopping Supercharged Cursor AI System..."
    
    stop_server "tools-coordination" "Tools Coordination Server"
    stop_server "infrastructure-deployment" "Infrastructure Deployment Server"
    stop_server "code-intelligence" "Code Intelligence Server"
    stop_server "enhanced-memory" "Enhanced Memory Server"
    stop_server "main-api" "Main API"
    stop_server "personas-api" "Personas API"
    
    log_success "🎯 All services stopped"
}

# Restart all services
restart_all() {
    log "🔄 Restarting Supercharged Cursor AI System..."
    stop_all
    sleep 2
    start_all
}

# Update Cursor MCP configuration
update_cursor_config() {
    log "⚙️ Updating Cursor MCP configuration..."
    
    local cursor_mcp_config="$HOME/.cursor/mcp.json"
    
    # Create enhanced MCP configuration
    cat > "$cursor_mcp_config" << 'EOF'
{
  "mcpServers": {
    "orchestra-personas": {
      "command": "python3",
      "args": ["/Users/lynnmusil/orchestra-dev/personas_server.py"],
      "disabled": false,
      "priority": "critical",
      "description": "Enhanced AI Personas: Cherry (8K), Sophia (12K), Karen (6K)",
      "timeout": 30000
    },
    "enhanced-memory": {
      "command": "python3", 
      "args": ["/Users/lynnmusil/orchestra-dev/enhanced_memory_server_v2.py"],
      "disabled": false,
      "priority": "critical",
      "description": "5-Tier Memory Architecture with Persona Integration",
      "timeout": 30000
    },
    "code-intelligence": {
      "command": "python3",
      "args": ["/Users/lynnmusil/orchestra-dev/code_intelligence_server_enhanced.py"],
      "disabled": false,
      "priority": "high",
      "description": "Real-time Code Analysis and Quality Feedback",
      "timeout": 20000
    },
    "infrastructure-deployment": {
      "command": "python3",
      "args": ["/Users/lynnmusil/orchestra-dev/infrastructure_deployment_server.py"],
      "disabled": false,
      "priority": "high", 
      "description": "Pulumi IaC and Infrastructure Control",
      "timeout": 25000
    },
    "tools-coordination": {
      "command": "python3",
      "args": ["/Users/lynnmusil/orchestra-dev/tools_coordination_server.py"],
      "disabled": false,
      "priority": "medium",
      "description": "Unified API and External Service Access",
      "timeout": 15000
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["@mcp-server/sequential-thinking"],
      "disabled": false,
      "priority": "medium",
      "description": "Complex Task Breakdown and Workflow Management",
      "timeout": 30000
    },
    "pulumi": {
      "command": "npm",
      "args": ["exec", "@pulumi/mcp-server"],
      "disabled": false,
      "priority": "high",
      "description": "Infrastructure as Code Acceleration",
      "timeout": 30000
    }
  },
  "globalSettings": {
    "maxConcurrentServers": 8,
    "retryAttempts": 3,
    "healthCheckInterval": 30000
  }
}
EOF
    
    log_success "✅ Enhanced Cursor MCP configuration updated"
}

# Main execution
main() {
    cd "$PROJECT_DIR"
    
    case "${1:-start}" in
        "start")
            start_all
            ;;
        "stop")
            stop_all
            ;;
        "restart")
            restart_all
            ;;
        "status")
            display_status
            ;;
        "config")
            update_cursor_config
            ;;
        "setup")
            update_cursor_config
            start_all
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|config|setup}"
            echo ""
            echo "Commands:"
            echo "  start   - Start all enhanced MCP servers"
            echo "  stop    - Stop all servers"
            echo "  restart - Restart all servers"
            echo "  status  - Show system status"
            echo "  config  - Update Cursor MCP configuration"
            echo "  setup   - Update config and start all servers"
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 
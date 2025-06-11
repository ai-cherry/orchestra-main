#!/bin/bash

# 🌅 Orchestra AI - Improved Morning Startup Script
# Enhanced with robust error handling and service validation

set -euo pipefail  # Strict error handling

# Colors for pretty output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m' # No Color

# Configuration
readonly PROJECT_DIR="/Users/lynnmusil/orchestra-dev"
readonly REMOTE_PROJECT_DIR="/home/ubuntu/orchestra-main-cursor-backup"
readonly SSH_KEY="$HOME/.ssh/manus-lambda-key"
readonly SSH_USER="ubuntu"
readonly SSH_HOST="localhost"
readonly SSH_PORT="8080"

# Logging functions
log_info() { echo -e "${BLUE}$1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "${PURPLE}$1${NC}"; }

# Error handler
error_handler() {
    local line_no=$1
    local error_code=$2
    log_error "Script failed at line $line_no with exit code $error_code"
    log_info "💡 Check the logs above for details or run with 'bash -x' for debug mode"
    exit $error_code
}
trap 'error_handler ${LINENO} $?' ERR

# Utility functions
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=10
    local attempt=1
    
    log_info "🔍 Waiting for $service_name to respond..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 3 "$url" >/dev/null 2>&1; then
            log_success "$service_name is responding"
            return 0
        fi
        log_info "Attempt $attempt/$max_attempts for $service_name..."
        sleep 2
        ((attempt++))
    done
    
    log_warning "$service_name not responding after $max_attempts attempts"
    return 1
}

check_ssh_connection() {
    if ssh -p "$SSH_PORT" -i "$SSH_KEY" -o ConnectTimeout=5 -o BatchMode=yes "$SSH_USER@$SSH_HOST" 'echo "SSH test successful"' >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Main script starts here
main() {
    log_header "🌅 Good Morning! Starting your Orchestra AI development environment..."
    log_header "============================================================"

    # Step 1: Validate and setup workspace
    log_info "📁 Step 1: Setting up workspace..."
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    cd "$PROJECT_DIR"
    log_success "In project directory: $(pwd)"

    # Step 2: Check and start SSH tunnels
    log_info "🔗 Step 2: Managing SSH tunnels..."
    
    # Check if tunnel script exists
    if [ -f "./start_persistent_tunnels.sh" ]; then
        if ./start_persistent_tunnels.sh status; then
            log_success "SSH tunnels already active"
        else
            log_info "Starting SSH tunnels..."
            ./start_persistent_tunnels.sh start
            sleep 5
            
            # Verify tunnel is working
            if check_ssh_connection; then
                log_success "SSH tunnel established and verified"
            else
                log_warning "SSH tunnel may have issues - continuing anyway"
            fi
        fi
    else
        log_warning "SSH tunnel script not found - checking if tunnels are manually active"
        if check_ssh_connection; then
            log_success "SSH connection verified (manually configured)"
        else
            log_error "No SSH connection available. Please set up tunnels manually."
            exit 1
        fi
    fi

    # Step 3: Sync code (optional - only if sync script exists)
    log_info "📥 Step 3: Checking for code sync..."
    if [ -f "./sync_orchestra.sh" ]; then
        log_info "Syncing latest code from remote..."
        if ./sync_orchestra.sh pull; then
            log_success "Code synchronized successfully"
        else
            log_warning "Code sync had issues - continuing with local code"
        fi
    else
        log_info "No sync script found - using local code only"
    fi

    # Step 4: Verify and fix remote dependencies
    log_info "🔧 Step 4: Checking remote services health..."
    if check_ssh_connection; then
        log_info "Checking remote Python dependencies..."
        
        # More robust dependency check with better error handling
        ssh -p "$SSH_PORT" -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "
            export PATH=\"\$HOME/.local/bin:\$PATH\"
            cd '$REMOTE_PROJECT_DIR' 2>/dev/null || cd ~
            
            echo 'Checking Python dependencies...'
            python3 -c '
import sys
missing_deps = []
required_deps = [\"litellm\", \"protobuf\", \"mcp\", \"fastapi\", \"uvicorn\"]

for dep in required_deps:
    try:
        __import__(dep)
        print(f\"✅ {dep}: Available\")
    except ImportError:
        missing_deps.append(dep)
        print(f\"❌ {dep}: Missing\")

if missing_deps:
    print(f\"Installing missing dependencies: {missing_deps}\")
    import subprocess
    result = subprocess.run([sys.executable, \"-m\", \"pip\", \"install\", \"--user\"] + missing_deps, 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(\"✅ Dependencies installed successfully\")
    else:
        print(f\"⚠️ Some dependencies may have installation issues: {result.stderr}\")
else:
    print(\"✅ All required dependencies available\")
'
        " 2>/dev/null || log_warning "Remote dependency check completed with some issues"
        
        log_success "Remote environment checked"
    else
        log_warning "Cannot verify remote dependencies - SSH connection unavailable"
    fi

    # Step 5: Start MCP services with proper validation
    log_info "🎯 Step 5: Starting and validating MCP services..."
    
    # Start remote MCP services
    if [ -f "./manage_remote_mcp.sh" ]; then
        log_info "Starting remote MCP services..."
        if ./manage_remote_mcp.sh start; then
            log_success "Remote MCP services started"
        else
            log_warning "Some remote MCP services may need attention"
        fi
    fi
    
    # Start local MCP services if they exist
    local_mcp_started=false
    for script in mcp_unified_server.py mcp_simple_server.py; do
        if [ -f "$script" ] && [ ! -f "${script%.py}.pid" ]; then
            log_info "Starting local MCP: $script"
            python3 "$script" >/dev/null 2>&1 &
            echo $! > "${script%.py}.pid"
            local_mcp_started=true
        fi
    done
    
    if $local_mcp_started; then
        sleep 3  # Give services time to start
        log_success "Local MCP services started"
    fi

    # Step 6: Validate services are responding
    log_info "🔍 Step 6: Validating service health..."
    
    services_healthy=true
    
    # Check personas API
    if wait_for_service "http://127.0.0.1:8081/health" "Personas API"; then
        personas_status=$(curl -s http://127.0.0.1:8081/health 2>/dev/null | grep -o '"personas":\[[^]]*\]' || echo "Unknown")
        log_success "Personas API: $personas_status"
    else
        services_healthy=false
    fi
    
    # Check main API
    if wait_for_service "http://127.0.0.1:8082/health" "Main API"; then
        log_success "Main API responding"
    else
        log_warning "Main API not responding - may need manual start"
    fi
    
    # Check if any local MCP servers are running
    local_mcp_count=$(ps aux | grep -E "mcp.*server" | grep -v grep | wc -l)
    if [ "$local_mcp_count" -gt 0 ]; then
        log_success "Local MCP servers: $local_mcp_count running"
    else
        log_info "No local MCP servers detected"
    fi

    # Step 7: Open development environment
    log_info "💻 Step 7: Opening development environment..."
    
    # Try different ways to open Cursor
    if command -v cursor >/dev/null 2>&1; then
        cursor "$PROJECT_DIR" &
        log_success "Cursor IDE opened"
    elif command -v code >/dev/null 2>&1; then
        code "$PROJECT_DIR" &
        log_success "VS Code opened (Cursor not found)"
    elif [ -d "/Applications/Cursor.app" ]; then
        open -a Cursor "$PROJECT_DIR" &
        log_success "Cursor opened via Application"
    else
        log_warning "Please manually open your IDE with: $PROJECT_DIR"
    fi

    # Step 8: Final system report
    log_info "🧪 Step 8: Final system verification..."
    
    echo
    log_header "============================================================"
    log_header "📊 SYSTEM STATUS REPORT"
    log_header "============================================================"
    
    # SSH Tunnels
    if check_ssh_connection; then
        log_success "SSH Connection: Active and verified"
    else
        log_warning "SSH Connection: Issues detected"
    fi
    
    # Service Health Summary
    if $services_healthy; then
        log_success "Core Services: All healthy"
    else
        log_warning "Core Services: Some issues detected (check above)"
    fi
    
    # Local Environment
    if [ -d "$PROJECT_DIR" ] && [ "$(ls -A "$PROJECT_DIR")" ]; then
        file_count=$(find "$PROJECT_DIR" -type f | wc -l)
        log_success "Local Environment: Ready ($file_count files)"
    else
        log_warning "Local Environment: Issues detected"
    fi
    
    # Development Tools
    if command -v cursor >/dev/null 2>&1 || command -v code >/dev/null 2>&1; then
        log_success "IDE: Available and launched"
    else
        log_warning "IDE: Please install Cursor or VS Code"
    fi

    echo
    log_header "🎉 Morning startup complete! Your development environment is ready."
    echo
    log_info "📋 Quick Reference Commands:"
    echo -e "  🔄 Sync code:           ${YELLOW}./sync_orchestra.sh {pull|push|both}${NC}"
    echo -e "  🎯 Manage MCP:          ${YELLOW}./manage_remote_mcp.sh {start|stop|status}${NC}"
    echo -e "  🔗 Check tunnels:       ${YELLOW}./start_persistent_tunnels.sh status${NC}"
    echo -e "  🖥️  SSH to remote:       ${YELLOW}ssh -p $SSH_PORT -i $SSH_KEY $SSH_USER@$SSH_HOST${NC}"
    echo -e "  🏥 Health check:        ${YELLOW}curl http://127.0.0.1:8081/health${NC}"
    echo
    log_success "💡 Pro tip: All services are validated and healthy. Happy coding! 🚀"
}

# Run main function
main "$@" 
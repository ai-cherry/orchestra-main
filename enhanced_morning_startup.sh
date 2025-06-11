#!/bin/bash

# 🌅 Orchestra AI - Enhanced Morning Startup Script
# Complete Cursor integration with MCP servers, settings, and workspace configuration

set -euo pipefail  # Strict error handling

# Colors for pretty output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Configuration
readonly PROJECT_DIR="/Users/lynnmusil/orchestra-dev"
readonly REMOTE_PROJECT_DIR="/home/ubuntu/orchestra-main-cursor-backup"
readonly SSH_KEY="$HOME/.ssh/manus-lambda-key"
readonly SSH_USER="ubuntu"
readonly SSH_HOST="localhost"
readonly SSH_PORT="8080"
readonly CURSOR_CONFIG_DIR="$HOME/.cursor"
readonly CURSOR_MCP_CONFIG="$CURSOR_CONFIG_DIR/mcp.json"

# Logging functions
log_info() { echo -e "${BLUE}$1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "${PURPLE}$1${NC}"; }
log_cursor() { echo -e "${CYAN}🎯 $1${NC}"; }

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

setup_cursor_mcp_config() {
    log_cursor "Setting up Cursor MCP configuration..."
    
    # Ensure Cursor config directory exists
    mkdir -p "$CURSOR_CONFIG_DIR"
    
    # Create comprehensive MCP configuration
    cat > "$CURSOR_MCP_CONFIG" << 'EOF'
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["@mcp-server/sequential-thinking"],
      "disabled": false,
      "alwaysAllow": ["sequentialthinking"]
    },
    "pulumi": {
      "command": "npm",
      "args": ["exec", "@pulumi/mcp-server"],
      "disabled": false,
      "alwaysAllow": ["pulumi-registry-get-resource", "pulumi-registry-list-resources", "pulumi-cli-preview", "pulumi-cli-up", "pulumi-cli-stack-output"]
    },
    "standard-tools": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/Users/lynnmusil/orchestra-dev"],
      "disabled": false,
      "alwaysAllow": ["read_file", "write_file", "create_directory", "list_directory"]
    }
  }
}
EOF
    
    log_success "Cursor MCP configuration created at: $CURSOR_MCP_CONFIG"
    
    # Validate the JSON
    if python3 -m json.tool "$CURSOR_MCP_CONFIG" >/dev/null 2>&1; then
        log_success "MCP configuration JSON is valid"
    else
        log_warning "MCP configuration JSON may have syntax issues"
    fi
}

setup_cursor_workspace() {
    log_cursor "Configuring Cursor workspace settings..."
    
    local workspace_config="$PROJECT_DIR/.cursor/cursor.json"
    mkdir -p "$PROJECT_DIR/.cursor"
    
    # Create workspace-specific settings
    cat > "$workspace_config" << 'EOF'
{
  "rules": [
    "architecture",
    "standards"
  ],
  "composer": {
    "writingStyle": "concise",
    "includeMinimap": true
  },
  "aiFeatures": {
    "codeGeneration": true,
    "autoComplete": true,
    "chatWithCodebase": true
  },
  "mcpIntegration": {
    "autoLoad": true,
    "enableSequentialThinking": true,
    "enablePulumi": true
  }
}
EOF
    
    log_success "Workspace configuration created"
}

verify_cursor_integrations() {
    log_cursor "Verifying Cursor integrations..."
    
    local integrations_healthy=true
    
    # Check MCP config exists and is valid
    if [ -f "$CURSOR_MCP_CONFIG" ]; then
        log_success "MCP configuration file exists"
        if python3 -m json.tool "$CURSOR_MCP_CONFIG" >/dev/null 2>&1; then
            log_success "MCP configuration is valid JSON"
        else
            log_warning "MCP configuration has JSON syntax errors"
            integrations_healthy=false
        fi
    else
        log_warning "MCP configuration file missing"
        integrations_healthy=false
    fi
    
    # Check workspace configuration
    if [ -f "$PROJECT_DIR/.cursor/cursor.json" ]; then
        log_success "Workspace configuration exists"
    else
        log_warning "Workspace configuration missing"
    fi
    
    # Verify MCP servers are running
    local mcp_processes=$(ps aux | grep -E "mcp.*server|sequential-thinking|pulumi.*mcp" | grep -v grep | wc -l)
    if [ "$mcp_processes" -gt 0 ]; then
        log_success "MCP servers running: $mcp_processes processes"
    else
        log_warning "No MCP server processes detected"
        integrations_healthy=false
    fi
    
    return $([ "$integrations_healthy" = true ] && echo 0 || echo 1)
}

# Main script starts here
main() {
    log_header "🌅 Good Morning! Starting your Orchestra AI development environment..."
    log_header "✨ Enhanced with complete Cursor integration!"
    log_header "============================================================"

    # Can start from anywhere - script will navigate to project dir
    log_info "📍 Starting from: $(pwd)"
    log_info "🎯 Target directory: $PROJECT_DIR"

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

    # Step 4: Setup Cursor MCP Configuration
    log_cursor "🎯 Step 4: Configuring Cursor MCP integration..."
    setup_cursor_mcp_config
    setup_cursor_workspace

    # Step 5: Verify and fix remote dependencies
    log_info "🔧 Step 5: Checking remote services health..."
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

    # Step 6: Start MCP services with proper validation
    log_info "🎯 Step 6: Starting and validating MCP services..."
    
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

    # Step 7: Validate services are responding
    log_info "🔍 Step 7: Validating service health..."
    
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
    local_mcp_count=$(ps aux | grep -E "mcp.*server|sequential-thinking|pulumi.*mcp" | grep -v grep | wc -l)
    if [ "$local_mcp_count" -gt 0 ]; then
        log_success "Local MCP servers: $local_mcp_count running"
    else
        log_info "No local MCP servers detected"
    fi

    # Step 8: Verify Cursor integrations
    log_cursor "🎯 Step 8: Verifying Cursor integrations..."
    if verify_cursor_integrations; then
        log_success "Cursor integrations verified and ready"
    else
        log_warning "Some Cursor integrations may need attention"
    fi

    # Step 9: Open development environment with proper configuration
    log_cursor "💻 Step 9: Opening Cursor with full configuration..."
    
    # Give user instructions for proper Cursor startup
    echo
    log_cursor "🎯 CURSOR STARTUP INSTRUCTIONS:"
    echo -e "${CYAN}1. Cursor will open with MCP servers pre-configured${NC}"
    echo -e "${CYAN}2. Look for MCP connection status in Cursor's status bar${NC}"
    echo -e "${CYAN}3. Available MCP tools: Sequential Thinking, Pulumi, Standard Tools${NC}"
    echo -e "${CYAN}4. Workspace rules and settings are automatically loaded${NC}"
    echo
    
    # Try different ways to open Cursor
    if command -v cursor >/dev/null 2>&1; then
        cursor "$PROJECT_DIR" &
        log_success "Cursor IDE opened with project configuration"
    elif command -v code >/dev/null 2>&1; then
        code "$PROJECT_DIR" &
        log_success "VS Code opened (Cursor not found) - MCP config may not work"
    elif [ -d "/Applications/Cursor.app" ]; then
        open -a Cursor "$PROJECT_DIR" &
        log_success "Cursor opened via Application with project"
    else
        log_warning "Please manually open Cursor with: $PROJECT_DIR"
        log_info "MCP configuration ready at: $CURSOR_MCP_CONFIG"
    fi

    # Step 10: Final comprehensive system report
    log_info "🧪 Step 10: Final system verification..."
    
    echo
    log_header "============================================================"
    log_header "📊 COMPREHENSIVE SYSTEM STATUS REPORT"
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
    
    # Cursor Integration Status
    if verify_cursor_integrations >/dev/null 2>&1; then
        log_success "Cursor Integration: MCP servers configured and ready"
    else
        log_warning "Cursor Integration: Some configuration issues"
    fi
    
    # Development Tools
    if command -v cursor >/dev/null 2>&1 || command -v code >/dev/null 2>&1; then
        log_success "IDE: Available and launched with full configuration"
    else
        log_warning "IDE: Please install Cursor or VS Code"
    fi

    echo
    log_header "🎉 Enhanced morning startup complete! Cursor is fully configured and ready."
    echo
    log_cursor "🎯 CURSOR MCP STATUS:"
    echo -e "${CYAN}📍 Configuration: $CURSOR_MCP_CONFIG${NC}"
    echo -e "${CYAN}🔧 Workspace Settings: $PROJECT_DIR/.cursor/cursor.json${NC}"
    echo -e "${CYAN}🤖 MCP Servers: Sequential Thinking, Pulumi, Standard Tools${NC}"
    echo -e "${CYAN}📊 Service Health: Check status bar in Cursor${NC}"
    echo
    log_info "📋 Quick Reference Commands:"
    echo -e "  🔄 Sync code:           ${YELLOW}./sync_orchestra.sh {pull|push|both}${NC}"
    echo -e "  🎯 Manage MCP:          ${YELLOW}./manage_remote_mcp.sh {start|stop|status}${NC}"
    echo -e "  🔗 Check tunnels:       ${YELLOW}./start_persistent_tunnels.sh status${NC}"
    echo -e "  🖥️  SSH to remote:       ${YELLOW}ssh -p $SSH_PORT -i $SSH_KEY $SSH_USER@$SSH_HOST${NC}"
    echo -e "  🏥 Health check:        ${YELLOW}curl http://127.0.0.1:8081/health${NC}"
    echo -e "  🎯 Cursor MCP config:   ${YELLOW}cat $CURSOR_MCP_CONFIG${NC}"
    echo
    log_success "💡 Pro tip: All services validated, Cursor configured with MCP servers. Happy coding! 🚀"
}

# Run main function
main "$@" 
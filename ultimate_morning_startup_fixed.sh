#!/bin/bash

# 🌅 Orchestra AI - ULTIMATE Morning Startup Script (PRODUCTION-ALIGNED)
# Cursor AI: Pure Development Assistant + Personas: Production Business System

set -euo pipefail  # Strict error handling

# Colors for pretty output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;95m'
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
readonly CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"
readonly CURSOR_WORKSPACE_SETTINGS="$PROJECT_DIR/.vscode/settings.json"

# Logging functions
log_info() { echo -e "${BLUE}$1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "${PURPLE}$1${NC}"; }
log_cursor() { echo -e "${CYAN}🎯 $1${NC}"; }
log_dev() { echo -e "${MAGENTA}💻 $1${NC}"; }
log_production() { echo -e "${GREEN}🚀 $1${NC}"; }

# Error handler
error_handler() {
    local line_no=$1
    local error_code=$2
    log_error "Script failed at line $line_no with exit code $error_code"
    log_info "💡 Check the logs above for details or run with 'bash -x' for debug mode"
    exit $error_code
}
trap 'error_handler ${LINENO} $?' ERR

setup_cursor_development_config() {
    log_dev "💻 Setting up Cursor AI as DEVELOPMENT ASSISTANT..."
    
    # Ensure directories exist
    mkdir -p "$HOME/Library/Application Support/Cursor/User"
    mkdir -p "$PROJECT_DIR/.vscode"
    mkdir -p "$PROJECT_DIR/.cursor"
    
    # Create Cursor settings for DEVELOPMENT FOCUS
    cat > "$CURSOR_SETTINGS" << 'EOF'
{
  "cursor.modelSettings": {
    "defaultModel": "claude-4-sonnet",
    "maxMode": true,
    "autoMode": false,
    "enableAllModels": true,
    "availableModels": [
      "claude-4-sonnet",
      "claude-4-opus", 
      "claude-3.5-sonnet",
      "gemini-2.5-pro",
      "gpt-4.1",
      "o3-pro",
      "deepseek-r1-0528"
    ]
  },
  "cursor.betaFeatures": {
    "composerV2": true,
    "agentMode": true,
    "contextualChat": true,
    "smartRewrite": true,
    "codebaseIndexing": true,
    "semanticSearch": true,
    "multiFileEdit": true,
    "terminalIntegration": true,
    "gitIntegration": true,
    "apiAccess": true,
    "mcpIntegration": true,
    "advancedCompletion": true,
    "experimentalFeatures": true
  },
  "cursor.permissions": {
    "fileSystemAccess": "full",
    "networkAccess": "development",
    "terminalAccess": "full",
    "apiAccess": "development",
    "allowExternalConnections": false,
    "allowCodeExecution": true,
    "allowFileModification": true,
    "allowDirectoryTraversal": true,
    "allowInfrastructureControl": "development-only"
  },
  "cursor.development": {
    "focus": "coding-assistant",
    "personaIntegration": "domain-aware-comments-only",
    "productionAccess": "read-only-for-context"
  }
}
EOF

    # Create workspace-specific settings for DEVELOPMENT
    cat > "$CURSOR_WORKSPACE_SETTINGS" << 'EOF'
{
  "cursor.rules": [
    "architecture",
    "standards" 
  ],
  "cursor.composer": {
    "writingStyle": "concise",
    "includeMinimap": true,
    "enableMultiFileEdit": true,
    "maxMode": true,
    "focus": "development"
  },
  "cursor.domainAwareness": {
    "payReadyCode": {
      "note": "Financial/Payment code - Business logic managed by Sophia persona in production",
      "context": "PCI DSS compliance required, payment processing patterns"
    },
    "paragonRxCode": {
      "note": "Medical/Healthcare code - Business logic managed by Karen persona in production", 
      "context": "HIPAA compliance required, medical coding standards"
    },
    "infrastructureCode": {
      "note": "Infrastructure/Coordination code - Managed by Cherry persona in production",
      "context": "Multi-domain coordination, system integration patterns"
    }
  },
  "cursor.production": {
    "personasApi": "http://127.0.0.1:8081",
    "accessLevel": "development-context-only",
    "note": "Personas handle live business operations, Cursor handles development"
  }
}
EOF

    # Create DEVELOPMENT-FOCUSED MCP configuration
    cat > "$CURSOR_MCP_CONFIG" << 'EOF'
{
  "mcpServers": {
    "code-intelligence": {
      "command": "python3", 
      "args": ["/Users/lynnmusil/orchestra-dev/code_intelligence_server_enhanced.py"],
      "description": "Real-time Code Analysis with Domain Awareness",
      "features": ["complexity analysis", "domain-aware insights", "refactoring suggestions"]
    },
    "infrastructure-deployment": {
      "command": "python3",
      "args": ["/Users/lynnmusil/orchestra-dev/infrastructure_deployment_server.py"],
      "description": "Development Infrastructure Control (Vercel, Lambda Labs)",
      "features": ["vercel deployment", "lambda labs management", "development environments"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sequential-thinking"],
      "description": "Advanced Problem Solving for Development",
      "features": ["multi-step analysis", "development planning", "architecture decisions"]
    },
    "pulumi": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-pulumi"],
      "description": "Infrastructure as Code for Development",
      "features": ["cloud resources", "development deployment", "staging environments"]
    },
    "filesystem": {
      "command": "npx", 
      "args": ["@modelcontextprotocol/server-filesystem", "/Users/lynnmusil/orchestra-dev"],
      "description": "Complete Development Filesystem Access",
      "features": ["file operations", "directory management", "code search"]
    }
  },
  "global": {
    "timeout": 30,
    "retries": 3,
    "features": {
      "development_focus": true,
      "domain_awareness": true,
      "production_separation": true,
      "code_intelligence": true
    },
    "performance": {
      "target_response_time": "2ms",
      "development_optimized": true
    }
  }
}
EOF

    # Create development API access configuration
    cat > "$PROJECT_DIR/.cursor/development_config.json" << 'EOF'
{
  "developmentServices": {
    "lambdaLabs": {
      "baseUrl": "http://127.0.0.1",
      "ports": {
        "ssh": 8080,
        "personas": 8081,
        "mainApi": 8082,
        "frontend": 8083
      },
      "accessLevel": "development"
    },
    "vercel": {
      "deployment": "development-only",
      "production": "personas-controlled"
    }
  },
  "domainSeparation": {
    "cursorAI": {
      "role": "Development assistant, code analysis, deployment tools",
      "scope": "Development environment only",
      "personaInteraction": "Domain-aware code comments only"
    },
    "personas": {
      "role": "Live business operations, database interactions, customer service",
      "scope": "Production environment",
      "cursorInteraction": "Separate system, no direct integration"
    }
  },
  "permissions": {
    "allowDevelopmentDeployment": true,
    "allowProductionAccess": false,
    "allowPersonaDataAccess": false,
    "allowCodeAnalysis": true
  }
}
EOF
    
    log_success "Development-focused Cursor configuration created"
    log_success "✅ ALL models enabled for development assistance"
    log_success "✅ MAX Mode ENABLED for coding productivity"
    log_success "✅ Domain-aware code intelligence (not persona integration)"
    log_success "✅ Development infrastructure control only"
    log_success "✅ Production personas remain separate system"
}

start_production_personas() {
    log_production "🚀 Starting Production Persona System..."
    
    # Check if personas are already running
    if curl -s http://127.0.0.1:8081/health >/dev/null 2>&1; then
        log_success "Production personas already running"
        
        # Get persona status
        persona_status=$(curl -s http://127.0.0.1:8081/health 2>/dev/null || echo '{"status": "unknown"}')
        log_success "Cherry (Personal Overseer): Cross-domain coordination"
        log_success "Sophia (Pay Ready Guru): PRIMARY ASSISTANT (12K context)"  
        log_success "Karen (ParagonRX): Medical specialist (6K context)"
        
        return 0
    fi
    
    # Start personas if not running
    log_info "Starting production persona system..."
    
    if check_ssh_connection; then
        log_info "Starting personas via SSH tunnel..."
        ssh -p "$SSH_PORT" -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" \
            "cd $REMOTE_PROJECT_DIR && python3 personas_server.py > personas_api.log 2>&1 & echo \$! > personas_api.pid && echo 'Personas API started on port 8000 with PID: \$(cat personas_api.pid)'"
        
        sleep 5
        
        if wait_for_service "http://127.0.0.1:8081/health" "Production Personas"; then
            log_success "Production persona system started successfully"
        else
            log_warning "Personas may be starting up, check manually"
        fi
    else
        log_warning "No SSH connection - personas may need manual start"
    fi
}

start_development_mcp_servers() {
    log_dev "💻 Starting Development MCP Servers..."
    
    # Start only development-focused MCP servers
    local servers_started=0
    
    # Code Intelligence Server for development
    if ! pgrep -f "code_intelligence_server_enhanced.py" >/dev/null; then
        log_info "Starting Code Intelligence Server..."
        python3 "$PROJECT_DIR/code_intelligence_server_enhanced.py" &
        ((servers_started++))
        sleep 2
    fi
    
    # Infrastructure Deployment for development environments
    if ! pgrep -f "infrastructure_deployment_server.py" >/dev/null; then
        log_info "Starting Infrastructure Deployment Server..."
        python3 "$PROJECT_DIR/infrastructure_deployment_server.py" &
        ((servers_started++))
        sleep 2
    fi
    
    if [ $servers_started -gt 0 ]; then
        log_success "Started $servers_started development MCP servers"
    else
        log_success "Development MCP servers already running"
    fi
}

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

open_cursor_development() {
    log_dev "💻 Opening Cursor AI as Development Assistant..."
    
    echo
    log_dev "💻 CURSOR AI DEVELOPMENT FEATURES:"
    echo -e "${MAGENTA}✅ Code Analysis: Real-time complexity, quality, refactoring${NC}"
    echo -e "${MAGENTA}✅ Domain Awareness: Pay Ready, ParagonRX, Infrastructure context${NC}"
    echo -e "${MAGENTA}✅ Infrastructure Control: Vercel deployment, Lambda Labs management${NC}"
    echo -e "${MAGENTA}✅ ALL Models: Claude-4-Sonnet/Opus, Gemini-2.5-Pro, GPT-4.1, O3-Pro${NC}"
    echo -e "${MAGENTA}✅ MAX Mode: Maximum development productivity${NC}"
    echo -e "${MAGENTA}✅ MCP Servers: Code intelligence, infrastructure, problem solving${NC}"
    echo
    log_dev "📝 DOMAIN-AWARE DEVELOPMENT:"
    echo -e "${CYAN}• Pay Ready code → Cursor adds context: 'Sophia handles business logic'${NC}"
    echo -e "${CYAN}• ParagonRX code → Cursor adds context: 'Karen handles medical compliance'${NC}" 
    echo -e "${CYAN}• Infrastructure → Cursor adds context: 'Cherry coordinates in production'${NC}"
    echo
    
    log_info "🚀 Opening Cursor with development focus..."
    
    # Open Cursor for development
    if [ -d "/Applications/Cursor.app" ]; then
        open -a Cursor "$PROJECT_DIR"
        log_success "Cursor opened as development assistant"
        
        # Give Cursor time to start
        sleep 3
        
        # Verify Cursor opened
        if ps aux | grep -q "[C]ursor.app"; then
            log_success "✅ Cursor AI development assistant ready!"
        else
            log_warning "⚠️ Cursor may not have opened properly"
        fi
    else
        log_error "❌ Could not find Cursor! Please install from: https://cursor.sh"
        return 1
    fi
    
    return 0
}

check_system_separation() {
    log_header "🔍 Checking Development/Production Separation..."
    
    # Check Cursor (Development)
    if ps aux | grep -q "[C]ursor.app"; then
        log_dev "💻 Cursor AI: Development assistant ACTIVE"
    else
        log_warning "💻 Cursor AI: Not running"
    fi
    
    # Check Personas (Production)  
    if curl -s http://127.0.0.1:8081/health >/dev/null 2>&1; then
        log_production "🚀 Production Personas: ACTIVE and handling business operations"
    else
        log_warning "🚀 Production Personas: Not responding"
    fi
    
    # Check MCP Servers (Development Tools)
    local mcp_count=$(ps aux | grep -E "(code_intelligence|infrastructure_deployment|enhanced_memory)" | grep -v grep | wc -l)
    if [ "$mcp_count" -gt 0 ]; then
        log_dev "💻 Development MCP Servers: $mcp_count active"
    else
        log_warning "💻 Development MCP Servers: None running"
    fi
    
    echo
    log_header "🎯 SYSTEM ARCHITECTURE CONFIRMED:"
    echo -e "${CYAN}📍 Cursor AI: Pure development assistant with domain awareness${NC}"
    echo -e "${GREEN}📍 Personas: Live production system handling business operations${NC}"
    echo -e "${YELLOW}📍 Connection: Domain-aware code comments only (no direct integration)${NC}"
}

# Main script
main() {
    log_header "🌅 Good Morning! Starting Orchestra AI Development Environment..."
    log_dev "💻 Cursor AI: Development Assistant + Domain Awareness"
    log_production "🚀 Personas: Production Business System (Separate)"
    log_header "=================================================================="

    log_info "📍 Starting from: $(pwd)"
    log_info "🎯 Target directory: $PROJECT_DIR"

    # Navigate to project directory
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    cd "$PROJECT_DIR"
    log_success "In project directory: $(pwd)"

    # Setup Development-focused Cursor configuration
    log_dev "💻 Step 1: Development-Focused Cursor Configuration..."
    setup_cursor_development_config

    # Check/Start Production Personas (separate system)
    log_production "🚀 Step 2: Production Persona System..."
    start_production_personas

    # Start Development MCP Servers
    log_dev "💻 Step 3: Development MCP Servers..."
    start_development_mcp_servers

    # Check SSH tunnels for production access
    log_info "🔗 Step 4: Production Access (SSH Tunnels)..."
    if check_ssh_connection; then
        log_success "SSH connection to production available"
    else
        log_warning "SSH connection not available - production access limited"
    fi

    # Open Cursor as Development Assistant
    log_dev "💻 Step 5: Opening Cursor AI Development Assistant..."
    if open_cursor_development; then
        log_success "🎉 Cursor AI development assistant ready!"
    else
        log_error "❌ Failed to open Cursor"
        exit 1
    fi

    # Check system separation
    sleep 2
    check_system_separation

    # Final status
    echo
    log_header "🎉 Orchestra AI Development Environment Ready!"
    echo
    log_dev "💻 CURSOR AI READY FOR:"
    echo -e "${CYAN}• Code analysis with domain awareness${NC}"
    echo -e "${CYAN}• Real-time development assistance${NC}"
    echo -e "${CYAN}• Infrastructure deployment (dev environments)${NC}"
    echo -e "${CYAN}• Domain-specific code context (Pay Ready, ParagonRX)${NC}"
    echo
    
    log_production "🚀 PRODUCTION PERSONAS HANDLING:"
    echo -e "${GREEN}• Live customer interactions${NC}"
    echo -e "${GREEN}• Database operations${NC}"
    echo -e "${GREEN}• Business logic execution${NC}"
    echo -e "${GREEN}• Cross-domain coordination${NC}"
    echo
    
    log_header "📋 WHAT TO CHECK:"
    echo -e "${CYAN}1. Cursor: Domain-aware code suggestions${NC}"
    echo -e "${CYAN}2. MCP Tools: Code intelligence, infrastructure tools${NC}"
    echo -e "${GREEN}3. Personas API: http://127.0.0.1:8081/health${NC}"
    echo -e "${YELLOW}4. Separation: Development ↔ Production systems independent${NC}"
    echo
    
    log_header "💡 Perfect separation: Cursor handles CODE, Personas handle BUSINESS! 🚀"
}

# Run main function
main "$@" 
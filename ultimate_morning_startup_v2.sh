#!/bin/bash

# 🌅 Orchestra AI - ULTIMATE Morning Startup Script V2
# FIXED: Proper Cursor project opening even when Cursor is already running

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
log_max() { echo -e "${MAGENTA}🚀 $1${NC}"; }

setup_cursor_ultimate_config() {
    log_max "🚀 Setting up Cursor with ALL models and ULTIMATE features..."
    
    # Ensure directories exist
    mkdir -p "$HOME/Library/Application Support/Cursor/User"
    mkdir -p "$PROJECT_DIR/.vscode"
    mkdir -p "$PROJECT_DIR/.cursor"
    
    # Create ULTIMATE Cursor settings
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
    "networkAccess": "full",
    "terminalAccess": "full",
    "apiAccess": "full",
    "allowExternalConnections": true,
    "allowCodeExecution": true,
    "allowFileModification": true,
    "allowDirectoryTraversal": true,
    "allowInfrastructureControl": true
  },
  "cursor.api": {
    "enableApiAccess": true,
    "allowExternalApis": true,
    "trustedDomains": [
      "localhost",
      "127.0.0.1",
      "192.9.142.8",
      "lambdalabs.com",
      "*.lambdalabs.com",
      "notion.so",
      "*.notion.so"
    ]
  }
}
EOF

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
      "alwaysAllow": [
        "pulumi-registry-get-resource",
        "pulumi-registry-list-resources", 
        "pulumi-cli-preview",
        "pulumi-cli-up",
        "pulumi-cli-stack-output"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/Users/lynnmusil/orchestra-dev"],
      "disabled": false,
      "alwaysAllow": [
        "read_file",
        "write_file", 
        "create_directory",
        "list_directory"
      ]
    },
    "brave-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search"],
      "disabled": false,
      "alwaysAllow": ["brave_web_search"]
    }
  }
}
EOF

    # Create workspace-specific settings
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
    "maxMode": true
  },
  "cursor.orchestra": {
    "personas": {
      "cherry": "http://127.0.0.1:8081/cherry",
      "sophia": "http://127.0.0.1:8081/sophia", 
      "karen": "http://127.0.0.1:8081/karen"
    },
    "infrastructure": {
      "lambdaLabs": "127.0.0.1:8080-8083",
      "mainApi": "127.0.0.1:8082",
      "personasApi": "127.0.0.1:8081"
    }
  }
}
EOF

    # Create API access configuration
    cat > "$PROJECT_DIR/.cursor/api_config.json" << 'EOF'
{
  "orchestraServices": {
    "lambdaLabs": {
      "baseUrl": "http://127.0.0.1",
      "ports": {
        "ssh": 8080,
        "personas": 8081,
        "mainApi": 8082,
        "frontend": 8083
      }
    },
    "notion": {
      "workspaceId": "20bdba04940280ca9ba7f9bce721f547"
    }
  },
  "permissions": {
    "allowInfrastructureChanges": true,
    "allowDatabaseOperations": true,
    "allowFileSystemAccess": true,
    "allowNetworkAccess": true
  }
}
EOF
    
    log_success "ULTIMATE Cursor configuration created"
    log_success "✅ ALL models enabled (Claude-4-Sonnet, Claude-4-Opus, Gemini-2.5-Pro, GPT-4.1, O3-Pro, DeepSeek)"
    log_success "✅ MAX Mode ENABLED"
    log_success "✅ ALL Beta features ENABLED"
    log_success "✅ Full API access configured"
    log_success "✅ Infrastructure control enabled"
}

open_cursor_properly() {
    log_max "💻 Opening Cursor with ULTIMATE configuration..."
    
    echo
    log_max "🚀 CURSOR ULTIMATE FEATURES ENABLED:"
    echo -e "${MAGENTA}✅ ALL Premium Models: Claude-4-Sonnet/Opus, Gemini-2.5-Pro, GPT-4.1, O3-Pro, DeepSeek${NC}"
    echo -e "${MAGENTA}✅ MAX Mode: ENABLED for maximum capabilities${NC}"
    echo -e "${MAGENTA}✅ Beta Features: ALL activated${NC}"
    echo -e "${MAGENTA}✅ API Access: Full infrastructure control${NC}"
    echo -e "${MAGENTA}✅ MCP Servers: Sequential Thinking, Pulumi, Filesystem, Search${NC}"
    echo -e "${MAGENTA}✅ Workspace Rules: Architecture & Standards loaded${NC}"
    echo
    
    log_info "🚀 Opening Cursor with project directory..."
    
    # Check if Cursor is already running
    local cursor_running=false
    if ps aux | grep -q "[C]ursor.app"; then
        cursor_running=true
        log_info "📱 Cursor is already running"
    fi
    
    # IMPROVED: Multiple methods to ensure Cursor opens with the project
    if [ -d "/Applications/Cursor.app" ]; then
        log_info "🎯 Method 1: Opening with specific project folder..."
        
        # Method 1: Use open with specific folder (most reliable)
        open -a Cursor "$PROJECT_DIR"
        sleep 2
        
        # Method 2: If Cursor was already running, also use cursor:// URL scheme
        if $cursor_running; then
            log_info "🎯 Method 2: Using URL scheme to ensure project loads..."
            open "cursor://file/$PROJECT_DIR"
            sleep 1
        fi
        
        # Method 3: Use osascript to ensure window focus
        log_info "🎯 Method 3: Ensuring Cursor window is focused..."
        osascript -e 'tell application "Cursor" to activate' 2>/dev/null || true
        
        log_success "✅ Cursor opening commands sent"
        
        # Give Cursor time to fully load
        log_info "⏳ Waiting for Cursor to fully load..."
        sleep 3
        
        # Verify Cursor is running and responding
        if ps aux | grep -q "[C]ursor.app"; then
            local cursor_processes=$(ps aux | grep "[C]ursor" | wc -l)
            log_success "✅ Cursor is running ($cursor_processes processes)"
            
            # Additional verification: Check if Cursor is the frontmost app
            local frontmost_app=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null || echo "unknown")
            if [[ "$frontmost_app" == "Cursor" ]]; then
                log_success "🎯 Cursor is the active application"
            else
                log_warning "⚠️ Cursor may not be the active window (frontmost: $frontmost_app)"
                log_info "💡 Click on Cursor window or use Cmd+Tab to switch to Cursor"
            fi
            
            return 0
        else
            log_error "❌ Cursor failed to start"
            return 1
        fi
        
    elif command -v cursor >/dev/null 2>&1; then
        cursor "$PROJECT_DIR" &
        log_success "Cursor opened via command line"
        return 0
    else
        log_error "❌ Could not find Cursor! Please manually open Cursor with: $PROJECT_DIR"
        log_info "💡 Install Cursor from: https://cursor.sh"
        return 1
    fi
}

# Main script
main() {
    log_header "🌅 Good Morning! Starting your ULTIMATE Orchestra AI environment..."
    log_max "🚀 MAX Mode + All Models + Full API Access + Beta Features!"
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

    # Setup ULTIMATE Cursor configuration
    log_max "🚀 Step 1: ULTIMATE Cursor Configuration..."
    setup_cursor_ultimate_config

    # Open Cursor properly
    log_max "💻 Step 2: Opening Cursor with ULTIMATE configuration..."
    if open_cursor_properly; then
        log_success "🎉 Cursor setup complete!"
    else
        log_error "❌ Failed to open Cursor properly"
        log_info "🔧 Manual workaround: open -a Cursor '$PROJECT_DIR'"
        exit 1
    fi

    # Final status and instructions
    echo
    log_header "🎉 ULTIMATE startup complete! Cursor is MAXED OUT and ready!"
    echo
    log_max "🎯 WHAT TO CHECK IN CURSOR NOW:"
    echo -e "${CYAN}1. 📱 Look for Cursor window (should be focused)${NC}"
    echo -e "${CYAN}2. 📁 Check that orchestra-dev project is loaded${NC}"
    echo -e "${CYAN}3. 🎯 Model dropdown: Look for ALL premium models${NC}"
    echo -e "${CYAN}4. ⚡ Settings: MAX Mode toggle should be ON (purple)${NC}"
    echo -e "${CYAN}5. 🤖 Status bar: Check for MCP server connections${NC}"
    echo -e "${CYAN}6. 🧪 Try Sequential Thinking tool in chat${NC}"
    echo
    
    log_max "🚀 CONFIG FILES CREATED:"
    echo -e "${MAGENTA}📍 Global Config: $CURSOR_SETTINGS${NC}"
    echo -e "${MAGENTA}🎯 Workspace Config: $CURSOR_WORKSPACE_SETTINGS${NC}"
    echo -e "${MAGENTA}🤖 MCP Config: $CURSOR_MCP_CONFIG${NC}"
    echo -e "${MAGENTA}🏗️ API Config: $PROJECT_DIR/.cursor/api_config.json${NC}"
    echo
    
    log_max "💡 You now have the most powerful AI development environment possible! 🚀"
    log_info "🎯 If Cursor window isn't visible, use Cmd+Tab or click Cursor in Dock"
}

# Run main function
main "$@" 
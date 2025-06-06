#!/bin/bash
# Setup script for Claude Code with MCP integration in Cursor IDE

set -e

echo "🚀 Setting up Claude Code with MCP for AI cherry_ai..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging configuration
LOG_DIR="$HOME/.claude-code/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    local level=$1
    shift
    local msg="$@"
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $msg" | tee -a "$LOG_FILE"
}

# Function to log with color
log_info() {
    echo -e "${BLUE}ℹ${NC} $@"
    log "INFO" "$@"
}

log_success() {
    echo -e "${GREEN}✓${NC} $@"
    log "SUCCESS" "$@"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $@"
    log "WARNING" "$@"
}

log_error() {
    echo -e "${RED}✗${NC} $@"
    log "ERROR" "$@"
}

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/..' && pwd)"
log_info "Project root: $PROJECT_ROOT"

# Check if claude-code is installed
if ! command -v claude &> /dev/null; then
    log_warning "Claude Code CLI not found. Installing..."
    if command -v npm &> /dev/null; then
        sudo npm install -g @anthropic-ai/claude-code || error_exit "Failed to install Claude Code CLI"
        log_success "Claude Code CLI installed successfully"
    else
        error_exit "npm is not installed. Please install Node.js and npm first."
    fi
else
    log_success "Claude Code CLI is already installed"
fi

# Create claude config directory if it doesn't exist
CLAUDE_CONFIG_DIR="$HOME/.config/claude"
mkdir -p "$CLAUDE_CONFIG_DIR" || error_exit "Failed to create config directory"

# Create MCP server registry
log_info "Creating MCP server registry..."
MCP_REGISTRY_FILE="$PROJECT_ROOT/mcp_server/server_registry.json"

cat > "$MCP_REGISTRY_FILE" << 'EOF'
{
  "version": "1.0.0",
  "servers": {
    "Lambda-cloud-run": {
      "path": "servers/Lambda_cloud_run_server.py",
      "command": "python",
      "description": "Deploy and manage Cloud Run services",
      "required_env": ["LAMBDA_PROJECT_ID", "LAMBDA_REGION"],
      "optional_env": ["GOOGLE_APPLICATION_CREDENTIALS"]
    },
    "Lambda-secrets": {
      "path": "servers/Lambda_secret_manager_server.py",
      "command": "python",
      "description": "Manage Google Secret Manager",
      "required_env": ["LAMBDA_PROJECT_ID"],
      "optional_env": ["GOOGLE_APPLICATION_CREDENTIALS"]
    },
    "dragonfly": {
      "path": "servers/dragonfly_server.py",
      "command": "python",
      "description": "Interact with DragonflyDB cache",
      "required_env": [],
      "optional_env": ["DRAGONFLY_HOST", "DRAGONFLY_PORT", "DRAGONFLY_PASSWORD"]
    },
    "firestore": {
      "path": "servers/firestore_server.py",
      "command": "python",
      "description": "Manage Firestore documents",
      "required_env": ["LAMBDA_PROJECT_ID"],
      "optional_env": ["GOOGLE_APPLICATION_CREDENTIALS"]
    }
  }
}
EOF

log_success "MCP server registry created"

# Create MCP configuration for Claude Code
log_info "Configuring MCP servers for Claude Code..."

# Build MCP configuration dynamically based on available servers
log_info "Building MCP configuration from available servers..."

# Check which servers exist and create configuration
MCP_CONFIG="{
  \"mcpServers\": {"

SERVER_COUNT=0
for server_file in "$PROJECT_ROOT/mcp_server/servers/"*.py; do
    if [ -f "$server_file" ]; then
        server_name=$(basename "$server_file" .py | sed 's/_server$//' | sed 's/_/-/g')
        log_info "Found server: $server_name ($server_file)"

        if [ $SERVER_COUNT -gt 0 ]; then
            MCP_CONFIG+=","
        fi

        MCP_CONFIG+="
    \"$server_name\": {
      \"command\": \"python\",
      \"args\": [
        \"$server_file\"
      ],
      \"env\": {"

        # Add environment variables based on server type
        case "$server_name" in
            "Lambda-cloud-run")
                MCP_CONFIG+="
        \"LAMBDA_PROJECT_ID\": \"\${LAMBDA_PROJECT_ID}\",
        \"LAMBDA_REGION\": \"\${LAMBDA_REGION}\""
                ;;
            "Lambda-secret-manager")
                MCP_CONFIG+="
        \"LAMBDA_PROJECT_ID\": \"\${LAMBDA_PROJECT_ID}\""
                ;;
            "dragonfly")
                MCP_CONFIG+="
        \"DRAGONFLY_HOST\": \"\${DRAGONFLY_HOST:-localhost}\",
        \"DRAGONFLY_PORT\": \"\${DRAGONFLY_PORT:-6379}\",
        \"DRAGONFLY_PASSWORD\": \"\${DRAGONFLY_PASSWORD}\""
                ;;
            "firestore")
                MCP_CONFIG+="
        \"LAMBDA_PROJECT_ID\": \"\${LAMBDA_PROJECT_ID}\""
                ;;
        esac

        MCP_CONFIG+="
      }
    }"

        SERVER_COUNT=$((SERVER_COUNT + 1))
    fi
done

MCP_CONFIG+="
  },
  \"defaultModel\": \"claude-4\",
  \"features\": {
    \"mcp\": true,
    \"codeCompletion\": true,
    \"diffViewer\": true,
    \"contextSharing\": true
  }
}"

echo "$MCP_CONFIG" > "$CLAUDE_CONFIG_DIR/config.json"

# Expand environment variables in config
if command -v envsubst &> /dev/null; then
    envsubst < "$CLAUDE_CONFIG_DIR/config.json" > "$CLAUDE_CONFIG_DIR/config.json.tmp" || error_exit "Failed to expand environment variables"
    mv "$CLAUDE_CONFIG_DIR/config.json.tmp" "$CLAUDE_CONFIG_DIR/config.json"
    log_success "MCP configuration created with environment variables expanded"
else
    log_warning "envsubst not found, configuration will use literal environment variable references"
    log_success "MCP configuration created"
fi

log_info "Found $SERVER_COUNT MCP servers"

# Create a project-specific .mcp.json for team sharing
echo -e "${YELLOW}Creating project MCP configuration...${NC}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cat > "$PROJECT_ROOT/.mcp.json" << 'EOF'
{
  "name": "AI cherry_ai MCP Configuration",
  "description": "MCP servers for AI cherry_ai development",
  "servers": {
    "Lambda-cloud-run": {
      "description": "Deploy and manage Cloud Run services",
      "capabilities": ["deploy", "status", "list"]
    },
    "Lambda-secrets": {
      "description": "Manage Google Secret Manager",
      "capabilities": ["get", "create", "update", "list"]
    },
    "dragonfly": {
      "description": "Interact with DragonflyDB cache",
      "capabilities": ["get", "set", "delete", "list"]
    },
    "firestore": {
      "description": "Manage Firestore documents",
      "capabilities": ["create", "read", "update", "query"]
    }
  }
}
EOF

echo -e "${GREEN}✓ Project MCP configuration created${NC}"

# Validate configuration
log_info "Validating MCP configuration..."
if [ -f "$CLAUDE_CONFIG_DIR/config.json" ]; then
    if python -m json.tool "$CLAUDE_CONFIG_DIR/config.json" > /dev/null 2>&1; then
        log_success "MCP configuration is valid JSON"
    else
        error_exit "MCP configuration is not valid JSON"
    fi
else
    error_exit "MCP configuration file not created"
fi

# Create a launcher script for Cursor
log_info "Creating Cursor launcher with Claude Code..."

cat > "$PROJECT_ROOT/launch_cursor_with_claude.sh" << 'EOF'
#!/bin/bash
# Launch Cursor with Claude Code integration

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging configuration
LOG_DIR="$HOME/.claude-code/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cursor_launch_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    local level=$1
    shift
    local msg="$@"
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $msg" | tee -a "$LOG_FILE"
}

# Function to log with color
log_info() {
    echo -e "${BLUE}ℹ${NC} $@"
    log "INFO" "$@"
}

log_success() {
    echo -e "${GREEN}✓${NC} $@"
    log "SUCCESS" "$@"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $@"
    log "WARNING" "$@"
}

log_error() {
    echo -e "${RED}✗${NC} $@"
    log "ERROR" "$@"
}

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_DIR="$PROJECT_ROOT/mcp_server"

# Ensure environment is loaded
if [ -f ~/.Lambda_env_setup.sh ]; then
    source ~/.Lambda_env_setup.sh
    log_info "Loaded Lambda environment setup"
else
    log_warning "Lambda environment setup not found at ~/.Lambda_env_setup.sh"
fi

# Load server registry if it exists
SERVER_REGISTRY="$MCP_SERVER_DIR/server_registry.json"
if [ -f "$SERVER_REGISTRY" ]; then
    log_info "Loading server registry from $SERVER_REGISTRY"
else
    log_warning "Server registry not found, will scan for available servers"
fi

# Array to store PID and server info
declare -a MCP_PIDS
declare -a MCP_SERVERS

# Function to check if a server file exists and is executable
check_server() {
    local server_path=$1
    if [ -f "$server_path" ]; then
        if python -m py_compile "$server_path" 2>/dev/null; then
            return 0
        else
            log_error "Server file has syntax errors: $server_path"
            return 1
        fi
    else
        log_error "Server file not found: $server_path"
        return 1
    fi
}

# Function to start a server
start_server() {
    local server_name=$1
    local server_path=$2

    log_info "Starting $server_name server..."

    # Check if server exists
    if ! check_server "$server_path"; then
        log_error "Cannot start $server_name - server file issues"
        return 1
    fi

    # Start the server with proper error handling
    python "$server_path" >> "$LOG_FILE" 2>&1 &
    local pid=$!

    # Give server a moment to start
    sleep 1

    # Check if server is still running
    if kill -0 $pid 2>/dev/null; then
        MCP_PIDS+=($pid)
        MCP_SERVERS+=("$server_name")
        log_success "Started $server_name server (PID: $pid)"
        return 0
    else
        log_error "Failed to start $server_name server"
        return 1
    fi
}

# Start MCP servers based on availability
log_info "Starting MCP servers..."

# Define available servers and their paths
declare -A AVAILABLE_SERVERS=(
    ["Lambda-cloud-run"]="$MCP_SERVER_DIR/servers/Lambda_cloud_run_server.py"
    ["Lambda-secrets"]="$MCP_SERVER_DIR/servers/Lambda_secret_manager_server.py"
    ["dragonfly"]="$MCP_SERVER_DIR/servers/dragonfly_server.py"
    ["firestore"]="$MCP_SERVER_DIR/servers/firestore_server.py"
)

# Start each available server
for server_name in "${!AVAILABLE_SERVERS[@]}"; do
    server_path="${AVAILABLE_SERVERS[$server_name]}"
    if [ -f "$server_path" ]; then
        start_server "$server_name" "$server_path" || true
    else
        log_warning "Skipping $server_name - server not found at $server_path"
    fi
done

# Check if any servers were started
if [ ${#MCP_PIDS[@]} -eq 0 ]; then
    log_error "No MCP servers could be started"
    log_info "Please check the log file: $LOG_FILE"
    exit 1
fi

log_success "Started ${#MCP_PIDS[@]} MCP servers"

# Function to cleanup on exit
cleanup() {
    log_info "Stopping MCP servers..."
    for i in "${!MCP_PIDS[@]}"; do
        local pid="${MCP_PIDS[$i]}"
        local server="${MCP_SERVERS[$i]}"
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null || true
            log_info "Stopped $server server (PID: $pid)"
        fi
    done
    log_success "All MCP servers stopped"
}
trap cleanup EXIT INT TERM

# Check if cursor is installed
if ! command -v cursor &> /dev/null; then
    log_error "Cursor is not installed or not in PATH"
    log_info "Please install Cursor from https://cursor.sh"
    exit 1
fi

# Launch Cursor
log_info "Launching Cursor..."
cursor "$PROJECT_ROOT" &
CURSOR_PID=$!

# Show helpful information
log_success "Cursor launched with ${#MCP_PIDS[@]} MCP servers"
log_info "Log file: $LOG_FILE"
log_info "Press Ctrl+C to stop all servers and exit"

# Keep script running and monitor servers
while true; do
    # Check if Cursor is still running
    if ! kill -0 $CURSOR_PID 2>/dev/null; then
        log_info "Cursor has been closed"
        break
    fi

    # Check if servers are still running
    for i in "${!MCP_PIDS[@]}"; do
        local pid="${MCP_PIDS[$i]}"
        local server="${MCP_SERVERS[$i]}"
        if ! kill -0 $pid 2>/dev/null; then
            log_warning "$server server (PID: $pid) has stopped unexpectedly"
            # Attempt to restart
            server_path="${AVAILABLE_SERVERS[$server]}"
            if start_server "$server" "$server_path"; then
                # Update the PID in the array
                MCP_PIDS[$i]=${MCP_PIDS[-1]}
                unset 'MCP_PIDS[-1]'
            fi
        fi
    done

    sleep 5
done
EOF

chmod +x "$PROJECT_ROOT/launch_cursor_with_claude.sh" || error_exit "Failed to make launcher executable"

log_success "Cursor launcher created"

# Create a health check script
log_info "Creating MCP health check script..."
cat > "$PROJECT_ROOT/check_mcp_servers.sh" << 'EOF'
#!/bin/bash
# Check MCP server health

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_DIR="$PROJECT_ROOT/mcp_server"

echo "Checking MCP server availability..."
echo ""

for server_file in "$MCP_SERVER_DIR/servers/"*.py; do
    if [ -f "$server_file" ]; then
        server_name=$(basename "$server_file" .py | sed 's/_server$//' | sed 's/_/-/g')
        echo -n "$server_name: "
        if python -m py_compile "$server_file" 2>/dev/null; then
            echo "✓ Available"
        else
            echo "✗ Has syntax errors"
        fi
    fi
done
EOF

chmod +x "$PROJECT_ROOT/check_mcp_servers.sh"
log_success "Health check script created"

# Provide usage instructions
echo ""
echo -e "${GREEN}=== Claude Code Setup Complete ===${NC}"
echo ""
echo "Setup Summary:"
echo "- Log directory: $LOG_DIR"
echo "- Setup log: $LOG_FILE"
echo "- MCP servers found: $SERVER_COUNT"
echo "- Server registry: $MCP_REGISTRY_FILE"
echo ""
echo "To use Claude Code in Cursor:"
echo "1. Open Cursor's integrated terminal"
echo "2. Run: claude"
echo "3. Authenticate with your Anthropic account (Claude Max)"
echo ""
echo "Quick commands:"
echo "- Launch Claude: Ctrl+Esc (Windows/Linux) or Cmd+Esc (Mac)"
echo "- Insert file reference: Alt+Ctrl+K (Windows/Linux) or Cmd+Option+K (Mac)"
echo ""
echo "Available scripts:"
echo "  ./launch_cursor_with_claude.sh  - Launch Cursor with MCP servers"
echo "  ./check_mcp_servers.sh         - Check MCP server availability"
echo ""
echo "Example Claude commands with MCP:"
echo '- "Deploy my app to Cloud Run staging"'
echo '- "Get the database password from Secret Manager"'
echo '- "Cache this result in DragonflyDB with key user:123"'
echo ""
log_info "Setup complete! Check the log file for details: $LOG_FILE"

#!/bin/bash
# Enhanced setup and verification script for GCP integration in GitHub Codespaces
# This script balances robustness with simplicity and integrates with existing scripts

# Parse command line arguments
IS_REBUILD=false
for arg in "$@"; do
  case $arg in
    --rebuild)
      IS_REBUILD=true
      shift
      ;;
  esac
done

# Set log file based on whether this is a rebuild
if [ "$IS_REBUILD" = true ]; then
  LOG_FILE="/workspaces/orchestra-main/codespace_rebuild.log"
  echo "This is a rebuild operation" > "$LOG_FILE"
else
  LOG_FILE="/workspaces/orchestra-main/codespace_setup.log"
fi

# Redirect output to the log file for debugging
exec > >(tee -i "$LOG_FILE") 2>&1

echo "======================================================"
if [ "$IS_REBUILD" = true ]; then
  echo "  CODESPACE REBUILD VERIFICATION"
else
  echo "  ENHANCED CODESPACE SETUP AND VERIFICATION"
fi
echo "======================================================"
echo "Starting setup at $(date)"
echo "Is rebuild: $IS_REBUILD"

# Function for error handling
handle_error() {
  echo "ERROR: $1"
  echo "See $LOG_FILE for details"
}

# Create necessary directories
echo "Creating required directories..."
mkdir -p $HOME/.gcp
mkdir -p $HOME/.vscode-remote/data/Machine

# Set environment variables for standard mode
echo "Setting environment variables for standard mode..."
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export STANDARD_MODE=true
export DISABLE_WORKSPACE_TRUST=true
export USE_RECOVERY_MODE=false

# Check if running in a recovery container
echo "Checking Codespace environment..."
if grep -q "recovery container" /workspaces/.codespaces/.persistedshare/creation.log 2>/dev/null; then
  echo "NOTE: Running in a recovery container"
  echo "This may indicate issues with the original container configuration"
fi

# Verify GCP service account key
echo "Verifying GCP authentication..."
if [ -f "$HOME/.gcp/service-account.json" ]; then
  echo "Service account key file exists"
  
  # Set credentials environment variable if not already set
  if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
    echo "Set GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
  fi
  
  # Add to .bashrc if not already there (idempotent)
  if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json" $HOME/.bashrc; then
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
    echo "Added GOOGLE_APPLICATION_CREDENTIALS to .bashrc"
  fi
else
  handle_error "Service account key file not found at $HOME/.gcp/service-account.json"
fi

# Update VS Code settings for standard mode (idempotent)
echo "Updating VS Code settings for standard mode..."
SETTINGS_FILE="$HOME/.vscode-remote/data/Machine/settings.json"

# Create or update settings file
if [ -f "$SETTINGS_FILE" ]; then
  # Check if already configured
  if grep -q "security.workspace.trust.enabled" "$SETTINGS_FILE"; then
    echo "Workspace trust settings already exist in settings.json, ensuring they are set correctly"
    # Use sed to update existing settings (platform-independent approach)
    sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' "$SETTINGS_FILE"
    sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' "$SETTINGS_FILE"
  else
    # Append settings to existing file
    TEMP_FILE=$(mktemp)
    # Remove closing brace if it exists
    sed '$ s/}$//' "$SETTINGS_FILE" > "$TEMP_FILE"
    # Add our settings and closing brace
    cat << 'EOF' >> "$TEMP_FILE"
,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
    mv "$TEMP_FILE" "$SETTINGS_FILE"
    echo "Added workspace trust settings to existing settings.json"
  fi
else
  # Create new settings file
  cat << 'EOF' > "$SETTINGS_FILE"
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
  echo "Created new settings.json with workspace trust disabled"
fi

# Verify Poetry installation
echo "Verifying Poetry installation..."
if command -v poetry &> /dev/null; then
  echo "Poetry is installed"
  poetry --version
else
  echo "WARNING: Poetry not found in PATH"
fi

# Verify Python installation
echo "Verifying Python installation..."
if command -v python &> /dev/null; then
  echo "Python is installed"
  python --version
else
  echo "WARNING: Python not found in PATH"
fi

# Verify gcloud installation
echo "Verifying gcloud installation..."
if command -v gcloud &> /dev/null; then
  echo "gcloud is installed"
  gcloud --version
  
  # Test GCP authentication
  echo "Testing GCP authentication..."
  if gcloud auth list 2>&1 | grep -q "Credentialed Accounts"; then
    echo "GCP authentication is configured"
    
    # Verify project configuration
    echo "Verifying GCP project configuration..."
    PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ "$PROJECT" = "cherry-ai-project" ]; then
      echo "GCP project is correctly set to cherry-ai-project"
    else
      echo "WARNING: GCP project is set to $PROJECT, expected cherry-ai-project"
      echo "Setting project to cherry-ai-project..."
      gcloud config set project cherry-ai-project
    fi
    
    # Simple GCP test
    echo "Testing GCP connectivity..."
    if gcloud projects list --limit=1 &>/dev/null; then
      echo "Successfully connected to GCP and accessed projects"
    else
      handle_error "Failed to list GCP projects"
    fi
  else
    echo "WARNING: GCP authentication not configured or failed"
    echo "Attempting to authenticate with service account key..."
    if [ -f "$HOME/.gcp/service-account.json" ]; then
      gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json
      if [ $? -eq 0 ]; then
        echo "Successfully authenticated with GCP"
        gcloud config set project cherry-ai-project
      else
        handle_error "Failed to authenticate with GCP"
      fi
    else
      handle_error "Service account key file not found"
    fi
  fi
else
  echo "WARNING: gcloud not found in PATH"
fi

# Start the MCP memory system
echo "Starting MCP memory system..."
if [ -d "/workspaces/orchestra-main/mcp_server" ]; then
  # Check if the MCP server is already running
  if pgrep -f "python.*mcp_server.main" > /dev/null; then
    echo "MCP server is already running."
  else
    # Copy config if it doesn't exist
    if [ ! -f "/workspaces/orchestra-main/mcp_server/config.json" ]; then
      if [ -f "/workspaces/orchestra-main/mcp_server/config.json.example" ]; then
        cp /workspaces/orchestra-main/mcp_server/config.json.example /workspaces/orchestra-main/mcp_server/config.json
        echo "Created MCP configuration from example"
      fi
    fi
    
    # Start the MCP server in the background
    cd /workspaces/orchestra-main
    nohup python -m mcp_server.main > /tmp/mcp-server.log 2>&1 &
    echo "MCP server started with PID $!"
    echo "Log file: /tmp/mcp-server.log"
  fi
else
  echo "MCP server directory not found, skipping startup"
fi

echo "======================================================"
echo "  SETUP COMPLETE"
echo "======================================================"
echo "Finished at $(date)"
echo ""
echo "To apply environment variables to current session:"
echo "  source ~/.bashrc"

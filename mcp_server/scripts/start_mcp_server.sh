#!/bin/bash

# start_mcp_server.sh - Script to start the MCP memory system
#
# This script detects the environment and starts the MCP server using the
# appropriate method (direct run, Docker, or systemd service).

set -e

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
REPO_ROOT=$(realpath "$SCRIPT_DIR/../..")
CONFIG_FILE="$REPO_ROOT/mcp_server/config.json"
USE_OPTIMIZED=true  # Set to false to disable optimized components

# Create config file if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Creating configuration file..."
  cp "$REPO_ROOT/mcp_server/config.json.example" "$CONFIG_FILE"
  echo "Config file created at $CONFIG_FILE"
fi

# Check if we're in a Docker container
if [ -f "/.dockerenv" ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
  echo "Detected Docker environment"
  METHOD="direct"
# Check if we're in a GitHub Codespace
elif [ -n "$CODESPACES" ] || [ -n "$GITHUB_CODESPACE_TOKEN" ]; then
  echo "Detected GitHub Codespace environment"
  METHOD="direct"
# Check if systemd is available
elif command -v systemctl >/dev/null 2>&1; then
  echo "Detected system with systemd"
  METHOD="systemd"
else
  echo "Standard environment detected"
  METHOD="direct"
fi

case "$METHOD" in
  systemd)
    echo "Starting MCP server via systemd..."
    if [ ! -f "/etc/systemd/system/mcp-server.service" ]; then
      echo "Service not installed. Installing..."
      
      # Check if running as root
      if [ "$EUID" -ne 0 ]; then
        echo "Please run with sudo to install the service"
        exit 1
      fi
      
      "$SCRIPT_DIR/install_mcp_service.sh"
    else
      echo "Service already installed. Starting..."
      sudo systemctl start mcp-server.service
    fi
    
    echo "Service status:"
    systemctl status mcp-server.service --no-pager
    ;;
    
  direct)
    echo "Starting MCP server directly..."
    
    # Check if server is already running
    if pgrep -f "python.*mcp_server.main" > /dev/null; then
      echo "MCP server is already running."
      exit 0
    fi
    
    # Check if Poetry is installed
    if ! command -v poetry &>/dev/null; then
      echo "Poetry not found. Installing Poetry..."
      
      # Check if pip is available
      if ! command -v pip &>/dev/null && ! python -m pip --version &>/dev/null; then
        echo "pip not found. Checking for alternative methods..."
        
        # Try to install pip if get-pip.py is available
        if [ -f "$REPO_ROOT/get-pip.py" ]; then
          echo "Installing pip using get-pip.py..."
          python "$REPO_ROOT/get-pip.py" --user
        else
          echo "Error: pip is not available and cannot be installed automatically."
          echo "Please install pip manually and try again."
          exit 1
        fi
      fi
      
      # Install Poetry
      echo "Installing Poetry..."
      curl -sSL https://install.python-poetry.org | python3 -
      
      # Add Poetry to PATH for this session
      export PATH="$HOME/.local/bin:$PATH"
      
      # Verify Poetry installation
      if ! command -v poetry &>/dev/null; then
        echo "Error: Failed to install Poetry."
        echo "Please install Poetry manually and try again."
        exit 1
      fi
    fi
    
    # Install dependencies and the package
    echo "Installing MCP server dependencies with Poetry..."
    cd "$REPO_ROOT/mcp_server"
    
    # Check if pyproject.toml exists
    if [ ! -f "pyproject.toml" ]; then
      echo "Error: pyproject.toml not found in $REPO_ROOT/mcp_server"
      echo "Please ensure the Poetry configuration is properly set up."
      exit 1
    fi
    
    # Install dependencies
    poetry install
    
    # Start the server in the background
    echo "Starting MCP server in the background..."
    cd "$REPO_ROOT"
    
    # Set environment variable for optimized components if enabled
    if [ "$USE_OPTIMIZED" = true ]; then
      echo "Using optimized storage and memory components"
      export MCP_USE_OPTIMIZED=true
    fi
    
    nohup poetry run mcp-server --config "$CONFIG_FILE" > /tmp/mcp-server.log 2>&1 &
    
    echo "MCP server started. Process ID: $!"
    echo "Log file: /tmp/mcp-server.log"
    echo "To stop the server: pkill -f 'python.*mcp_server.main'"
    ;;
    
  *)
    echo "Error: Unknown method: $METHOD"
    exit 1
    ;;
esac

echo "MCP server is running."
echo "To verify, you can check the status or access the API at: http://localhost:8080/api/status"

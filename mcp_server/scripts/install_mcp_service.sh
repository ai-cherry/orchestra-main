#!/bin/bash

# install_mcp_service.sh - Install and setup MCP service for automatic startup
#
# This script sets up the MCP memory system to run automatically on system startup.
# It installs the systemd service and enables it.

set -e

# Make sure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
REPO_ROOT=$(realpath "$SCRIPT_DIR/../..")
SERVICE_FILE="$SCRIPT_DIR/mcp-server.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "==== MCP Memory System Installation ===="
echo "Repository root: $REPO_ROOT"

# Create configuration if it doesn't exist
CONFIG_FILE="$REPO_ROOT/mcp_server/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Creating configuration file..."
  cp "$REPO_ROOT/mcp_server/config.json.example" "$CONFIG_FILE"
  echo "Config file created at $CONFIG_FILE"
fi

# Install dependencies if needed
echo "Checking for dependencies..."
if ! python -c "import flask" &>/dev/null; then
  echo "Installing dependencies..."
  apt-get update
  apt-get install -y python3-pip
  pip install flask flask-cors flask-socketio requests aiohttp pydantic
fi

# Install package
echo "Installing MCP package..."
cd "$REPO_ROOT"
python -m pip install -e .

# Copy service file to systemd directory
echo "Installing systemd service..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/"

# Update service file with correct paths
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$REPO_ROOT|g" "$SYSTEMD_DIR/mcp-server.service"

# Reload systemd to recognize new service
systemctl daemon-reload

# Enable and start the service
echo "Enabling and starting MCP service..."
systemctl enable mcp-server.service
systemctl start mcp-server.service

echo "MCP service installed and started!"
echo "Status:"
systemctl status mcp-server.service --no-pager

echo ""
echo "To check logs: journalctl -u mcp-server.service -f"
echo "To stop the service: systemctl stop mcp-server.service"
echo "To disable autostart: systemctl disable mcp-server.service"

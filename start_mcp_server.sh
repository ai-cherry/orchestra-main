#!/bin/bash
# start_mcp_server.sh - Simple script to start the MCP server
#
# This script handles the common setup tasks for the MCP server:
# 1. Ensuring Poetry is installed
# 2. Installing dependencies
# 3. Running the server with proper environment variables

set -e

echo "=== MCP Server Startup Helper ==="

# 1. Check if Poetry is installed
if ! command -v poetry &>/dev/null; then
    echo "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Change to the MCP server directory
cd "$(dirname "$0")/mcp_server"

# 3. Install dependencies
echo "Installing dependencies with Poetry..."
poetry install

# 4. Set environment variables for optimized components
export MCP_USE_OPTIMIZED=true

# 5. Start the server
echo "Starting MCP server..."
poetry run python -m mcp_server.run_mcp_server --config ./config.json

# Note: If the server starts successfully but the command doesn't return,
# you may need to press Ctrl+C to stop it
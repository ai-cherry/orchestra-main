#!/bin/bash
# Simple MCP test script

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting Memory MCP server..."
./venv/bin/python -m mcp_server.servers.memory_server 
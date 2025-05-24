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
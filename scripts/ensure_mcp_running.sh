#!/bin/bash
# Ensure MCP is running - add to .bashrc for auto-start

# Only run if we're in an interactive shell and in the orchestra directory
if [[ $- == *i* ]] && [[ "$PWD" == *"orchestra"* ]]; then
    # Check if any MCP service is not running
    MCP_DOWN=false
    for service in mcp-memory mcp-orchestrator mcp-tools mcp-weaviate; do
        if ! systemctl is-active --quiet $service 2>/dev/null; then
            MCP_DOWN=true
            break
        fi
    done
    
    if [ "$MCP_DOWN" = true ]; then
        echo "🚀 Starting MCP services..."
        sudo systemctl start mcp-memory mcp-orchestrator mcp-tools mcp-weaviate 2>/dev/null
        
        # Quick verification
        sleep 2
        RUNNING=$(systemctl is-active mcp-memory mcp-orchestrator mcp-tools mcp-weaviate 2>/dev/null | grep -c "active")
        echo "✅ MCP services started ($RUNNING/4 active)"
    fi
fi 
#!/bin/bash
# Start MCP servers

cd /root/orchestra-main

# Kill any existing MCP processes
pkill -f "mcp_server" || true

# Create logs directory
mkdir -p logs

# Start basic MCP servers
echo "Starting MCP servers..."

# Memory server
nohup python3 -m mcp_server.servers.memory_server > logs/mcp_memory.log 2>&1 &
echo $! > logs/mcp_memory.pid
echo "Memory server started (PID: $(cat logs/mcp_memory.pid))"

# Tools server
nohup python3 -m mcp_server.servers.tools_server > logs/mcp_tools.log 2>&1 &
echo $! > logs/mcp_tools.pid
echo "Tools server started (PID: $(cat logs/mcp_tools.pid))"

# Orchestrator server
nohup python3 -m mcp_server.servers.orchestrator_server > logs/mcp_orchestrator.log 2>&1 &
echo $! > logs/mcp_orchestrator.pid
echo "Orchestrator server started (PID: $(cat logs/mcp_orchestrator.pid))"

echo "All MCP servers started. Check logs/ directory for output."

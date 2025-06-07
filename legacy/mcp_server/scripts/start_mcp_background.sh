#!/bin/bash
# Script to start the MCP memory system in the background
# This script ensures only one instance of MCP is running

# Color output for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set the working directory
cd /workspaces/cherry_ai-main

# Check if configuration exists, create if not
if [ ! -f "mcp_server/config.json" ]; then
  if [ -f "mcp_server/config.json.example" ]; then
    echo -e "${YELLOW}Creating MCP configuration from example...${NC}"
    cp mcp_server/config.json.example mcp_server/config.json
    echo -e "${GREEN}MCP configuration created.${NC}"
  else
    echo -e "${RED}MCP configuration example not found!${NC}"
    exit 1
  fi
fi

# Check if MCP server is already running
if pgrep -f "python.*mcp_server.main" > /dev/null; then
  echo -e "${YELLOW}MCP server is already running.${NC}"
  exit 0
fi

# Start the MCP server in the background
echo -e "${GREEN}Starting MCP memory system in the background...${NC}"
nohup python -m mcp_server.main > /tmp/mcp-server.log 2>&1 &
MCP_PID=$!

# Sleep briefly to check if process is still running
sleep 1
if ps -p $MCP_PID > /dev/null; then
  echo -e "${GREEN}MCP server started successfully with PID $MCP_PID${NC}"
  echo -e "${GREEN}Log file: /tmp/mcp-server.log${NC}"
else
  echo -e "${RED}Failed to start MCP server!${NC}"
  echo -e "${YELLOW}Check log file: /tmp/mcp-server.log${NC}"
  exit 1
fi

exit 0

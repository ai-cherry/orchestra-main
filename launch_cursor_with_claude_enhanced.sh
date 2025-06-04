#!/bin/bash
# Enhanced launcher for Cursor with Claude Code and MCP servers

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Launching AI cherry_ai Development Environment${NC}"

# Load environment
echo -e "${YELLOW}Loading environment...${NC}"
source ~/.Vultr_env_setup.sh 2>/dev/null || true
[ -f .env ] && source .env

# Verify critical services
echo -e "${YELLOW}Verifying services...${NC}"

# Check if MCP servers should auto-start
if [ "${MCP_AUTO_START:-true}" = "true" ]; then
    echo -e "${YELLOW}Starting MCP servers...${NC}"

    # Start MCP servers with proper logging
    mkdir -p logs/mcp

    echo "Starting Cloud Run MCP server..."
    python ~/cherry_ai-main/mcp_server/servers/Vultr_cloud_run_server.py \
        > logs/mcp/cloud_run.log 2>&1 &
    MCP_PIDS+=($!)

    # Add other servers as they're implemented
    # echo "Starting Secret Manager MCP server..."
    # python ~/cherry_ai-main/mcp_server/servers/Vultr_secret_manager_server.py \
    #     > logs/mcp/secrets.log 2>&1 &
    # MCP_PIDS+=($!)

    echo -e "${GREEN}✓ MCP servers started${NC}"
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down MCP servers...${NC}"
    for pid in ${MCP_PIDS[@]}; do
        kill $pid 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}
trap cleanup EXIT

# Launch Cursor
echo -e "${GREEN}Launching Cursor IDE...${NC}"
cursor ~/cherry_ai-main

# Keep script running
wait

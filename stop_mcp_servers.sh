#!/bin/bash
# 🛑 Stop All MCP Servers

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}🛑 Stopping Orchestra AI MCP Servers${NC}"
echo "====================================="

if [ -d ~/.mcp/pids ]; then
    for pid_file in ~/.mcp/pids/*.pid; do
        if [ -f "$pid_file" ]; then
            server_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}Stopping $server_name (PID: $pid)...${NC}"
                kill "$pid" 2>/dev/null || true
                sleep 1
                
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    echo -e "${RED}Force killing $server_name...${NC}"
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
            
            rm -f "$pid_file"
        fi
    done
    echo -e "${GREEN}✅ All MCP servers stopped${NC}"
else
    echo -e "${RED}❌ No PID directory found${NC}"
fi 
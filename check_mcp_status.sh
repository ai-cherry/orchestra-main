#!/bin/bash
# 📊 Check MCP Server Status

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📊 Orchestra AI MCP Server Status${NC}"
echo "=================================="

if [ -d ~/.mcp/pids ]; then
    server_count=0
    running_count=0
    
    for pid_file in ~/.mcp/pids/*.pid; do
        if [ -f "$pid_file" ]; then
            server_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            server_count=$((server_count + 1))
            
            if kill -0 "$pid" 2>/dev/null; then
                # Get memory and uptime info
                mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ' || echo "0")
                uptime=$(ps -p "$pid" -o etime --no-headers 2>/dev/null | tr -d ' ' || echo "unknown")
                echo -e "${GREEN}✅ $server_name${NC}: Running (PID: $pid, Mem: ${mem_usage}%, Uptime: $uptime)"
                running_count=$((running_count + 1))
            else
                echo -e "${RED}❌ $server_name${NC}: Not running (stale PID file)"
                rm -f "$pid_file"
            fi
        fi
    done
    
    echo ""
    echo "Summary: $running_count/$server_count servers running"
    
    if [ $running_count -eq $server_count ] && [ $server_count -gt 0 ]; then
        echo -e "${GREEN}🎉 All servers operational!${NC}"
    elif [ $running_count -gt 0 ]; then
        echo -e "${YELLOW}⚠️ Some servers not running${NC}"
    else
        echo -e "${RED}❌ No servers running${NC}"
    fi
else
    echo -e "${RED}❌ No MCP servers found${NC}"
    echo "Run ./start_mcp_servers_working.sh to start servers"
fi

echo ""
echo -e "${GREEN}🔗 Expected Endpoints:${NC}"
echo "  Unified MCP:        http://localhost:8000"
echo "  Weaviate Direct:    http://localhost:8001"
echo "  Web Scraping:       http://localhost:8012"  
echo "  Infrastructure:     http://localhost:8009"
echo "  Sophia Pay Ready:   http://localhost:8014"

echo ""
echo "📝 Logs: ~/.mcp/logs/"
echo "🚀 Start: ./start_mcp_servers_working.sh"
echo "🛑 Stop:  ./stop_mcp_servers.sh" 
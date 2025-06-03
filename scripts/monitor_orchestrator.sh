#!/bin/bash
# Monitor the Comprehensive AI Orchestrator

echo "📊 Monitoring Comprehensive AI Orchestrator"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check orchestrator process
check_process() {
    if [ -f "orchestrator.pid" ]; then
        PID=$(cat orchestrator.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Orchestrator Process: Running (PID: $PID)${NC}"
        else
            echo -e "${RED}❌ Orchestrator Process: Not Running${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Orchestrator Process: No PID file found${NC}"
    fi
}

# Check service endpoints
check_services() {
    echo -e "\n🔗 Service Status:"
    
    # MCP WebSocket
    if timeout 2 bash -c "echo '' | nc -w 1 localhost 8765" 2>/dev/null; then
        echo -e "${GREEN}✅ MCP WebSocket (8765): Available${NC}"
    else
        echo -e "${RED}❌ MCP WebSocket (8765): Not Available${NC}"
    fi
    
    # Cursor Integration
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/api/v1/status | grep -q "200"; then
        echo -e "${GREEN}✅ Cursor Integration (8090): Available${NC}"
    else
        echo -e "${RED}❌ Cursor Integration (8090): Not Available${NC}"
    fi
    
    # Weaviate
    if curl -s http://localhost:8080/v1/.well-known/ready | grep -q "true"; then
        echo -e "${GREEN}✅ Weaviate (8080): Ready${NC}"
    else
        echo -e "${RED}❌ Weaviate (8080): Not Ready${NC}"
    fi
    
    # PostgreSQL
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL (5432): Ready${NC}"
    else
        echo -e "${RED}❌ PostgreSQL (5432): Not Ready${NC}"
    fi
}

# Check logs
check_logs() {
    echo -e "\n📝 Recent Log Activity:"
    if [ -f "logs/orchestrator.log" ]; then
        echo "Last 10 log entries:"
        tail -n 10 logs/orchestrator.log | sed 's/^/  /'
    else
        echo -e "${YELLOW}⚠️  No log file found${NC}"
    fi
}

# Check resource usage
check_resources() {
    echo -e "\n💻 Resource Usage:"
    if [ -f "orchestrator.pid" ]; then
        PID=$(cat orchestrator.pid)
        if ps -p $PID > /dev/null 2>&1; then
            # Get CPU and memory usage
            ps -p $PID -o pid,vsz,rss,pcpu,pmem,comm | tail -n 1 | \
            awk '{printf "  PID: %s\n  Memory: %.1f MB (%.1f%%)\n  CPU: %.1f%%\n", $1, $3/1024, $5, $4}'
        fi
    fi
}

# Main monitoring loop
if [ "$1" == "--watch" ]; then
    # Continuous monitoring mode
    while true; do
        clear
        echo "📊 Monitoring Comprehensive AI Orchestrator ($(date))"
        echo "=========================================="
        check_process
        check_services
        check_resources
        echo -e "\nPress Ctrl+C to exit..."
        sleep 5
    done
else
    # Single check
    check_process
    check_services
    check_resources
    check_logs
    
    echo -e "\n💡 Tip: Use '$0 --watch' for continuous monitoring"
fi
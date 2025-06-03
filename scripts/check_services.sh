#!/bin/bash
# Check status of Orchestra AI services

echo "🔍 Orchestra AI Service Status"
echo "=============================="
echo ""

# Function to check service
check_service() {
    local name=$1
    local pidfile="logs/mcp_${name}.pid"
    local port=$2
    
    echo -n "• $name server: "
    
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            echo "✓ Running (PID: $pid, Port: $port)"
            
            # Check if port is listening
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                echo "  └─ Port $port: ✓ Listening"
            else
                echo "  └─ Port $port: ⚠️  Not listening"
            fi
        else
            echo "✗ Not running (stale PID file)"
        fi
    else
        echo "✗ Not running"
    fi
}

# Check each service
echo "MCP Servers:"
check_service "orchestrator" "${MCP_ORCHESTRATOR_PORT:-8002}"
check_service "memory" "${MCP_MEMORY_PORT:-8003}"
check_service "tools" "${MCP_TOOLS_PORT:-8006}"
check_service "weaviate" "${MCP_WEAVIATE_DIRECT_PORT:-8001}"

# Check PostgreSQL
echo ""
echo "Database:"
echo -n "• PostgreSQL: "
if pg_isready -h localhost > /dev/null 2>&1; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# Check Weaviate (if configured)
echo -n "• Weaviate: "
if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo "✓ Running"
else
    echo "⚠️  Not running (optional)"
fi

# Show recent logs
echo ""
echo "Recent Activity:"
if [ -d "logs" ]; then
    echo "• Latest log entries:"
    for log in logs/mcp_*.log; do
        if [ -f "$log" ]; then
            service=$(basename "$log" .log | sed 's/mcp_//')
            echo "  └─ $service: $(tail -1 "$log" 2>/dev/null | cut -c1-60)..."
        fi
    done
fi

echo ""
echo "=============================="
echo "Use './scripts/start_all_services.sh' to start services"
echo "Use './scripts/stop_all_services.sh' to stop services"
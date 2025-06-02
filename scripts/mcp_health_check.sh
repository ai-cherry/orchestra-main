#!/bin/bash
# MCP Health Check Script

echo "=== MCP System Health Check ==="
echo ""

# Function to check if a port is listening
check_port() {
    local port=$1
    local service=$2
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "✅ $service (port $port) is listening"
    else
        echo "❌ $service (port $port) is NOT listening"
    fi
}

# Check PostgreSQL
echo "📊 PostgreSQL Status:"
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL is running"
    # Test connection
    if PGPASSWORD=orch3str4_2024 psql -h localhost -U orchestrator -d orchestrator -c "SELECT 1;" >/dev/null 2>&1; then
        echo "✅ PostgreSQL connection successful"
    else
        echo "❌ PostgreSQL connection failed (check password/permissions)"
    fi
else
    echo "❌ PostgreSQL is NOT running"
fi
echo ""

# Check systemd services
echo "🔧 Systemd Service Status:"
for service in mcp-memory mcp-orchestrator mcp-tools mcp-weaviate; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service is running"
    else
        echo "❌ $service is NOT running"
    fi
done
echo ""

# Check ports
echo "🌐 Port Status:"
check_port 8001 "Weaviate Direct MCP"
check_port 8002 "Orchestrator MCP"
check_port 8003 "Memory MCP"
check_port 8006 "Tools MCP"
echo ""

# Check recent logs for errors
echo "📝 Recent Errors (last 10 lines):"
for service in mcp-memory mcp-orchestrator mcp-tools mcp-weaviate; do
    if systemctl is-enabled --quiet $service 2>/dev/null; then
        errors=$(journalctl -u $service -n 10 --no-pager 2>/dev/null | grep -i error | tail -3)
        if [ -n "$errors" ]; then
            echo "⚠️  $service errors:"
            echo "$errors" | sed 's/^/   /'
        fi
    fi
done

echo ""
echo "💡 Quick fixes:"
echo "  - Run setup: bash scripts/setup_mcp_autostart.sh"
echo "  - Restart all: systemctl restart mcp-*.service"
echo "  - View logs: journalctl -u mcp-memory -f" 
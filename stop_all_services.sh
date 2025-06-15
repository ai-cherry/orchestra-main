#!/bin/bash

# 🎼 Orchestra AI - Stop All Services Script
# Safely stops all development services

set -e

echo "🎼 Orchestra AI - Stopping All Services"
echo "======================================"
echo ""

# Function to kill processes by pattern
kill_by_pattern() {
    local pattern=$1
    local description=$2
    
    echo "🛑 Stopping $description..."
    
    # Find PIDs matching the pattern
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "   Found processes: $pids"
        # Try graceful shutdown first
        kill $pids 2>/dev/null || true
        sleep 2
        
        # Check if processes are still running
        still_running=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$still_running" ]; then
            echo "   Forcefully stopping remaining processes: $still_running"
            kill -9 $still_running 2>/dev/null || true
        fi
        echo "   ✅ $description stopped"
    else
        echo "   ℹ️  No $description processes running"
    fi
}

# Stop API servers
kill_by_pattern "python.*api" "API servers"
kill_by_pattern "uvicorn" "Uvicorn servers"

# Stop frontend servers
kill_by_pattern "node.*vite" "Frontend servers"
kill_by_pattern "vite" "Vite development server"

# Stop MCP servers (if running)
kill_by_pattern "mcp.*server" "MCP servers"

# Check for any remaining Orchestra processes
echo ""
echo "🔍 Checking for remaining Orchestra processes..."
remaining=$(ps aux | grep -E "(orchestra|uvicorn|vite)" | grep -v grep | grep -v "stop_all_services" || true)

if [ -n "$remaining" ]; then
    echo "⚠️  Some processes may still be running:"
    echo "$remaining"
    echo ""
    echo "If needed, you can manually stop them with:"
    echo "   pkill -f 'pattern-name'"
else
    echo "✅ All Orchestra services stopped successfully"
fi

echo ""
echo "🔍 Port status check:"
echo "Port 3000 (Frontend): $(lsof -ti :3000 2>/dev/null && echo 'OCCUPIED' || echo 'FREE')"
echo "Port 8000 (API): $(lsof -ti :8000 2>/dev/null && echo 'OCCUPIED' || echo 'FREE')"

echo ""
echo "🎼 All services stopped. Environment is clean."
echo "   Run './start_orchestra.sh' to restart services"
echo "" 
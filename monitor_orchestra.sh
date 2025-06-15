#!/bin/bash

# Simple monitoring script for Orchestra AI
LOG_FILE="$HOME/orchestra-dev/logs/monitor.log"

check_service() {
    local service_name=$1
    local port=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "$(date): ✅ $service_name is healthy" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ❌ $service_name is unhealthy" >> "$LOG_FILE"
        return 1
    fi
}

# Check all services
check_service "MCP Memory Server" 8003
check_service "API Server" 8000
check_service "Frontend" 3002

# Check supervisor process
if pgrep -f "orchestra_supervisor.py" > /dev/null; then
    echo "$(date): ✅ Supervisor is running" >> "$LOG_FILE"
else
    echo "$(date): ❌ Supervisor is not running" >> "$LOG_FILE"
    # Restart supervisor via LaunchAgent
    launchctl stop com.orchestra.ai.supervisor
    launchctl start com.orchestra.ai.supervisor
fi

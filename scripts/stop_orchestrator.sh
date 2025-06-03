#!/bin/bash
# Stop the Comprehensive AI Orchestrator

echo "🛑 Stopping Comprehensive AI Orchestrator..."

# Check for PID file
if [ -f "orchestrator.pid" ]; then
    PID=$(cat orchestrator.pid)
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping orchestrator process (PID: $PID)..."
        kill -TERM $PID
        
        # Wait for graceful shutdown
        sleep 3
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force stopping orchestrator..."
            kill -9 $PID
        fi
        
        echo "✅ Orchestrator stopped"
    else
        echo "⚠️  Orchestrator process not found (PID: $PID)"
    fi
    
    rm -f orchestrator.pid
else
    echo "⚠️  No orchestrator.pid file found"
    
    # Try to find and kill by process name
    PIDS=$(pgrep -f "comprehensive_orchestrator.py")
    if [ ! -z "$PIDS" ]; then
        echo "Found orchestrator processes: $PIDS"
        kill -TERM $PIDS
        sleep 3
        kill -9 $PIDS 2>/dev/null || true
        echo "✅ Orchestrator processes stopped"
    fi
fi

echo "🧹 Cleanup complete"
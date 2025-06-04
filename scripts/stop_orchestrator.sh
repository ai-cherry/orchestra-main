#!/bin/bash
# Stop the Comprehensive AI conductor

echo "🛑 Stopping Comprehensive AI conductor..."

# Check for PID file
if [ -f "conductor.pid" ]; then
    PID=$(cat conductor.pid)
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping conductor process (PID: $PID)..."
        kill -TERM $PID
        
        # Wait for graceful shutdown
        sleep 3
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force stopping conductor..."
            kill -9 $PID
        fi
        
        echo "✅ conductor stopped"
    else
        echo "⚠️  conductor process not found (PID: $PID)"
    fi
    
    rm -f conductor.pid
else
    echo "⚠️  No conductor.pid file found"
    
    # Try to find and kill by process name
    PIDS=$(pgrep -f "comprehensive_conductor.py")
    if [ ! -z "$PIDS" ]; then
        echo "Found conductor processes: $PIDS"
        kill -TERM $PIDS
        sleep 3
        kill -9 $PIDS 2>/dev/null || true
        echo "✅ conductor processes stopped"
    fi
fi

echo "🧹 Cleanup complete"
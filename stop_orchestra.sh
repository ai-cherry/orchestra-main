#!/bin/bash
# Stop Orchestra AI Services

echo "🛑 Stopping Orchestra AI Services..."

# Stop API server
echo "Stopping API server..."
pkill -f "uvicorn agent.app.main" || echo "API server not running"

# Stop any background agents
pkill -f "agent.app" || true

# Clean up any orphaned processes
pkill -f "orchestra" || true

echo "✅ All services stopped"

# Check if anything is still running on port 8000
if lsof -i:8000 > /dev/null 2>&1; then
    echo "⚠️  Warning: Something is still using port 8000:"
    lsof -i:8000
fi

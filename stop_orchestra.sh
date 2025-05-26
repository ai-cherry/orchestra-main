#!/bin/bash
# Orchestra AI - Stop Everything

echo "🛑 Stopping Orchestra AI..."

# Stop Python processes
pkill -f "orchestrator_server.py"
pkill -f "memory_server.py"
pkill -f "uvicorn"

# Stop Docker Compose if running
if command -v docker-compose &> /dev/null; then
    docker-compose down
fi

echo "✓ Orchestra AI stopped"

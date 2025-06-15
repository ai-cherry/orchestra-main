#!/bin/bash
echo "Stopping Orchestra AI services..."

# Kill processes by port
for port in 8000 8001 8002 3000 3001 3002 3003 8003 8004; do
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
done

echo "✅ All services stopped"

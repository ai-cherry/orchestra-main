#!/bin/bash
# Start the Comprehensive AI conductor

set -e

echo "🚀 Starting Comprehensive AI conductor..."

# Check if running in correct directory
if [ ! -f "ai_components/coordination/comprehensive_conductor.py" ]; then
    echo "❌ Error: Must run from cherry_ai-main directory"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Install required dependencies
echo "📦 Installing dependencies..."
pip install -q watchdog websockets aiohttp pyjwt

# Check if services are running
echo "🔍 Checking required services..."

# Check PostgreSQL
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️  PostgreSQL not running. Starting..."
    sudo service postgresql start
fi

# Check Weaviate
if ! curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo "⚠️  Weaviate not running. Starting..."
    docker-compose up -d weaviate
    sleep 10
fi

# Create log directory
mkdir -p logs

# Start the conductor with proper logging
echo "🎯 Starting conductor components..."

# Run with nohup for background execution
nohup python3 -u ai_components/coordination/comprehensive_conductor.py \
    > logs/conductor.log 2>&1 &

CONDUCTOR_PID=$!
echo $CONDUCTOR_PID > conductor.pid

echo "✅ conductor started with PID: $CONDUCTOR_PID"
echo "📝 Logs: tail -f logs/conductor.log"

# Wait a moment for startup
sleep 5

# Check if conductor is running
if ps -p $CONDUCTOR_PID > /dev/null; then
    echo "✅ conductor is running successfully!"
    echo ""
    echo "🔗 Services available at:"
    echo "   - MCP WebSocket: ws://localhost:8765"
    echo "   - Cursor Integration API: http://localhost:8090"
    echo "   - Health Status: http://localhost:8080/health"
    echo ""
    echo "📊 Monitor with: ./scripts/monitor_conductor.sh"
    echo "🛑 Stop with: ./scripts/stop_conductor.sh"
else
    echo "❌ conductor failed to start. Check logs/conductor.log"
    exit 1
fi
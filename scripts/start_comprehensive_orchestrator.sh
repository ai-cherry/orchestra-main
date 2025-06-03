#!/bin/bash
# Start the Comprehensive AI Orchestrator

set -e

echo "🚀 Starting Comprehensive AI Orchestrator..."

# Check if running in correct directory
if [ ! -f "ai_components/orchestration/comprehensive_orchestrator.py" ]; then
    echo "❌ Error: Must run from orchestra-main directory"
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

# Start the orchestrator with proper logging
echo "🎯 Starting orchestrator components..."

# Run with nohup for background execution
nohup python3 -u ai_components/orchestration/comprehensive_orchestrator.py \
    > logs/orchestrator.log 2>&1 &

ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID > orchestrator.pid

echo "✅ Orchestrator started with PID: $ORCHESTRATOR_PID"
echo "📝 Logs: tail -f logs/orchestrator.log"

# Wait a moment for startup
sleep 5

# Check if orchestrator is running
if ps -p $ORCHESTRATOR_PID > /dev/null; then
    echo "✅ Orchestrator is running successfully!"
    echo ""
    echo "🔗 Services available at:"
    echo "   - MCP WebSocket: ws://localhost:8765"
    echo "   - Cursor Integration API: http://localhost:8090"
    echo "   - Health Status: http://localhost:8080/health"
    echo ""
    echo "📊 Monitor with: ./scripts/monitor_orchestrator.sh"
    echo "🛑 Stop with: ./scripts/stop_orchestrator.sh"
else
    echo "❌ Orchestrator failed to start. Check logs/orchestrator.log"
    exit 1
fi
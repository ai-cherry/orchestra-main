#!/bin/bash
# Orchestra AI - Local Development Script
# Starts all services for local development

set -e

echo "🎼 Starting Orchestra AI Development Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Please start Redis first:"
    echo "   brew services start redis (macOS)"
    echo "   sudo service redis-server start (Linux)"
    exit 1
fi

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start backend services
echo "🚀 Starting backend services..."
./orchestra_service_manager.sh start

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        exit 1
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting frontend development server..."
cd modern-admin
npm install
VITE_API_URL=http://localhost:8000 npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Orchestra AI Development Environment Started!"
echo ""
echo "📍 Service URLs:"
echo "   Frontend:    http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   MCP Memory:  http://localhost:8003"
echo ""
echo "📊 Service Status:"
./orchestra_service_manager.sh status
echo ""
echo "🛑 To stop all services, press Ctrl+C"
echo ""

# Trap Ctrl+C to cleanup
trap cleanup INT

cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $FRONTEND_PID 2>/dev/null || true
    ./orchestra_service_manager.sh stop
    echo "✅ All services stopped"
    exit 0
}

# Keep script running
wait $FRONTEND_PID 
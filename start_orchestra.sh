#!/bin/bash
echo "🎼 Starting Orchestra AI Full Stack..."
echo "======================================"

# Start API in background
echo "🚀 Starting API server..."
./start_api.sh &
API_PID=$!

# Wait a moment for API to initialize
sleep 3

# Start frontend
echo "🚀 Starting frontend..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Orchestra AI is starting up!"
echo "🔗 Frontend: http://localhost:3000"
echo "🔗 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $API_PID $FRONTEND_PID; exit' SIGINT
wait

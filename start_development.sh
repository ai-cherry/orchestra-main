#!/bin/bash
# 🚀 Orchestra AI Development Startup Script

echo "🚀 Starting Orchestra AI Development Environment"
echo "=============================================="

cd "/Users/lynnmusil/orchestra-dev"

# Start API service
echo "🔌 Starting API service on port 8010..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload &
API_PID=$!

# Start admin interface
echo "🌐 Starting admin interface on port 5174..."
cd admin-interface
npm run dev &
ADMIN_PID=$!

cd "/Users/lynnmusil/orchestra-dev"

echo ""
echo "✅ Services started:"
echo "   🔌 API: http://localhost:8010"
echo "   🌐 Admin: http://localhost:5174"
echo "   📝 Health: http://localhost:8010/health"

echo ""
echo "🧠 Cursor AI Features:"
echo "   ✅ Auto-approval for safe operations"
echo "   ✅ Context awareness enabled"
echo "   ✅ MCP servers configured"
echo "   ✅ Smart persona routing"

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $API_PID $ADMIN_PID 2>/dev/null; exit' INT
wait

#!/bin/bash

echo "🎼 Orchestra AI - Fix and Deploy Script"
echo "======================================="

# Stop all existing services
echo "🛑 Stopping all existing services..."
./stop_all_services.sh

# Kill any processes on conflicting ports
echo "🔍 Checking for processes on ports 8000, 8003, and 3000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:3002 | xargs kill -9 2>/dev/null || true
lsof -ti:3003 | xargs kill -9 2>/dev/null || true

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data uploads logs backups

# Ensure SQLite database exists
echo "🗄️ Setting up SQLite database..."
if [ ! -f "data/orchestra.db" ]; then
    touch data/orchestra.db
fi

# Fix permissions
echo "🔧 Fixing permissions..."
chmod +x *.sh

# Build and start Docker containers
echo "🐳 Building Docker containers..."
docker-compose build --no-cache

echo "🚀 Starting Orchestra AI services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
echo -n "API Service: "
curl -s http://localhost:8000/api/health >/dev/null && echo "✅ Healthy" || echo "❌ Not responding"

echo -n "MCP Service: "
curl -s http://localhost:8003/health >/dev/null && echo "✅ Healthy" || echo "❌ Not responding"

echo -n "Frontend: "
curl -s http://localhost:3000 >/dev/null && echo "✅ Healthy" || echo "❌ Not responding"

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "📋 Logs (last 20 lines):"
docker-compose logs --tail=20

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access the application at:"
echo "   - Frontend: http://localhost:3000"
echo "   - API: http://localhost:8000/docs"
echo "   - MCP Server: http://localhost:8003/docs"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down" 
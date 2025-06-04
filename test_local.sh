#!/bin/bash
# Quick local test of cherry_ai MCP

echo "🚀 Starting cherry_ai MCP locally..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Access Points:"
echo "   API: http://localhost:8000"
echo "   Grafana: http://localhost:3000"
echo "   Prometheus: http://localhost:9090"

echo ""
echo "🧪 Running health checks..."
curl -s http://localhost:8000/health || echo "API not ready yet"

echo ""
echo "✅ Local deployment complete!"
echo "   Use 'docker-compose logs -f' to view logs"
echo "   Use 'docker-compose down' to stop services"

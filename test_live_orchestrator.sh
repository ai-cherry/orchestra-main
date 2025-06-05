#!/bin/bash

echo "🧪 Testing Live Cherry AI Orchestrator"
echo "======================================"

SERVER_IP="150.136.94.139"

echo "1. Testing Orchestrator UI..."
curl -s http://$SERVER_IP/orchestrator/ | grep -q "cherry-ai-orchestrator-enhanced.js" && echo "✅ Enhanced JS loaded" || echo "❌ Enhanced JS not found"

echo -e "\n2. Testing API endpoints..."
echo "   - Agents endpoint:"
curl -s -X GET http://$SERVER_IP:8000/api/agents -w "\n   Status: %{http_code}\n" || echo "   ❌ Failed"

echo -e "\n   - Orchestrations endpoint:"
curl -s -X GET http://$SERVER_IP:8000/api/orchestrations -w "\n   Status: %{http_code}\n" || echo "   ❌ Failed"

echo -e "\n   - Workflows endpoint:"
curl -s -X GET http://$SERVER_IP:8000/api/workflows -w "\n   Status: %{http_code}\n" || echo "   ❌ Failed"

echo -e "\n3. Testing Weaviate connection..."
curl -s http://$SERVER_IP:8080/v1/.well-known/ready | jq '.' || echo "❌ Weaviate not responding"

echo -e "\n======================================"
echo "📋 Access URLs:"
echo "- Orchestrator UI: http://$SERVER_IP/orchestrator/"
echo "- API Base: http://$SERVER_IP:8000/api/"
echo "- Weaviate: http://$SERVER_IP:8080/"
echo "======================================"

echo -e "\n🌐 Opening in browser..."
open "http://$SERVER_IP/orchestrator/" 2>/dev/null || echo "Please open http://$SERVER_IP/orchestrator/ in your browser"
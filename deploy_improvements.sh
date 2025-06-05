#!/bin/bash
# Deploy improvements to Lambda Labs production server

set -e

LAMBDA_IP="150.136.94.139"
LAMBDA_USER="ubuntu"

echo "🚀 Deploying Orchestra AI Improvements to Lambda Labs..."

# Copy new files
echo "📦 Copying new AI assistant..."
scp ai_assist.py ${LAMBDA_USER}@${LAMBDA_IP}:/opt/cherry-ai/
scp docs/unified_development_plan.md ${LAMBDA_USER}@${LAMBDA_IP}:/opt/cherry-ai/docs/

# Deploy on server
ssh ${LAMBDA_USER}@${LAMBDA_IP} << 'EOF'
cd /opt/cherry-ai

# Make ai_assist.py executable
chmod +x ai_assist.py

# Create symlink for easy access
sudo ln -sf /opt/cherry-ai/ai_assist.py /usr/local/bin/ai_assist

# Add to environment if not already there
if ! grep -q "OPENROUTER_API_KEY" ~/.bashrc; then
    echo '# OpenRouter API for AI assistance' >> ~/.bashrc
    echo 'export OPENROUTER_API_KEY="YOUR_KEY_HERE"' >> ~/.bashrc
    echo '⚠️  Remember to update OPENROUTER_API_KEY in ~/.bashrc'
fi

# Create MCP docker-compose addon
cat > docker-compose.mcp.yml << 'EOFDOCKER'
version: '3.9'

services:
  mcp-filesystem:
    image: anthropics/filesystem-mcp
    volumes:
      - /opt/cherry-ai:/mcp/workspace
    ports:
      - "8080:8080"
    restart: unless-stopped
EOFDOCKER

# Check if MCP service should be started
if command -v docker &> /dev/null; then
    echo "🐳 Starting MCP filesystem server..."
    docker-compose -f docker-compose.mcp.yml up -d
fi

# Create collaboration status script
cat > check_collaboration.sh << 'EOFSCRIPT'
#!/bin/bash
echo "🔍 Orchestra AI Collaboration Status"
echo "===================================="
echo ""
echo "📡 WebSocket Bridge:"
curl -s http://localhost:8765/health || echo "❌ Not responding"
echo ""
echo "🗄️ Databases:"
echo -n "PostgreSQL: "
pg_isready -h localhost -p 5432 && echo "✅" || echo "❌"
echo -n "Redis: "
redis-cli ping > /dev/null 2>&1 && echo "✅" || echo "❌"
echo -n "Weaviate: "
curl -s http://localhost:8082/v1/.well-known/ready > /dev/null && echo "✅" || echo "❌"
echo ""
echo "🤖 Services:"
systemctl is-active cherry-ai | grep -q active && echo "Cherry AI: ✅" || echo "Cherry AI: ❌"
systemctl is-active cherry-ai-bridge | grep -q active && echo "Bridge: ✅" || echo "Bridge: ❌"
EOFSCRIPT

chmod +x check_collaboration.sh

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set OPENROUTER_API_KEY in ~/.bashrc"
echo "2. Configure Cursor IDE to connect to MCP at http://${LAMBDA_IP}:8080"
echo "3. Test AI assistant: ai_assist review main.py"
echo "4. Check status: ./check_collaboration.sh"
EOF

echo ""
echo "✅ Improvements deployed successfully!"
echo ""
echo "🔗 Important endpoints:"
echo "   - Main API: http://${LAMBDA_IP}/"
echo "   - WebSocket: ws://${LAMBDA_IP}:8765"
echo "   - MCP Server: http://${LAMBDA_IP}:8080"
echo ""
echo "📝 Don't forget to:"
echo "   1. Update DNS for cherry-ai.me → ${LAMBDA_IP}"
echo "   2. Set OPENROUTER_API_KEY on the server"
echo "   3. Configure Cursor IDE MCP connection" 
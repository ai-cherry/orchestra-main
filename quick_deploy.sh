#!/bin/bash
# Quick Manual Deployment Script

set -e

echo "🚀 Quick Manual Deployment"
echo "========================="

# Check required environment variables
if [ -z "$VULTR_SERVER_IP" ]; then
    echo "❌ Error: VULTR_SERVER_IP not set"
    echo "Set it with: export VULTR_SERVER_IP=your-server-ip"
    exit 1
fi

if [ ! -f "$HOME/.ssh/vultr_orchestra" ]; then
    echo "❌ Error: SSH key not found at $HOME/.ssh/vultr_orchestra"
    echo "Make sure you have the SSH key configured"
    exit 1
fi

echo "📦 Deploying to Vultr server: $VULTR_SERVER_IP"

# Function to run commands on server
vultr_exec() {
    ssh -i $HOME/.ssh/vultr_orchestra -o StrictHostKeyChecking=no root@$VULTR_SERVER_IP "$@"
}

echo "🔄 Step 1: Pulling latest code on server..."
vultr_exec << 'EOF'
cd /opt/orchestra
git pull origin main
EOF

echo "🐍 Step 2: Installing new dependencies..."
vultr_exec << 'EOF'
cd /opt/orchestra
source venv/bin/activate

# Use the new safe install method with constraints
if [ -f scripts/safe_install.sh ]; then
    echo "Using safe_install.sh..."
    chmod +x scripts/safe_install.sh
    ./scripts/safe_install.sh
else
    # Fallback to old method
    pip install -r requirements/base.txt
fi

# Ensure MCP is installed
pip install mcp portkey-ai -c requirements/constraints.txt 2>/dev/null || pip install mcp portkey-ai
EOF

echo "🔧 Step 3: Updating auth configuration..."
vultr_exec << 'EOF'
cd /opt/orchestra

# Add ORCHESTRA_API_KEY if not already in .env
if ! grep -q "ORCHESTRA_API_KEY" .env 2>/dev/null; then
    echo "" >> .env
    echo "# Simple API Authentication" >> .env
    echo "ORCHESTRA_API_KEY=$(openssl rand -hex 32)" >> .env
    echo "✅ Generated new ORCHESTRA_API_KEY"
fi

chown orchestra:orchestra .env
chmod 600 .env
EOF

echo "🔄 Step 4: Restarting services..."
vultr_exec << 'EOF'
systemctl daemon-reload
systemctl restart orchestra-api orchestra-mcp || true

# Wait for services to start
sleep 10

# Check status
systemctl status orchestra-api --no-pager || echo "API service status check failed"
systemctl status orchestra-mcp --no-pager || echo "MCP service status check failed"
EOF

echo "✅ Step 5: Health check..."
sleep 5

# Test API
echo "Testing API health..."
curl -s http://$VULTR_SERVER_IP:8000/health | jq . || echo "API health check failed"

# Test Weaviate
echo "Testing Weaviate..."
curl -s http://$VULTR_SERVER_IP:8080/v1/.well-known/ready || echo "Weaviate check failed"

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "API: http://$VULTR_SERVER_IP:8000"
echo "API Docs: http://$VULTR_SERVER_IP:8000/docs"
echo "Admin UI: http://$VULTR_SERVER_IP"
echo ""
echo "To get your API key:"
echo "ssh -i ~/.ssh/vultr_orchestra root@$VULTR_SERVER_IP 'grep ORCHESTRA_API_KEY /opt/orchestra/.env'"

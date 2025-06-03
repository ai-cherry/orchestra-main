#!/bin/bash
# Deploy Comprehensive AI Orchestrator to Vultr

set -e

echo "🚀 Deploying Comprehensive AI Orchestrator to Vultr"
echo "=================================================="

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Pulumi
    if ! command -v pulumi &> /dev/null; then
        echo "❌ Pulumi not found. Please install Pulumi first."
        exit 1
    fi
    
    # Check environment variables
    required_vars=(
        "VULTR_API_KEY"
        "DATABASE_URL"
        "JWT_SECRET_KEY"
        "ANTHROPIC_API_KEY"
        "OPENAI_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Missing required environment variable: $var"
            exit 1
        fi
    done
    
    echo "✅ All prerequisites met"
}

# Configure Pulumi
configure_pulumi() {
    echo "⚙️  Configuring Pulumi..."
    
    cd infrastructure
    
    # Set Pulumi configuration
    pulumi config set vultr:api_key "$VULTR_API_KEY" --secret
    pulumi config set db_password "$DB_PASSWORD" --secret
    pulumi config set jwt_secret "$JWT_SECRET_KEY" --secret
    pulumi config set postgres_app_password "$DB_PASSWORD" --secret
    
    # Set SSH key if available
    if [ -f ~/.ssh/id_rsa.pub ]; then
        SSH_KEY=$(cat ~/.ssh/id_rsa.pub)
        pulumi config set ssh_public_key "$SSH_KEY" --secret
    else
        echo "⚠️  No SSH key found. Generating one..."
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
        SSH_KEY=$(cat ~/.ssh/id_rsa.pub)
        pulumi config set ssh_public_key "$SSH_KEY" --secret
    fi
    
    cd ..
}

# Deploy infrastructure
deploy_infrastructure() {
    echo "🏗️  Deploying infrastructure..."
    
    cd infrastructure
    
    # Use the new comprehensive deployment
    rm -f __main__.py.bak
    mv __main__.py __main__.py.bak 2>/dev/null || true
    
    # Create new __main__.py that imports our comprehensive deployment
    cat > __main__.py << 'EOF'
"""Orchestra AI Comprehensive Infrastructure Deployment"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the comprehensive Vultr deployment
from vultr_deployment import *

# The exports are already defined in vultr_deployment.py
EOF
    
    # Run Pulumi deployment
    pulumi up --yes
    
    # Get outputs
    MASTER_IP=$(pulumi stack output master_ip)
    LOAD_BALANCER_IP=$(pulumi stack output load_balancer_ip)
    MCP_WEBSOCKET=$(pulumi stack output mcp_websocket)
    CURSOR_API=$(pulumi stack output cursor_api)
    
    cd ..
    
    echo "✅ Infrastructure deployed successfully"
    echo "   Master IP: $MASTER_IP"
    echo "   Load Balancer: $LOAD_BALANCER_IP"
}

# Deploy application code
deploy_application() {
    echo "📦 Deploying application code..."
    
    # Create deployment package
    tar -czf orchestrator-deploy.tar.gz \
        ai_components \
        scripts \
        requirements.txt \
        .env \
        --exclude='*.pyc' \
        --exclude='__pycache__'
    
    # Copy to master server
    echo "Copying code to master server..."
    scp -o StrictHostKeyChecking=no orchestrator-deploy.tar.gz root@$MASTER_IP:/opt/
    
    # Deploy on master
    ssh -o StrictHostKeyChecking=no root@$MASTER_IP << 'ENDSSH'
cd /opt
tar -xzf orchestrator-deploy.tar.gz
rm orchestrator-deploy.tar.gz

# Install dependencies
pip3 install -r requirements.txt

# Start comprehensive orchestrator
systemctl stop ai-orchestrator 2>/dev/null || true
systemctl stop orchestrator-mcp 2>/dev/null || true

# Update systemd service
cat > /etc/systemd/system/comprehensive-orchestrator.service << 'EOF'
[Unit]
Description=Comprehensive AI Orchestrator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/python3 /opt/ai_components/orchestration/comprehensive_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable comprehensive-orchestrator
systemctl start comprehensive-orchestrator

echo "✅ Application deployed and started"
ENDSSH
    
    # Clean up
    rm -f orchestrator-deploy.tar.gz
}

# Configure DNS (optional)
configure_dns() {
    if [ ! -z "$ORCHESTRATOR_DOMAIN" ]; then
        echo "🌐 Configuring DNS for $ORCHESTRATOR_DOMAIN..."
        
        # This would typically use Vultr DNS API or your DNS provider
        echo "   Please configure your DNS to point to:"
        echo "   A record: @ -> $LOAD_BALANCER_IP"
        echo "   A record: www -> $LOAD_BALANCER_IP"
        echo "   A record: api -> $LOAD_BALANCER_IP"
        echo "   A record: mcp -> $MASTER_IP"
    fi
}

# Main deployment flow
main() {
    check_prerequisites
    configure_pulumi
    deploy_infrastructure
    deploy_application
    configure_dns
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "🔗 Access Points:"
    echo "   API Endpoint: http://$LOAD_BALANCER_IP"
    echo "   MCP WebSocket: $MCP_WEBSOCKET"
    echo "   Cursor API: $CURSOR_API"
    echo ""
    echo "📊 Monitoring:"
    echo "   Grafana: http://$MASTER_IP:3000"
    echo "   Prometheus: http://$MASTER_IP:9090"
    echo ""
    echo "🔧 Management:"
    echo "   SSH to master: ssh root@$MASTER_IP"
    echo "   Check status: ssh root@$MASTER_IP 'systemctl status comprehensive-orchestrator'"
    echo "   View logs: ssh root@$MASTER_IP 'journalctl -u comprehensive-orchestrator -f'"
    echo ""
    echo "⚡ The orchestrator will automatically:"
    echo "   - Monitor coding activities"
    echo "   - Coordinate AI agents (Roo, Factory AI)"
    echo "   - Scale infrastructure based on load"
    echo "   - Provide secure API access for AI models"
}

# Run main deployment
main
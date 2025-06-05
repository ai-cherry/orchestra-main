#!/bin/bash
# Quick Deploy Cherry AI Collaboration Bridge
# Run this when SSH access is available

SERVER_IP="45.32.69.157"
SSH_USER="root"

echo "🚀 Cherry AI Collaboration Bridge Quick Deploy"
echo "============================================="

# Check if we can connect
echo "🔍 Checking SSH access to $SERVER_IP..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SSH_USER@$SERVER_IP "echo 'SSH OK'" 2>/dev/null; then
    echo "✅ SSH access confirmed!"
    
    # Create deployment package
    echo "📦 Creating deployment package..."
    tar -czf cherry_collab_deploy.tar.gz cherry_ai_live_collaboration_bridge.py deploy_collaboration_bridge.py
    
    # Upload and deploy
    echo "📤 Uploading files..."
    scp cherry_collab_deploy.tar.gz $SSH_USER@$SERVER_IP:/tmp/
    
    echo "🚀 Deploying..."
    ssh $SSH_USER@$SERVER_IP << 'EOF'
        cd /tmp
        tar -xzf cherry_collab_deploy.tar.gz
        python3 deploy_collaboration_bridge.py
EOF
    
    echo "✅ Deployment complete!"
    echo "🔗 WebSocket server should be available at ws://$SERVER_IP:8765"
    
else
    echo "❌ Cannot connect to $SERVER_IP via SSH"
    echo ""
    echo "📋 Alternative deployment methods:"
    echo "1. Use Vultr web console to access the server"
    echo "2. Check if SSH port is 22 or different"
    echo "3. Ensure your SSH key is added to the server"
    echo ""
    echo "📦 Files ready for manual deployment in:"
    echo "   - cherry_ai_live_collaboration_bridge.py"
    echo "   - deploy_collaboration_bridge.py"
fi 
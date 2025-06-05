#!/bin/bash
# deploy_react_to_production.sh
# Deploy the enhanced React interface to cherry-ai.me production server

set -e # Exit immediately if a command exits with a non-zero status.

LAMBDA_HOST="ubuntu@150.136.94.139"
REMOTE_WEB_DIR="/var/www/cherry-ai"
LOCAL_BUILD_DIR="src/ui/web/react_app/build"

echo "🚀 Deploying Enhanced React Interface to cherry-ai.me..."

# Step 1: Verify local build exists
if [ ! -d "$LOCAL_BUILD_DIR" ]; then
    echo "❌ Build directory not found at $LOCAL_BUILD_DIR"
    echo "Please run: cd src/ui/web/react_app && npm run build"
    exit 1
fi

echo "✅ Found React build at $LOCAL_BUILD_DIR"

# Step 2: Create a backup of current production content
echo "📦 Creating backup of current production content..."
ssh "$LAMBDA_HOST" << EOF
    sudo mkdir -p /var/backups/cherry-ai
    sudo cp -r $REMOTE_WEB_DIR /var/backups/cherry-ai/backup-\$(date +%Y%m%d-%H%M%S) || true
EOF

# Step 3: Upload the new React build
echo "⬆️  Uploading React build to production server..."
cd "$LOCAL_BUILD_DIR"
tar -czf /tmp/react-build.tar.gz .
scp /tmp/react-build.tar.gz "$LAMBDA_HOST:/tmp/"
rm /tmp/react-build.tar.gz

# Step 4: Deploy on the server
echo "🔧 Deploying React build on production server..."
ssh -t "$LAMBDA_HOST" << EOF
    set -e
    
    echo "    📁 Ensuring web directory exists..."
    sudo mkdir -p $REMOTE_WEB_DIR
    
    echo "    🗑️  Removing old content..."
    sudo rm -rf $REMOTE_WEB_DIR/*
    
    echo "    📦 Extracting new React build..."
    cd $REMOTE_WEB_DIR
    sudo tar -xzf /tmp/react-build.tar.gz
    sudo chown -R www-data:www-data $REMOTE_WEB_DIR
    sudo chmod -R 755 $REMOTE_WEB_DIR
    
    echo "    🧹 Cleaning up temporary files..."
    rm /tmp/react-build.tar.gz
    
    echo "    🔄 Restarting nginx..."
    sudo systemctl reload nginx
    
    echo "    🔍 Checking nginx status..."
    sudo systemctl status nginx --no-pager || true
    
    echo "    ✅ React deployment completed!"
EOF

echo ""
echo "🎉 Enhanced React Interface Successfully Deployed!"
echo ""
echo "🌐 Your website is now live at: http://cherry-ai.me"
echo "🍒 Features now available:"
echo "   • Three AI Personas: Cherry 🍒, Sophia 💼, Karen 🏥"
echo "   • Five Search Modes: Normal, Creative, Deep, Super-Deep, Uncensored"
echo "   • File Upload (up to 5GB)"
echo "   • Multimedia Generation"
echo "   • Real-time Analytics"
echo "   • Modern React/TypeScript UI"
echo ""
echo "⚡ Backend API running on port 8000"
echo "🔧 To deploy backend changes, use: ./deploy_admin_ui.sh"
echo ""
echo "✨ Cherry AI Orchestrator is now live! ✨" 
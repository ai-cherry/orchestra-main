#!/bin/bash
set -euo pipefail

# Production server configuration
PROD_SERVER="45.32.69.157"
PROD_USER="root"
PROD_DIR="/root/orchestra-main"
WEB_ROOT="/var/www/orchestra-admin"

echo "=== Orchestra AI Production Deployment ==="
echo "Deploying to: $PROD_SERVER"

# Step 1: Pull latest code on production
echo "1. Pulling latest code on production server..."
ssh $PROD_USER@$PROD_SERVER << 'EOF'
cd /root/orchestra-main
git pull origin main
echo "✓ Code updated"
EOF

# Step 2: Install dependencies and build Admin UI
echo "2. Building Admin UI on production..."
ssh $PROD_USER@$PROD_SERVER << 'EOF'
cd /root/orchestra-main/admin-ui
npm install --legacy-peer-deps
npm run build
echo "✓ Admin UI built"
EOF

# Step 3: Deploy Admin UI to web root
echo "3. Deploying Admin UI to web root..."
ssh $PROD_USER@$PROD_SERVER << 'EOF'
cd /root/orchestra-main/admin-ui
sudo rsync -av --delete dist/ /var/www/orchestra-admin/
echo "✓ Admin UI deployed"
EOF

# Step 4: Restart backend services
echo "4. Restarting backend services..."
ssh $PROD_USER@$PROD_SERVER << 'EOF'
# Kill any existing Python processes on port 8001
sudo lsof -ti:8001 | xargs -r sudo kill -9 || true

# Start the real agent backend
cd /root/orchestra-main
source venv/bin/activate
nohup python -m agent.app.main > /var/log/orchestra-backend.log 2>&1 &
sleep 3
echo "✓ Backend restarted"
EOF

# Step 5: Reload nginx
echo "5. Reloading nginx..."
ssh $PROD_USER@$PROD_SERVER << 'EOF'
sudo nginx -t && sudo systemctl reload nginx
echo "✓ Nginx reloaded"
EOF

# Step 6: Verify deployment
echo "6. Verifying deployment..."
ssh $PROD_USER@$PROD_SERVER << 'EOF'
# Check if backend is responding
if curl -s -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" http://localhost:8001/api/agents | grep -q "sys-001"; then
    echo "✓ Backend API is responding with real agent data"
else
    echo "✗ Backend API check failed"
    exit 1
fi

# Check if nginx is serving the UI
if curl -s http://localhost | grep -q "Cherry Admin UI"; then
    echo "✓ Admin UI is being served"
else
    echo "✗ Admin UI check failed"
    exit 1
fi
EOF

echo ""
echo "=== Deployment Complete ==="
echo "Access the site at: https://cherry-ai.me"
echo "Login with:"
echo "  - Email: any email (e.g., admin@cherry-ai.me)"
echo "  - Password: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"

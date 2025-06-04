#!/bin/bash
# Quick deployment script for real agents

echo "🚀 Deploying Cherry AI with REAL agents..."

# Server details
SERVER="45.32.69.157"
PASSWORD='z+G3D,$n9M3.=Dr}'

# Create deployment command
DEPLOY_CMD='
cd /root/cherry_ai-main

# Stop any existing API
pkill -f uvicorn || true
sleep 2

# Start the real API
source venv/bin/activate
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8080 > /root/api_real.log 2>&1 &
sleep 3

# Test the API
echo "Testing API..."
curl -s -X GET "http://localhost:8080/api/agents" \
     -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | \
     python3 -m json.tool | head -20

# Install nodejs if needed
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# Install pnpm
npm install -g pnpm

# Build Admin UI
cd admin-ui
pnpm install --no-frozen-lockfile
pnpm build

# Deploy to web root
mkdir -p /var/www/cherry_ai-admin
cp -r dist/* /var/www/cherry_ai-admin/

# Configure nginx
cat > /etc/nginx/sites-available/cherry_ai-admin << EOF
server {
    listen 80;
    server_name cherry-ai.me;

    root /var/www/cherry_ai-admin;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/cherry_ai-admin /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "✅ Deployment complete!"
echo "🌐 Visit https://cherry-ai.me to see your REAL AI agents!"
'

# Execute on server
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER "$DEPLOY_CMD"

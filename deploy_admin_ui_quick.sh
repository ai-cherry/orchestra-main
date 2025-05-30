#!/bin/bash
# Quick Admin UI Build & Deploy Script

set -e

VULTR_IP="45.32.69.157"

echo "🚀 Building & Deploying Admin UI"
echo "================================"

# Check if pnpm is installed locally
if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    npm install -g pnpm
fi

# Build Admin UI locally
echo "📦 Building Admin UI..."
cd admin-ui
pnpm install --frozen-lockfile
NODE_ENV=production pnpm build

echo "✅ Build complete! Files in admin-ui/dist/"

# Deploy to server
echo "🚢 Deploying to Vultr server..."
ssh -i ~/.ssh/vultr_orchestra root@$VULTR_IP 'mkdir -p /var/www/orchestra-admin'

# Copy built files
scp -i ~/.ssh/vultr_orchestra -r dist/* root@$VULTR_IP:/var/www/orchestra-admin/

# Update nginx configuration
echo "🔧 Updating nginx configuration..."
ssh -i ~/.ssh/vultr_orchestra root@$VULTR_IP << 'EOF'
cat > /etc/nginx/sites-available/orchestra << 'NGINX'
server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me _;

    # Admin UI (default)
    location / {
        root /var/www/orchestra-admin;
        try_files $uri $uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Direct API access (for backward compatibility)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    # Weaviate proxy
    location /weaviate/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
NGINX

# Test and reload nginx
nginx -t && systemctl reload nginx
echo "✅ Nginx configuration updated!"
EOF

echo ""
echo "🎉 Admin UI Deployed Successfully!"
echo "=================================="
echo ""
echo "Your website is now available at:"
echo "- http://45.32.69.157 (Direct IP)"
echo "- http://cherry-ai.me (After DNS update)"
echo ""
echo "API endpoints moved to:"
echo "- http://45.32.69.157/api/*"
echo "- http://45.32.69.157/health"
echo "- http://45.32.69.157/docs"
echo ""
echo "⚠️  Don't forget to update DNS:"
echo "   cherry-ai.me A record → 45.32.69.157" 
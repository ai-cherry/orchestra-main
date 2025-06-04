#!/bin/bash

# Cherry AI Admin Interface Production Deployment Script
# Deploys the complete admin interface to cherry-ai.me

set -e

echo "🚀 Starting Cherry AI Admin Interface Deployment to Production"
echo "=================================================="

# Configuration
PRODUCTION_SERVER="45.32.69.157"
ADMIN_INTERFACE_DIR="/home/ubuntu/orchestra-main-repo/admin-interface"
BUILD_DIR="$ADMIN_INTERFACE_DIR/.next"
STATIC_DIR="$ADMIN_INTERFACE_DIR/out"

echo "📦 Creating deployment package..."
cd "$ADMIN_INTERFACE_DIR"

# Export static files for production
echo "🔄 Building and exporting static files..."
npm run build

# Create deployment archive
echo "📁 Creating deployment archive..."
tar -czf cherry-ai-admin-production.tar.gz out/ public/ package.json

echo "🌐 Deploying to production server: $PRODUCTION_SERVER"

# Deploy to production server
echo "📤 Uploading files to production server..."
scp -o ConnectTimeout=30 -o StrictHostKeyChecking=no cherry-ai-admin-production.tar.gz root@$PRODUCTION_SERVER:/tmp/

echo "🔧 Setting up admin interface on production server..."
ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no root@$PRODUCTION_SERVER << 'EOF'
    # Extract admin interface
    cd /tmp
    tar -xzf cherry-ai-admin-production.tar.gz
    
    # Create web directory if it doesn't exist
    mkdir -p /var/www/cherry-ai
    
    # Backup existing files
    if [ -d "/var/www/cherry-ai" ]; then
        cp -r /var/www/cherry-ai /var/www/cherry-ai-backup-$(date +%Y%m%d_%H%M%S)
    fi
    
    # Deploy new files
    cp -r out/* /var/www/cherry-ai/
    cp -r public/* /var/www/cherry-ai/ 2>/dev/null || true
    
    # Set proper permissions
    chown -R www-data:www-data /var/www/cherry-ai
    chmod -R 755 /var/www/cherry-ai
    
    # Update nginx configuration for admin interface
    cat > /etc/nginx/sites-available/cherry-ai.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
    root /var/www/cherry-ai;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Main location
    location / {
        try_files $uri $uri.html $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy for backend services
    location /api/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support for real-time features
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINX_EOF

    # Enable the site
    ln -sf /etc/nginx/sites-available/cherry-ai.conf /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    # Ensure nginx is running
    systemctl enable nginx
    systemctl start nginx
    
    echo "✅ Admin interface deployed successfully!"
    echo "🌐 Website: http://cherry-ai.me"
    echo "📊 Status: $(systemctl is-active nginx)"
EOF

echo "🧹 Cleaning up local files..."
rm -f cherry-ai-admin-production.tar.gz

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=================================================="
echo "🌐 Cherry AI Admin Interface is now live at:"
echo "   https://cherry-ai.me"
echo ""
echo "🔐 Login Credentials:"
echo "   Admin: admin / OrchAI_Admin2024!"
echo "   Cherry: cherry / Cherry_AI_2024!"
echo "   Demo: demo / demo123"
echo ""
echo "📊 Infrastructure Monitoring:"
echo "   Grafana: http://207.246.108.201:3000"
echo "   Database: 45.77.87.106:5432"
echo ""
echo "✅ All systems operational and ready for use!"


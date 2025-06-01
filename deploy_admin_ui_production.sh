#!/bin/bash
#
# Production-grade deployment script with cache busting
#

set -e

echo "🚀 Production Admin UI Deployment"
echo "================================="

# Build with unique hash for cache busting
cd admin-ui
echo "🔨 Building with cache busting..."
rm -rf dist

# Add timestamp to environment for cache busting
export VITE_BUILD_TIME=$(date +%s)
pnpm run build-no-ts

# Deploy with proper cache headers
echo "📤 Deploying with cache control..."
sudo rm -rf /var/www/orchestra-admin/*
sudo cp -r dist/* /var/www/orchestra-admin/
sudo chown -R www-data:www-data /var/www/orchestra-admin/

# Update nginx config with aggressive cache busting
sudo tee /etc/nginx/sites-available/orchestra-admin > /dev/null << 'NGINX'
server {
    listen 80;
    server_name cherry-ai.me;
    root /var/www/orchestra-admin;

    # Force no caching for index.html
    location = /admin/index.html {
        alias /var/www/orchestra-admin/index.html;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Admin UI - serve static files
    location /admin/ {
        alias /var/www/orchestra-admin/;
        try_files $uri $uri/ /admin/index.html;
        
        # No cache for HTML
        location ~* \.html$ {
            add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        }
        
        # Cache assets with unique hashes for 1 year
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            add_header Cache-Control "public, max-age=31536000, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Root redirect
    location = / {
        return 301 /admin/;
    }
}
NGINX

# Reload nginx
sudo nginx -t && sudo nginx -s reload

echo "✅ Deployment complete - NO CACHE CLEARING NEEDED!"
echo "🌐 Site: https://cherry-ai.me/admin/" 
#!/bin/bash
# Quick script to fix cache issues on Vultr

echo "🔧 Fixing Orchestra Admin cache issues..."

# Update code
cd /root/orchestra-main
git pull

# Build with cache busting
cd admin-ui
npm run build

# Deploy new nginx config
sudo cp /root/orchestra-main/scripts/nginx_orchestra_admin_nocache.conf /etc/nginx/sites-available/orchestra

# Test nginx
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded with no-cache config"
else
    echo "❌ Nginx config error!"
    exit 1
fi

# Deploy fresh build
sudo rm -rf /var/www/orchestra-admin/*
sudo cp -r dist/* /var/www/orchestra-admin/

echo "✅ Cache fix applied! Test at https://cherry-ai.me"
echo "🔒 Use incognito/private window to verify"

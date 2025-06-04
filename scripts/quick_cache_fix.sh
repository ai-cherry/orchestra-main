#!/bin/bash
# Quick script to fix cache issues on Vultr

echo "🔧 Fixing cherry_ai Admin cache issues..."

# Update code
cd /root/cherry_ai-main
git pull

# Build with cache busting
cd admin-ui
npm run build

# Deploy new nginx config
sudo cp /root/cherry_ai-main/scripts/nginx_cherry_ai_admin_nocache.conf /etc/nginx/sites-available/cherry_ai

# Test nginx
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded with no-cache config"
else
    echo "❌ Nginx config error!"
    exit 1
fi

# Deploy fresh build
sudo rm -rf /var/www/cherry_ai-admin/*
sudo cp -r dist/* /var/www/cherry_ai-admin/

echo "✅ Cache fix applied! Test at https://cherry-ai.me"
echo "🔒 Use incognito/private window to verify"

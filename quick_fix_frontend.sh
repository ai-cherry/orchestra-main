#!/bin/bash
# Quick fix for cherry-ai.me frontend version issue

set -e

echo "🚀 Quick Frontend Fix for cherry-ai.me"
echo "====================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Build the latest frontend
echo -e "\n${YELLOW}Building latest frontend...${NC}"
cd /root/orchestra-main/admin-ui

# Quick build (skip if node_modules exists)
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build

# 2. Find where nginx is serving from
echo -e "\n${YELLOW}Finding nginx root directory...${NC}"
NGINX_ROOT=$(grep -h "root" /etc/nginx/sites-enabled/* 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || echo "/var/www/html")
echo "Nginx root: $NGINX_ROOT"

# 3. Backup and deploy
echo -e "\n${YELLOW}Deploying new frontend...${NC}"
sudo rm -rf "$NGINX_ROOT"/*
sudo cp -r dist/* "$NGINX_ROOT/"
sudo chown -R www-data:www-data "$NGINX_ROOT"

# 4. Clear nginx cache
sudo nginx -s reload

echo -e "\n${GREEN}✓ Frontend updated!${NC}"
echo "Visit https://cherry-ai.me in incognito mode to see the new version."
echo ""
echo "If you use Cloudflare:"
echo "1. Log into Cloudflare"
echo "2. Go to Caching → Configuration"
echo "3. Click 'Purge Everything'"
#!/bin/bash

# Quick Fix for Cherry AI Deployment Issues
# Based on diagnostic findings

set -e

echo "🔧 CHERRY AI QUICK FIX"
echo "====================="
echo "Fixing identified issues..."
echo ""

# Configuration
LAMBDA_IP="150.136.94.139"
USERNAME="ubuntu"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}STEP 1: Checking current state${NC}"
echo "================================"

# Check which HTML file is using enhanced JS
ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Checking which files use enhanced JS..."
cd /opt/orchestra
for html in *.html; do
    if grep -q "cherry-ai-orchestrator-enhanced.js" "$html" 2>/dev/null; then
        echo "✅ $html uses enhanced JS"
    else
        echo "❌ $html uses old JS"
    fi
done
EOF

echo ""
echo -e "${YELLOW}STEP 2: Fixing Nginx Configuration${NC}"
echo "==================================="

# Create proper nginx configuration
ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Creating orchestra nginx configuration..."

# Create the nginx config
sudo tee /etc/nginx/sites-available/orchestra > /dev/null << 'NGINX'
server {
    listen 80;
    server_name 150.136.94.139;
    
    # Main orchestrator location
    location /orchestrator/ {
        alias /opt/orchestra/;
        index cherry-ai-orchestrator-final.html;
        try_files $uri $uri/ /orchestrator/cherry-ai-orchestrator-final.html;
        
        # Disable all caching
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        add_header Pragma "no-cache";
        add_header X-Content-Type-Options "nosniff";
        
        # Force refresh
        add_header Last-Modified $date_gmt;
        add_header Cache-Control 'private';
        if_modified_since off;
        etag off;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
    
    # Root redirect
    location = / {
        return 301 /orchestrator/;
    }
}
NGINX

# Enable the site
sudo ln -sf /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
echo "✅ Nginx configuration updated"
EOF

echo ""
echo -e "${YELLOW}STEP 3: Ensuring correct files are served${NC}"
echo "=========================================="

ssh $USERNAME@$LAMBDA_IP << 'EOF'
cd /opt/orchestra

# Make sure the final HTML uses enhanced JS
if ! grep -q "cherry-ai-orchestrator-enhanced.js" cherry-ai-orchestrator-final.html; then
    echo "Updating cherry-ai-orchestrator-final.html to use enhanced JS..."
    sudo sed -i 's/cherry-ai-orchestrator\.js/cherry-ai-orchestrator-enhanced.js/g' cherry-ai-orchestrator-final.html
    echo "✅ Updated to use enhanced JS"
else
    echo "✅ Already using enhanced JS"
fi

# Set proper permissions
sudo chown -R www-data:www-data /opt/orchestra
sudo chmod -R 755 /opt/orchestra

# Clear any server-side cache
sudo rm -rf /var/cache/nginx/*
echo "✅ Cleared server cache"
EOF

echo ""
echo -e "${YELLOW}STEP 4: Testing the deployment${NC}"
echo "==============================="

# Test orchestrator endpoint
echo -e "${BLUE}Testing orchestrator access...${NC}"
RESPONSE=$(curl -s -I http://$LAMBDA_IP/orchestrator/ | head -1)
if [[ $RESPONSE == *"200"* ]] || [[ $RESPONSE == *"301"* ]] || [[ $RESPONSE == *"302"* ]]; then
    echo -e "${GREEN}✅ Orchestrator endpoint responding${NC}"
else
    echo -e "${RED}❌ Orchestrator endpoint not responding properly${NC}"
    echo "Response: $RESPONSE"
fi

# Test API
echo -e "\n${BLUE}Testing API health...${NC}"
API_HEALTH=$(curl -s http://$LAMBDA_IP/api/health | jq -r '.status' 2>/dev/null || echo "Failed")
if [[ $API_HEALTH == "healthy" ]]; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API health check failed: $API_HEALTH${NC}"
fi

# Check which JS file is actually being served
echo -e "\n${BLUE}Verifying JavaScript file...${NC}"
JS_CHECK=$(curl -s http://$LAMBDA_IP/orchestrator/cherry-ai-orchestrator-final.html | grep -o 'src="[^"]*\.js"' | head -1)
echo "HTML is loading: $JS_CHECK"

echo ""
echo -e "${GREEN}✅ FIXES APPLIED${NC}"
echo "================"
echo ""
echo -e "${BLUE}IMPORTANT NEXT STEPS:${NC}"
echo "1. Clear your browser cache completely (Ctrl+Shift+Delete)"
echo "2. Open in incognito/private mode first"
echo "3. Visit: http://$LAMBDA_IP/orchestrator/"
echo "4. Press F12 and check Console for any errors"
echo "5. Verify you see real data, not mock alerts"
echo ""
echo -e "${YELLOW}To monitor deployment status:${NC}"
echo "./monitor_cherry_deployment.py"
echo ""
echo -e "${YELLOW}If issues persist:${NC}"
echo "- Check browser Network tab (F12) to see which files are loading"
echo "- Look for 304 Not Modified responses (indicates caching)"
echo "- Try adding ?v=$(date +%s) to the URL to force refresh"
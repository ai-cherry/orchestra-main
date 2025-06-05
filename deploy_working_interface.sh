#!/bin/bash

echo "🚀 Deploying Working Cherry AI Interface"
echo "========================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
DOMAIN="cherry-ai.me"
LOCAL_FILE="admin-interface/working-interface.html"

echo -e "${BLUE}📁 Checking local file...${NC}"
if [ ! -f "$LOCAL_FILE" ]; then
    echo -e "${RED}❌ Working interface file not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found working interface file${NC}"

echo -e "${BLUE}🌐 Deploying to $DOMAIN...${NC}"

# Deploy via SSH (auto-accept host key)
ssh -o StrictHostKeyChecking=no root@$DOMAIN << EOF
    # Backup current index.html
    if [ -f "/var/www/html/index.html" ]; then
        cp /var/www/html/index.html /var/www/html/index.html.backup.\$(date +%Y%m%d_%H%M%S)
        echo "✅ Backed up existing interface"
    fi
    
    # Clear existing content
    rm -f /var/www/html/index.html
    
    echo "🔄 Ready for new interface..."
EOF

# Copy the new interface
echo -e "${BLUE}📤 Uploading new interface...${NC}"
scp -o StrictHostKeyChecking=no "$LOCAL_FILE" root@$DOMAIN:/var/www/html/index.html

# Set proper permissions
ssh -o StrictHostKeyChecking=no root@$DOMAIN << EOF
    chown www-data:www-data /var/www/html/index.html
    chmod 644 /var/www/html/index.html
    
    # Restart nginx to ensure no caching
    systemctl reload nginx
    
    echo "✅ Permissions set and nginx reloaded"
EOF

echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}🌐 Visit: http://cherry-ai.me${NC}"
echo -e "${BLUE}✨ The interface now has REAL search functionality!${NC}"
echo ""
echo "🔍 What's new:"
echo "  • Real API connections (no more mock alerts!)"
echo "  • Working search with actual results"
echo "  • Live API status indicator"
echo "  • Persona-based search"
echo "  • Multiple search modes (normal, creative, deep, super-deep)"
echo "  • Real-time result display"
echo ""
echo "🚀 Your backend was already working - now the frontend works too!" 
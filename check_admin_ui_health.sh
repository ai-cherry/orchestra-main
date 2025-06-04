#!/bin/bash
#
# check_admin_ui_health.sh
#
# Health check script for Admin UI deployment
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏥 Admin UI Health Check${NC}"
echo -e "${BLUE}========================${NC}"
echo

# Check nginx status
echo -e "${BLUE}1. Checking Nginx Status...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is not running${NC}"
fi

# Check nginx sites
echo -e "\n${BLUE}2. Checking Nginx Configuration...${NC}"
if [ -f "/etc/nginx/sites-enabled/cherry_ai-admin" ]; then
    echo -e "${GREEN}✓ Admin UI site configuration found${NC}"
else
    echo -e "${RED}✗ Admin UI site configuration missing${NC}"
fi

# Check deployment files
echo -e "\n${BLUE}3. Checking Deployment Files...${NC}"
NGINX_DIR="/var/www/cherry_ai-admin"

if [ -d "$NGINX_DIR" ]; then
    echo -e "${GREEN}✓ Deployment directory exists${NC}"
    
    # Check key files
    files_to_check=("index.html" "assets")
    for file in "${files_to_check[@]}"; do
        if [ -e "$NGINX_DIR/$file" ]; then
            echo -e "${GREEN}  ✓ $file exists${NC}"
        else
            echo -e "${RED}  ✗ $file missing${NC}"
        fi
    done
    
    # Count assets
    if [ -d "$NGINX_DIR/assets" ]; then
        js_count=$(find "$NGINX_DIR/assets" -name "*.js" 2>/dev/null | wc -l)
        css_count=$(find "$NGINX_DIR/assets" -name "*.css" 2>/dev/null | wc -l)
        echo -e "${BLUE}  → Found $js_count JS files, $css_count CSS files${NC}"
    fi
else
    echo -e "${RED}✗ Deployment directory not found${NC}"
fi

# Check local access
echo -e "\n${BLUE}4. Testing Local Access...${NC}"
local_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/admin/")
if [ "$local_status" -eq 200 ]; then
    echo -e "${GREEN}✓ Local access successful (HTTP $local_status)${NC}"
    
    # Check for error page
    content=$(curl -s "http://localhost/admin/")
    if echo "$content" | grep -q "Something went wrong"; then
        echo -e "${RED}  ⚠ Error page is being displayed${NC}"
    elif echo "$content" | grep -q "<div id=\"root\"></div>"; then
        echo -e "${GREEN}  ✓ App container found${NC}"
    fi
else
    echo -e "${RED}✗ Local access failed (HTTP $local_status)${NC}"
fi

# Check external access
echo -e "\n${BLUE}5. Testing External Access...${NC}"
external_status=$(curl -s -o /dev/null -w "%{http_code}" "https://cherry-ai.me/admin/" || echo "0")
if [ "$external_status" -eq 200 ]; then
    echo -e "${GREEN}✓ External access successful (HTTP $external_status)${NC}"
else
    echo -e "${YELLOW}⚠ External access returned HTTP $external_status${NC}"
    echo -e "${YELLOW}  This might be due to DNS or SSL issues${NC}"
fi

# Check API backend
echo -e "\n${BLUE}6. Checking API Backend...${NC}"
api_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" || echo "0")
if [ "$api_status" -eq 200 ]; then
    echo -e "${GREEN}✓ API backend is running${NC}"
else
    echo -e "${YELLOW}⚠ API backend returned HTTP $api_status${NC}"
    echo -e "${YELLOW}  The admin UI may not function properly without the API${NC}"
fi

# Check recent logs
echo -e "\n${BLUE}7. Recent Nginx Error Logs...${NC}"
if [ -f "/var/log/nginx/error.log" ]; then
    recent_errors=$(sudo tail -5 /var/log/nginx/error.log 2>/dev/null | grep -E "admin|cherry_ai" | wc -l)
    if [ "$recent_errors" -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $recent_errors recent error log entries:${NC}"
        sudo tail -5 /var/log/nginx/error.log | grep -E "admin|cherry_ai" | sed 's/^/  /'
    else
        echo -e "${GREEN}✓ No recent errors in nginx logs${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Cannot access nginx error logs${NC}"
fi

# Summary
echo -e "\n${BLUE}Summary:${NC}"
echo -e "${BLUE}========${NC}"

if [ "$local_status" -eq 200 ] && [ -d "$NGINX_DIR" ]; then
    if echo "$content" | grep -q "Something went wrong"; then
        echo -e "${YELLOW}⚠ Admin UI is deployed but showing an error page${NC}"
        echo -e "  → This indicates a JavaScript runtime error"
        echo -e "  → Check browser console for specific errors"
        echo -e "  → Run: journalctl -u nginx -n 50"
    else
        echo -e "${GREEN}✓ Admin UI appears to be working correctly${NC}"
    fi
else
    echo -e "${RED}✗ Admin UI deployment has issues${NC}"
    echo -e "  → Run: ./deploy_admin_ui_safe.sh to redeploy"
fi

echo
echo -e "${BLUE}URLs:${NC}"
echo -e "  Local:    http://localhost/admin/"
echo -e "  External: https://cherry-ai.me/admin/" 
#!/bin/bash
# Diagnostic script for cherry-ai.me deployment issues

echo "🔍 Diagnosing Cherry AI Deployment..."
echo "====================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check service
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}✓ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 is not running${NC}"
        return 1
    fi
}

# 1. Check system services
echo -e "\n${BLUE}1. System Services Status:${NC}"
check_service nginx
check_service orchestra-backend || echo "  (Backend service might not exist yet)"

# 2. Check nginx configuration
echo -e "\n${BLUE}2. Nginx Configuration:${NC}"
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "Default nginx site is enabled"
    NGINX_ROOT=$(grep -E "^\s*root" /etc/nginx/sites-enabled/default 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';')
    echo "Nginx root: ${NGINX_ROOT:-Not found}"
fi

if [ -f "/etc/nginx/sites-enabled/cherry-ai" ]; then
    echo -e "${GREEN}✓ cherry-ai nginx config exists${NC}"
else
    echo -e "${YELLOW}⚠ cherry-ai nginx config not found${NC}"
fi

# 3. Check frontend files
echo -e "\n${BLUE}3. Frontend Files:${NC}"
COMMON_PATHS=("/var/www/html" "/usr/share/nginx/html" "/var/www/cherry-ai")
FRONTEND_FOUND=false

for path in "${COMMON_PATHS[@]}"; do
    if [ -d "$path" ] && [ -f "$path/index.html" ]; then
        echo "Found frontend at: $path"
        echo -n "  Last modified: "
        stat -c %y "$path/index.html" | cut -d' ' -f1,2
        FRONTEND_FOUND=true
        
        # Check if it's the new version by looking for specific markers
        if grep -q "Cherry Admin" "$path/index.html" 2>/dev/null; then
            echo -e "  ${GREEN}✓ Appears to be Cherry Admin UI${NC}"
        else
            echo -e "  ${YELLOW}⚠ May be old version${NC}"
        fi
    fi
done

if [ "$FRONTEND_FOUND" = false ]; then
    echo -e "${RED}✗ No frontend files found in common locations${NC}"
fi

# 4. Check backend status
echo -e "\n${BLUE}4. Backend API Status:${NC}"

# Check if backend process is running
if pgrep -f "uvicorn.*agent.app.main" > /dev/null; then
    echo -e "${GREEN}✓ Uvicorn process is running${NC}"
    BACKEND_PID=$(pgrep -f "uvicorn.*agent.app.main")
    echo "  PID: $BACKEND_PID"
else
    echo -e "${RED}✗ Uvicorn process not found${NC}"
fi

# Check if port 8000 is listening
if netstat -tuln | grep -q ":8000 "; then
    echo -e "${GREEN}✓ Port 8000 is listening${NC}"
else
    echo -e "${RED}✗ Port 8000 is not listening${NC}"
fi

# Test API endpoint
echo -n "Testing API health endpoint: "
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$API_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API responding (HTTP $API_RESPONSE)${NC}"
elif [ "$API_RESPONSE" = "000" ]; then
    echo -e "${RED}✗ API not reachable${NC}"
else
    echo -e "${YELLOW}⚠ API returned HTTP $API_RESPONSE${NC}"
fi

# 5. Check environment configuration
echo -e "\n${BLUE}5. Environment Configuration:${NC}"
if [ -f "/etc/orchestra.env" ]; then
    echo -e "${GREEN}✓ /etc/orchestra.env exists${NC}"
    echo -n "  Contains API keys: "
    if grep -q "API_KEY" /etc/orchestra.env; then
        echo "Yes"
    else
        echo -e "${YELLOW}No API keys found${NC}"
    fi
else
    echo -e "${RED}✗ /etc/orchestra.env not found${NC}"
fi

# 6. Check Python environment
echo -e "\n${BLUE}6. Python Environment:${NC}"
if [ -d "/root/orchestra-main/venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    source /root/orchestra-main/venv/bin/activate 2>/dev/null
    echo "  Python version: $(python --version 2>&1)"
    echo -n "  FastAPI installed: "
    if python -c "import fastapi" 2>/dev/null; then
        echo "Yes"
    else
        echo -e "${RED}No${NC}"
    fi
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
fi

# 7. Check recent logs
echo -e "\n${BLUE}7. Recent Error Logs:${NC}"

echo "Nginx errors (last 5):"
if [ -f "/var/log/nginx/error.log" ]; then
    tail -5 /var/log/nginx/error.log | sed 's/^/  /'
else
    echo "  No nginx error log found"
fi

echo -e "\nBackend service logs (if exists):"
if systemctl status orchestra-backend &>/dev/null; then
    journalctl -u orchestra-backend -n 5 --no-pager | sed 's/^/  /'
else
    echo "  Service not configured"
fi

# 8. Check SSL certificate
echo -e "\n${BLUE}8. SSL Certificate:${NC}"
if [ -f "/etc/letsencrypt/live/cherry-ai.me/fullchain.pem" ]; then
    echo -e "${GREEN}✓ SSL certificate exists${NC}"
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/cherry-ai.me/fullchain.pem | cut -d= -f2)
    echo "  Expires: $CERT_EXPIRY"
else
    echo -e "${YELLOW}⚠ SSL certificate not found at expected location${NC}"
fi

# 9. Check DNS resolution
echo -e "\n${BLUE}9. DNS Resolution:${NC}"
echo -n "cherry-ai.me resolves to: "
dig +short cherry-ai.me || echo "Failed to resolve"

# 10. Summary and recommendations
echo -e "\n${BLUE}========== SUMMARY ==========${NC}"
echo "Based on the diagnostics:"

ISSUES=()
if [ ! -f "/etc/nginx/sites-enabled/cherry-ai" ]; then
    ISSUES+=("Nginx not properly configured for cherry-ai.me")
fi

if ! pgrep -f "uvicorn.*agent.app.main" > /dev/null; then
    ISSUES+=("Backend API is not running")
fi

if [ ! -f "/etc/orchestra.env" ]; then
    ISSUES+=("Environment configuration missing")
fi

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ No major issues detected${NC}"
    echo "If you're still seeing the old site, it's likely a caching issue."
else
    echo -e "${RED}Issues found:${NC}"
    for issue in "${ISSUES[@]}"; do
        echo "  - $issue"
    done
fi

echo -e "\n${YELLOW}Recommended action:${NC}"
echo "Run: bash fix_cherry_deployment.sh"
echo "This will fix all identified issues automatically."
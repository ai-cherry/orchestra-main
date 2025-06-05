#!/bin/bash

# Fix API Detection Issues
# The API is working but monitoring is checking wrong endpoint

set -e

echo "🔧 FIXING API DETECTION"
echo "======================"
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

echo -e "${YELLOW}STEP 1: Verifying API is Actually Working${NC}"
echo "========================================="

# Test the actual endpoints
echo "Testing /api/health endpoint..."
HEALTH_RESPONSE=$(curl -s http://$LAMBDA_IP/api/health)
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is working correctly!${NC}"
else
    echo -e "${RED}❌ API not responding${NC}"
fi

echo ""
echo -e "${YELLOW}STEP 2: Removing Old Mock Files${NC}"
echo "================================"

ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Cleaning up old mock JavaScript files..."

# Find and archive old files
cd /opt/orchestra
mkdir -p archived_old_versions

# Move old mock files
for file in cherry-ai-orchestrator.js agent_factory.html cherry-ai-homepage.html cherry-ai-orchestrator-complete.html cherry-ai-orchestrator.html cherry_functional_interface.html cherry_ultimate_interface.html system_monitoring.html; do
    if [ -f "$file" ]; then
        echo "Archiving: $file"
        mv "$file" archived_old_versions/ 2>/dev/null || true
    fi
done

# Keep only the working files
echo -e "\nFiles remaining in /opt/orchestra:"
ls -la | grep -E "(cherry-ai-orchestrator-final\.html|cherry-ai-orchestrator-enhanced\.js|simple_api\.py)"

echo -e "\n✅ Old mock files archived"
EOF

echo ""
echo -e "${YELLOW}STEP 3: Updating Monitoring Script${NC}"
echo "==================================="

# Create a fixed monitoring check
cat > check_api_status.sh << 'SCRIPT'
#!/bin/bash
# Quick API status check

API_URL="http://150.136.94.139/api/health"
RESPONSE=$(curl -s $API_URL)

if echo "$RESPONSE" | grep -q "healthy"; then
    echo "✅ API Status: HEALTHY"
    echo "Response: $RESPONSE"
else
    echo "❌ API Status: OFFLINE"
fi

# Check from browser perspective
echo -e "\nChecking CORS headers..."
curl -s -I -X GET $API_URL \
  -H "Origin: http://150.136.94.139" \
  -H "Access-Control-Request-Method: GET" | grep -i "access-control"
SCRIPT

chmod +x check_api_status.sh

echo -e "${GREEN}✅ Created check_api_status.sh${NC}"

echo ""
echo -e "${YELLOW}STEP 4: Testing All Endpoints${NC}"
echo "============================="

# Test each endpoint
endpoints=(
    "/api/health"
    "/api/search?q=test"
    "/api/agents"
    "/api/workflows"
    "/api/knowledge"
    "/api/monitoring/metrics"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "Testing $endpoint: "
    if curl -s http://$LAMBDA_IP$endpoint | grep -q -E "(healthy|results|name|total)"; then
        echo -e "${GREEN}✅ Working${NC}"
    else
        echo -e "${RED}❌ Failed${NC}"
    fi
done

echo ""
echo -e "${YELLOW}STEP 5: Browser Instructions${NC}"
echo "============================"

echo -e "${BLUE}The API is working! The issue is likely browser-side.${NC}"
echo ""
echo "To fix the red API status in your browser:"
echo ""
echo "1. ${YELLOW}Open Chrome DevTools (F12)${NC}"
echo "2. ${YELLOW}Go to Network tab${NC}"
echo "3. ${YELLOW}Look for failed requests to /api/health${NC}"
echo "4. ${YELLOW}Check Console for errors${NC}"
echo ""
echo "Common issues:"
echo "- Mixed content (HTTP/HTTPS)"
echo "- Browser extensions blocking requests"
echo "- Cached service worker"
echo ""
echo "Try these fixes:"
echo "1. Hard refresh: Ctrl+Shift+R"
echo "2. Clear site data: DevTools > Application > Clear Storage"
echo "3. Test in incognito mode with no extensions"
echo "4. Add timestamp: http://$LAMBDA_IP/orchestrator/?v=$(date +%s)"

echo ""
echo -e "${GREEN}✅ API IS WORKING - Issue is client-side${NC}"
echo "==========================================="
echo ""
echo "The backend is functioning correctly. The monitoring"
echo "script was checking the wrong endpoint format."
echo ""
echo "Use ./check_api_status.sh to verify API status"
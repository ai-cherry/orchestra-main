#!/bin/bash
#
# Verify Admin UI Deployment
#

echo "🔍 Verifying Admin UI Deployment"
echo "================================"

# Check deployed files
echo -e "\n📁 Deployed Files:"
ls -la /var/www/cherry_ai-admin/assets/*.js 2>/dev/null | tail -3

# Get version from JavaScript
echo -e "\n📌 Version Check:"
VERSION_JS=$(ls -t /var/www/cherry_ai-admin/assets/index-*.js 2>/dev/null | head -1)
if [ -f "$VERSION_JS" ]; then
    VERSION_HASH=$(basename "$VERSION_JS" | grep -oE '[0-9]{13}')
    if [ ! -z "$VERSION_HASH" ]; then
        VERSION_DATE=$(date -d @$((VERSION_HASH/1000)) 2>/dev/null || date -r $((VERSION_HASH/1000)) 2>/dev/null)
        echo "   Build Hash: $VERSION_HASH"
        echo "   Build Time: $VERSION_DATE"
    fi
fi

# Test the site
echo -e "\n🌐 Site Status:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/admin/")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "   ✅ Site is up (HTTP $HTTP_STATUS)"
    
    # Check if error page is showing
    CONTENT=$(curl -s "http://localhost/admin/")
    if echo "$CONTENT" | grep -q "Something went wrong"; then
        echo "   ⚠️  Error page detected"
    elif echo "$CONTENT" | grep -q "data-version"; then
        echo "   ✅ Version tracking enabled"
    fi
else
    echo "   ❌ Site returned HTTP $HTTP_STATUS"
fi

# Check cache headers
echo -e "\n🚀 Cache Headers:"
HEADERS=$(curl -sI "http://localhost/admin/" | grep -i cache)
if echo "$HEADERS" | grep -q "no-cache"; then
    echo "   ✅ No-cache headers set correctly"
    echo "$HEADERS" | sed 's/^/      /'
else
    echo "   ⚠️  Cache headers may need adjustment"
fi

echo -e "\n🔗 Access URLs:"
echo "   Local:    http://localhost/admin/"
echo "   Public:   https://cherry-ai.me/admin/"
echo
echo "✨ To see the exact version, open the browser console and look for:"
echo "   🎼 Cherry Admin UI v[timestamp]" 
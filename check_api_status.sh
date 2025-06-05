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

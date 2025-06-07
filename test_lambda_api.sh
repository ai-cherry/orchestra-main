#!/bin/bash
# Test Lambda Labs API Connection

# Check for required environment variable
if [ -z "$LAMBDA_TOKEN" ]; then
    echo "Error: LAMBDA_TOKEN environment variable not set"
    echo "Export it with: export LAMBDA_TOKEN='your-api-key'"
    exit 1
fi

echo "🧪 Testing Lambda Labs API Connection"
echo "===================================="

# Test API connection
echo -e "\n1️⃣ Testing API authentication..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  https://cloud.lambdalabs.com/api/v1/instance-types)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API authentication successful!"
else
    echo "❌ API authentication failed (HTTP $HTTP_CODE)"
    echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
    exit 1
fi

# Show available instance types
echo -e "\n2️⃣ Available instance types with capacity:"
echo "$BODY" | jq -r '.data[] | select(.regions_with_capacity | length > 0) | "\(.name) - $\(.price_cents_per_hour/100)/hr - Regions: \(.regions_with_capacity | join(", "))"'

# Check existing instances
echo -e "\n3️⃣ Existing instances:"
INSTANCES=$(curl -s -X GET \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  https://cloud.lambdalabs.com/api/v1/instances)

if [ "$(echo "$INSTANCES" | jq -r '.data | length')" -gt 0 ]; then
    echo "$INSTANCES" | jq -r '.data[] | "• \(.name) (ID: \(.id)) - IP: \(.ip) - Status: \(.status)"'
else
    echo "No instances currently running"
fi

# Check SSH keys
echo -e "\n4️⃣ SSH keys:"
SSH_KEYS=$(curl -s -X GET \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  https://cloud.lambdalabs.com/api/v1/ssh-keys)

echo "$SSH_KEYS" | jq -r '.data[] | "• \(.name) (ID: \(.id))"'

echo -e "\n✅ API test complete!"
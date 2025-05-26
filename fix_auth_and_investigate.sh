#!/bin/bash

echo "=== Fixing Cloud Shell Authentication ==="
echo

# Step 1: Re-authenticate
echo "Step 1: Re-authenticating..."
gcloud auth login --no-launch-browser

# Step 2: Set the correct account and project
echo
echo "Step 2: Setting account and project..."
gcloud config set account scoobyjava@cherry-ai.me
gcloud config set project cherry-ai-project

# Step 3: Verify authentication
echo
echo "Step 3: Verifying authentication..."
gcloud auth list
echo
echo "Current project: $(gcloud config get-value project)"

# Step 4: Test authentication
echo
echo "Step 4: Testing authentication..."
if gcloud projects describe cherry-ai-project &>/dev/null; then
    echo "✅ Authentication successful!"
else
    echo "❌ Authentication failed. Please run: gcloud auth login"
    exit 1
fi

# Step 5: Check deployment status
echo
echo "=== Checking Deployment Status ==="

echo
echo "1. Recent builds:"
gcloud builds list --limit=3 --format="table(id,status,createTime.date(tz=LOCAL))"

echo
echo "2. Cloud Run services:"
gcloud run services list --region=us-central1 --format="table(metadata.name,status.url,status.conditions[0].status:label=READY)"

echo
echo "3. Testing ai-orchestra-minimal service:"
SERVICE_URL="https://ai-orchestra-minimal-yshgcxa7ta-uc.a.run.app"

# First try without auth
echo "   Testing without authentication..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health")
echo "   Response: HTTP $HTTP_CODE"

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ]; then
    echo
    echo "   Service requires authentication. Testing with auth token..."
    TOKEN=$(gcloud auth print-identity-token 2>/dev/null)
    if [ -n "$TOKEN" ]; then
        AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/health")
        echo "   Response with auth: HTTP $AUTH_CODE"
    else
        echo "   Could not generate auth token"
    fi
fi

echo
echo "=== Checking Service Configuration ==="
gcloud run services describe ai-orchestra-minimal --region=us-central1 --format="get(metadata.annotations)" | grep -E "(ingress|run.googleapis.com)"

echo
echo "=== Recent Logs ==="
echo "Checking for recent errors..."
gcloud logging read "resource.type=\"cloud_run_revision\" severity>=ERROR timestamp>=\"$(date -u -d '30 minutes ago' '+%Y-%m-%dT%H:%M:%S')Z\"" --limit=10 --format="table(timestamp.date(tz=LOCAL),resource.labels.service_name,jsonPayload.message)" || echo "No recent errors found"

echo
echo "=== Next Steps ==="
echo
echo "If you're getting 403/401 errors, you have two options:"
echo
echo "Option 1: Allow public access (if this is a public API):"
echo "  gcloud run services add-iam-policy-binding ai-orchestra-minimal \\"
echo "    --region=us-central1 \\"
echo "    --member=\"allUsers\" \\"
echo "    --role=\"roles/run.invoker\""
echo
echo "Option 2: Keep it private and use authentication:"
echo "  curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" \\"
echo "    $SERVICE_URL/health"
echo
echo "To view more logs:"
echo "  gcloud logging read \"resource.labels.service_name=\\\"ai-orchestra-minimal\\\"\" --limit=50"

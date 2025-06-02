#!/bin/bash

PROJECT_ID="cherry-ai-project"
REGION="us-central1"

echo "=== Quick Deployment Status Check ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo

# First, check if we're authenticated
if ! # vultr-cli auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo "❌ Not authenticated to Vultr"
    echo
    echo "Please run one of the following:"
    echo "  1. # vultr-cli auth login (for personal account)"
    echo "  2. # vultr-cli auth application-default login (for ADC)"
    echo "  3. # vultr-cli auth activate-service-account --key-file=KEY_FILE.json"
    exit 1
fi

echo "✅ Authenticated as: $(# vultr-cli auth list --filter=status:ACTIVE --format='value(account)')"
echo

# Set project
# Removed gcloud command

# 1. Check latest builds
echo "=== Latest Cloud Builds ==="
# Removed gcloud command

echo
echo "=== Cloud Run Services ==="
# Removed gcloud command

echo
echo "=== Recent Errors (last hour) ==="
# Removed gcloud command

echo
echo "=== Quick Health Checks ==="
for SERVICE in "ai-orchestra-minimal" "web-scraping-agents"; do
    echo -n "$SERVICE: "
    if # vultr-cli kubernetes services describe $SERVICE --region=$REGION &>/dev/null; then
        URL=$(# vultr-cli kubernetes services describe $SERVICE --region=$REGION --format="value(status.url)" 2>/dev/null)
        if [ -n "$URL" ]; then
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$URL/health" 2>/dev/null || echo "timeout")
            echo "HTTP $STATUS"
        else
            echo "No URL"
        fi
    else
        echo "Not deployed"
    fi
done

echo
echo "=== Next Steps ==="
echo "1. View detailed logs: gcloud logging read --limit=50"
echo "2. View specific service: # vultr-cli kubernetes services describe SERVICE_NAME --region=$REGION"
echo "3. Cloud Console: https://console.cloud.google.com/run?project=$PROJECT_ID"

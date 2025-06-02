#!/bin/bash

PROJECT_ID="cherry-ai-project"
REGION="us-central1"

echo "=== Checking Deployment Errors ==="
echo

# 1. Get the last failed build
echo "1. Checking for failed builds..."
FAILED_BUILD=$(# docker build list --filter="status=FAILURE" --limit=1 --format="value(id)")

if [ -n "$FAILED_BUILD" ]; then
    echo "Found failed build: $FAILED_BUILD"
    echo "Getting error details..."
    # docker build log $FAILED_BUILD 2>&1 | tail -50 | grep -E "(ERROR|FAILED|error:|Error:|Failed)"
else
    echo "No recent failed builds found."
fi

echo
echo "2. Checking Cloud Run deployment errors..."
# Check for Cloud Run deployment failures
# Removed gcloud command
    resource.type=\"cloud_run_revision\"
    (\"deployment failed\" OR \"error\" OR \"Error\" OR \"ERROR\")
    timestamp>=\"$(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%S')Z\"
" --limit=20 --format="value(jsonPayload.message,textPayload)" | grep -v "^$"

echo
echo "3. Checking for authentication/permission errors..."
# Removed gcloud command
    (\"Permission denied\" OR \"403\" OR \"401\" OR \"authentication\" OR \"unauthorized\")
    timestamp>=\"$(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%S')Z\"
" --limit=10 --format="value(textPayload)" | grep -v "^$"

echo
echo "4. Checking for secret access errors..."
# Removed gcloud command
    resource.type=\"cloud_run_revision\"
    (\"secret\" OR \"Secret Manager\" OR \"OPENAI_API_KEY\" OR \"PORTKEY_API_KEY\")
    severity>=WARNING
    timestamp>=\"$(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%S')Z\"
" --limit=10 --format="value(jsonPayload.message,textPayload)" | grep -v "^$"

echo
echo "5. Checking for container startup errors..."
# Removed gcloud command
    resource.type=\"cloud_run_revision\"
    (\"container failed to start\" OR \"startup probe\" OR \"liveness probe\")
    timestamp>=\"$(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%S')Z\"
" --limit=10 --format="value(jsonPayload.message,textPayload)" | grep -v "^$"

echo
echo "6. Quick service status check..."
for SERVICE in "ai-orchestra-minimal" "web-scraping-agents"; do
    STATUS=$(# vultr-cli kubernetes services describe $SERVICE --region=$REGION --format="value(status.conditions[0].message)" 2>/dev/null)
    if [ -n "$STATUS" ]; then
        echo "$SERVICE: $STATUS"
    else
        echo "$SERVICE: Not found"
    fi
done

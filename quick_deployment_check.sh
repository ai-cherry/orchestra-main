#!/bin/bash

PROJECT_ID="cherry-ai-project"
REGION="us-central1"

echo "=== Quick Deployment Status Check ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo

# First, check if we're authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo "❌ Not authenticated to Google Cloud"
    echo
    echo "Please run one of the following:"
    echo "  1. gcloud auth login (for personal account)"
    echo "  2. gcloud auth application-default login (for ADC)"
    echo "  3. gcloud auth activate-service-account --key-file=KEY_FILE.json"
    exit 1
fi

echo "✅ Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
echo

# Set project
gcloud config set project $PROJECT_ID --quiet

# 1. Check latest builds
echo "=== Latest Cloud Builds ==="
gcloud builds list --limit=3 --format="table(id,status,createTime.date(tz=LOCAL),duration(unit=MINUTE))" 2>&1 || echo "Unable to list builds"

echo
echo "=== Cloud Run Services ==="
gcloud run services list --region=$REGION --format="table(metadata.name,status.url,status.conditions[0].status:label=READY)" 2>&1 || echo "Unable to list services"

echo
echo "=== Recent Errors (last hour) ==="
gcloud logging read "severity>=ERROR timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')Z\"" --limit=5 --format="table(timestamp.date(tz=LOCAL),resource.type,jsonPayload.message)" 2>&1 | head -20 || echo "Unable to read logs"

echo
echo "=== Quick Health Checks ==="
for SERVICE in "ai-orchestra-minimal" "web-scraping-agents"; do
    echo -n "$SERVICE: "
    if gcloud run services describe $SERVICE --region=$REGION &>/dev/null; then
        URL=$(gcloud run services describe $SERVICE --region=$REGION --format="value(status.url)" 2>/dev/null)
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
echo "2. View specific service: gcloud run services describe SERVICE_NAME --region=$REGION"
echo "3. Cloud Console: https://console.cloud.google.com/run?project=$PROJECT_ID"

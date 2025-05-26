#!/bin/bash

PROJECT_ID="cherry-ai-project"
REGION="us-central1"

# Default service
SERVICE="${1:-ai-orchestra-minimal}"
LINES="${2:-50}"

echo "=== Cloud Run Service Logs ==="
echo "Service: $SERVICE"
echo "Region: $REGION"
echo "Lines: $LINES"
echo

# Check if service exists
if ! gcloud run services describe $SERVICE --region=$REGION &>/dev/null; then
    echo "Error: Service '$SERVICE' not found in region $REGION"
    echo
    echo "Available services:"
    gcloud run services list --region=$REGION --format="value(metadata.name)"
    exit 1
fi

echo "Fetching last $LINES log entries..."
echo "Press Ctrl+C to stop"
echo

# Get logs with follow option
gcloud run services logs read $SERVICE \
    --region=$REGION \
    --limit=$LINES \
    --format="table(
        timestamp.date(tz=LOCAL):sort=1,
        severity,
        jsonPayload.message:label='MESSAGE'
    )"

echo
echo "To follow logs in real-time, use:"
echo "gcloud alpha run services logs tail $SERVICE --region=$REGION"
echo
echo "To filter for errors only:"
echo "gcloud run services logs read $SERVICE --region=$REGION --filter='severity>=ERROR'"

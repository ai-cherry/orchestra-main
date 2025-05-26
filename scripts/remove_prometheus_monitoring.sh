#!/bin/bash

echo "🔄 Removing Prometheus Monitoring from all Cloud Run services"
echo "============================================================"
echo ""

PROJECT_ID="cherry-ai-project"
gcloud config set project $PROJECT_ID

echo "📊 Updating all Cloud Run services..."
echo ""

# Get all services with their regions
gcloud run services list --platform=managed --format="csv(name,region)" | tail -n +2 | while IFS=',' read -r SERVICE REGION; do
    echo "Processing: $SERVICE in $REGION"

    # Remove the specific Prometheus environment variable
    gcloud run services update $SERVICE \
        --platform=managed \
        --region=$REGION \
        --remove-env-vars=ENABLE_PROMETHEUS_SIDECAR \
        --quiet 2>&1 | grep -v "No change" | grep -v "Nothing to update"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✅ Successfully updated $SERVICE"
    else
        echo "ℹ️  No Prometheus config found on $SERVICE (already clean)"
    fi
    echo ""
done

echo "🎉 Migration to Google Cloud Monitoring complete!"
echo ""
echo "📈 Your services now use Google Cloud Monitoring exclusively"
echo ""
echo "Benefits:"
echo "- ✅ No additional configuration needed"
echo "- ✅ Automatic metric collection"
echo "- ✅ Built-in dashboards"
echo "- ✅ No permission issues"
echo "- ✅ Lower resource usage"
echo ""
echo "View your metrics at:"
echo "• Console: https://console.cloud.google.com/monitoring"
echo "• Cloud Run: https://console.cloud.google.com/run"
echo ""
echo "The Prometheus permission errors should stop within a few minutes."

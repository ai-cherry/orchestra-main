#!/bin/bash

echo "🔄 Switching to Google Cloud Monitoring"
echo "======================================="
echo ""

PROJECT_ID="cherry-ai-project"
REGION="us-central1"

# Set project
gcloud config set project $PROJECT_ID

echo "📊 Disabling Prometheus sidecar for all Cloud Run services..."
echo ""

# List of services from the diagnostic output
SERVICES=(
    "admin-interface-2d1751f"
    "ai-orchestra-minimal"
    "ai-orchestra-minimal-4334680"
    "mcp-server"
    "orchestra-api"
    "web-scraping-agents-b4ed07b"
)

for SERVICE in "${SERVICES[@]}"; do
    echo "Processing: $SERVICE"
    
    # Update the service to remove Prometheus sidecar
    gcloud run services update $SERVICE \
        --platform=managed \
        --region=$REGION \
        --clear-env-vars=ENABLE_PROMETHEUS_SIDECAR \
        --quiet 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully disabled Prometheus for $SERVICE"
    else
        echo "⚠️  Service $SERVICE might not exist or couldn't be updated"
    fi
    echo ""
done

echo "🎉 Migration to Google Cloud Monitoring complete!"
echo ""
echo "📈 View metrics at: https://console.cloud.google.com/monitoring"
echo ""
echo "Benefits of Google Cloud Monitoring:"
echo "- ✅ No additional configuration needed"
echo "- ✅ Automatic metric collection for Cloud Run"
echo "- ✅ Built-in dashboards and alerts"
echo "- ✅ No permission issues"
echo "- ✅ Lower resource usage"
echo ""
echo "To view your Cloud Run metrics:"
echo "1. Go to: https://console.cloud.google.com/run"
echo "2. Click on any service"
echo "3. Navigate to the 'Metrics' tab" 
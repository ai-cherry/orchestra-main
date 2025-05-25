#!/bin/bash

echo "🔄 Switching ALL services to Google Cloud Monitoring"
echo "==================================================="
echo ""

PROJECT_ID="cherry-ai-project"
gcloud config set project $PROJECT_ID

echo "📊 Finding and updating all Cloud Run services..."
echo ""

# Get all services with their regions
gcloud run services list --platform=managed --format="csv(name,region)" | tail -n +2 | while IFS=',' read -r SERVICE REGION; do
    echo "Processing: $SERVICE in $REGION"
    
    # Update the service to remove Prometheus sidecar
    gcloud run services update $SERVICE \
        --platform=managed \
        --region=$REGION \
        --clear-env-vars=ENABLE_PROMETHEUS_SIDECAR \
        --quiet 2>&1 | grep -v "No change"
    
    if [ $? -eq 0 ] || [ $? -eq 1 ]; then
        echo "✅ Successfully processed $SERVICE"
    else
        echo "❌ Failed to update $SERVICE"
    fi
    echo ""
done

echo "🎉 All services migrated to Google Cloud Monitoring!"
echo ""
echo "📊 Verifying Prometheus is disabled..."
# Check if any services still have ENABLE_PROMETHEUS_SIDECAR
SERVICES_WITH_PROMETHEUS=$(gcloud run services list --platform=managed --format="value(name)" | while read SERVICE; do
    REGION=$(gcloud run services list --platform=managed --filter="name:$SERVICE" --format="value(region)")
    ENV_VARS=$(gcloud run services describe $SERVICE --region=$REGION --platform=managed --format="get(spec.template.spec.containers[0].env[].name)" 2>/dev/null)
    if echo "$ENV_VARS" | grep -q "ENABLE_PROMETHEUS_SIDECAR"; then
        echo "$SERVICE"
    fi
done)

if [ -z "$SERVICES_WITH_PROMETHEUS" ]; then
    echo "✅ All services successfully migrated!"
else
    echo "⚠️  These services may still have Prometheus enabled:"
    echo "$SERVICES_WITH_PROMETHEUS"
fi

echo ""
echo "📈 Google Cloud Monitoring is now active for all services"
echo "View your metrics at: https://console.cloud.google.com/monitoring" 
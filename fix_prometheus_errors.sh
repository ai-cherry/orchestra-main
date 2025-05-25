#!/bin/bash

echo "🔧 Fixing Prometheus Metrics Collection Errors"
echo "============================================="
echo ""

PROJECT_ID="cherry-ai-project"
gcloud config set project $PROJECT_ID

echo "1️⃣ Identifying Service Accounts:"
echo "--------------------------------"
# List all service accounts
gcloud iam service-accounts list --format="table(email,displayName)"
echo ""

echo "2️⃣ Checking Prometheus/Metrics Collector Service Account:"
echo "--------------------------------------------------------"
METRICS_SA="prometheus-metrics-collector@$PROJECT_ID.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $METRICS_SA 2>/dev/null; then
    echo "✅ Metrics collector service account exists"
    echo ""
    echo "Current roles:"
    gcloud projects get-iam-policy $PROJECT_ID \
        --flatten="bindings[].members" \
        --filter="bindings.members:$METRICS_SA" \
        --format="table(bindings.role)"
else
    echo "❌ Metrics collector service account not found"
    echo "Creating it..."
    gcloud iam service-accounts create prometheus-metrics-collector \
        --display-name="Prometheus Metrics Collector" \
        --description="Service account for collecting metrics from GCP services"
fi
echo ""

echo "3️⃣ Granting Required Permissions:"
echo "---------------------------------"
echo "Adding monitoring permissions..."

# Grant necessary roles for metrics collection
ROLES=(
    "roles/monitoring.metricWriter"
    "roles/monitoring.viewer"
    "roles/cloudtrace.agent"
    "roles/logging.logWriter"
)

for ROLE in "${ROLES[@]}"; do
    echo "Granting $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$METRICS_SA" \
        --role="$ROLE" \
        --quiet
done
echo ""

echo "4️⃣ Fixing Cloud Run Service Permissions:"
echo "----------------------------------------"
# Get all Cloud Run services
SERVICES=$(gcloud run services list --platform=managed --format="value(name)")

for SERVICE in $SERVICES; do
    echo "Checking service: $SERVICE"
    
    # Get the service account used by this service
    SERVICE_SA=$(gcloud run services describe $SERVICE \
        --platform=managed \
        --region=us-central1 \
        --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null)
    
    if [ -n "$SERVICE_SA" ]; then
        echo "  Service account: $SERVICE_SA"
        
        # Grant metrics writing permission to the service's SA
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_SA" \
            --role="roles/monitoring.metricWriter" \
            --quiet 2>/dev/null
    fi
done
echo ""

echo "5️⃣ Disabling Prometheus Sidecar (if not needed):"
echo "-----------------------------------------------"
echo "If you don't need Prometheus metrics collection, you can disable it:"
echo ""
echo "For each Cloud Run service, run:"
echo "gcloud run services update SERVICE_NAME \\"
echo "    --platform=managed \\"
echo "    --region=us-central1 \\"
echo "    --clear-env-vars=ENABLE_PROMETHEUS_SIDECAR"
echo ""

echo "6️⃣ Alternative: Using Google Cloud Monitoring:"
echo "----------------------------------------------"
echo "Consider using native Google Cloud Monitoring instead of Prometheus:"
echo "- It's already integrated with Cloud Run"
echo "- No additional permissions needed"
echo "- Access metrics at: https://console.cloud.google.com/monitoring"
echo ""

echo "✅ Permissions have been updated. The errors should stop appearing in logs within a few minutes." 
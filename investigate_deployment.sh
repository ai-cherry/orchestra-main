#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ID="cherry-ai-project"
REGION="us-central1"

echo -e "${BLUE}=== Google Cloud Deployment Investigation ===${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Timestamp: $(date)"
echo

# Set the project
gcloud config set project $PROJECT_ID 2>/dev/null

# Function to print section headers
print_section() {
    echo
    echo -e "${YELLOW}=== $1 ===${NC}"
}

# 1. Check Cloud Build History
print_section "Recent Cloud Build History"
echo "Last 5 builds:"
gcloud builds list --limit=5 --format="table(
    id,
    createTime.date(tz=LOCAL),
    duration(unit=MINUTE),
    status,
    substitutions.COMMIT_SHA:label='COMMIT'
)"

# Get the last build ID
LAST_BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)")
if [ -n "$LAST_BUILD_ID" ]; then
    echo
    echo "Last build details (ID: $LAST_BUILD_ID):"
    gcloud builds describe $LAST_BUILD_ID --format="yaml(status,logUrl,timing)"
fi

# 2. Check Cloud Run Services
print_section "Cloud Run Services Status"
gcloud run services list --platform=managed --region=$REGION --format="table(
    metadata.name:label='SERVICE',
    status.url:label='URL',
    status.conditions[0].type:label='STATUS',
    status.conditions[0].status:label='READY',
    metadata.annotations.'serving.knative.dev/lastModifier':label='LAST_MODIFIED_BY'
)"

# 3. Check specific services health
print_section "Service Health Checks"
SERVICES=("ai-orchestra-minimal" "web-scraping-agents")

for SERVICE in "${SERVICES[@]}"; do
    echo
    echo "Checking $SERVICE..."

    # Get service details
    SERVICE_EXISTS=$(gcloud run services describe $SERVICE --region=$REGION --format="value(metadata.name)" 2>/dev/null)

    if [ -n "$SERVICE_EXISTS" ]; then
        # Get service URL
        SERVICE_URL=$(gcloud run services describe $SERVICE --region=$REGION --format="value(status.url)" 2>/dev/null)

        # Get latest revision
        LATEST_REVISION=$(gcloud run services describe $SERVICE --region=$REGION --format="value(status.latestReadyRevisionName)" 2>/dev/null)

        echo "  URL: $SERVICE_URL"
        echo "  Latest Revision: $LATEST_REVISION"

        # Try health check
        if [ -n "$SERVICE_URL" ]; then
            echo -n "  Health Check: "
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$SERVICE_URL/health" 2>/dev/null)
            if [ "$HTTP_CODE" = "200" ]; then
                echo -e "${GREEN}✓ Healthy (HTTP $HTTP_CODE)${NC}"
            else
                echo -e "${RED}✗ Unhealthy (HTTP $HTTP_CODE)${NC}"
            fi
        fi
    else
        echo -e "  ${RED}✗ Service not found${NC}"
    fi
done

# 4. Check recent logs for errors
print_section "Recent Error Logs (Last 30 minutes)"
echo "Checking for errors in Cloud Run logs..."

# Cloud Run error logs
gcloud logging read "
    resource.type=\"cloud_run_revision\"
    severity>=ERROR
    timestamp>=\"$(date -u -d '30 minutes ago' '+%Y-%m-%dT%H:%M:%S')Z\"
" --limit=20 --format="table(
    timestamp.date(tz=LOCAL),
    resource.labels.service_name,
    jsonPayload.message:label='MESSAGE'
)" 2>/dev/null || echo "No error logs found in the last 30 minutes"

# 5. Check deployment-related logs
print_section "Recent Deployment Logs"
echo "GitHub Actions deployment logs (if using Cloud Build triggers):"

gcloud logging read "
    resource.type=\"build\"
    timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')Z\"
    \"github\"
" --limit=10 --format="table(
    timestamp.date(tz=LOCAL),
    textPayload
)" 2>/dev/null || echo "No GitHub-related build logs found"

# 6. Check resource quotas
print_section "Resource Quotas"
echo "Checking if any quotas are exceeded..."
gcloud compute project-info describe --format="table(
    quotas[].metric.list():label='METRIC',
    quotas[].limit.list():label='LIMIT',
    quotas[].usage.list():label='USAGE'
)" 2>/dev/null | grep -E "(CPUS|MEMORY|DISKS)" | head -10

# 7. Check recent container image builds
print_section "Recent Container Images"
echo "Last 5 container images in Artifact Registry:"
gcloud artifacts docker images list us-central1-docker.pkg.dev/$PROJECT_ID/orchestra-repo --limit=5 --format="table(
    package,
    tags.list():label='TAGS',
    createTime.date(tz=LOCAL),
    metadata.buildDetails.buildTriggerName:label='TRIGGER'
)" 2>/dev/null || echo "No images found in Artifact Registry"

# 8. Summary and recommendations
print_section "Summary & Next Steps"
echo "1. Check the Cloud Build logs for detailed error messages:"
echo "   ${BLUE}gcloud builds log $LAST_BUILD_ID${NC}"
echo
echo "2. View real-time logs for a specific service:"
echo "   ${BLUE}gcloud run services logs read ai-orchestra-minimal --region=$REGION${NC}"
echo
echo "3. Check the Cloud Console for more details:"
echo "   ${BLUE}https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID${NC}"
echo
echo "4. View Cloud Run services in console:"
echo "   ${BLUE}https://console.cloud.google.com/run?project=$PROJECT_ID${NC}"

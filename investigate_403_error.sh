#!/bin/bash

SERVICE="ai-orchestra-minimal"
REGION="us-central1"

echo "=== Investigating 403 Error for $SERVICE ==="
echo

# Get service details
echo "1. Service Details:"
gcloud run services describe $SERVICE --region=$REGION --format=yaml | grep -E "(ingress:|service:|url:|latestReadyRevisionName:|observedGeneration:)" || echo "Failed to get service details"

echo
echo "2. Service IAM Policy:"
gcloud run services get-iam-policy $SERVICE --region=$REGION || echo "Failed to get IAM policy"

echo
echo "3. Checking if service allows unauthenticated access:"
ALLOW_UNAUTH=$(gcloud run services describe $SERVICE --region=$REGION --format="value(metadata.annotations.'run.googleapis.com/ingress')" 2>/dev/null)
echo "Ingress setting: ${ALLOW_UNAUTH:-not set}"

echo
echo "4. Recent logs from the service:"
gcloud logging read "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE\" timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')Z\"" --limit=20 --format="table(timestamp.date(tz=LOCAL),severity,jsonPayload.message)" 2>/dev/null | head -30 || echo "No recent logs found"

echo
echo "5. Checking for authentication/authorization errors:"
gcloud logging read "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE\" (\"403\" OR \"Forbidden\" OR \"unauthorized\") timestamp>=\"$(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%S')Z\"" --limit=10 --format="value(jsonPayload.message,textPayload)" 2>/dev/null | grep -v "^$" || echo "No auth errors found"

echo
echo "=== Solutions for 403 Error ==="
echo
echo "Option 1: Allow unauthenticated access (for public APIs):"
echo "  gcloud run services add-iam-policy-binding $SERVICE \\"
echo "    --region=$REGION \\"
echo "    --member=\"allUsers\" \\"
echo "    --role=\"roles/run.invoker\""
echo
echo "Option 2: Test with authentication:"
echo "  curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" \\"
echo "    https://ai-orchestra-minimal-yshgcxa7ta-uc.a.run.app/health"
echo
echo "Option 3: Check if the service expects API keys:"
echo "  The service might be returning 403 if required API keys are missing"

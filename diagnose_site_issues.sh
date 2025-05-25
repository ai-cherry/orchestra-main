#!/bin/bash

echo "🔍 Cherry AI Site Diagnostics"
echo "============================"
echo ""

# Set project
PROJECT_ID="cherry-ai-project"
gcloud config set project $PROJECT_ID

echo "1️⃣ Checking Load Balancer and IP Addresses:"
echo "----------------------------------------"
gcloud compute addresses list --format="table(name,address,status,users.scope():label=USED_BY)"
echo ""

echo "2️⃣ Checking SSL Certificates:"
echo "-----------------------------"
gcloud compute ssl-certificates list --format="table(name,type,domains[0],managed.status,creationTimestamp)"
echo ""

echo "3️⃣ Checking URL Maps and Forwarding Rules:"
echo "----------------------------------------"
gcloud compute url-maps list --format="table(name,defaultService.scope():label=DEFAULT_SERVICE)"
echo ""
gcloud compute forwarding-rules list --global --format="table(name,IPAddress,target.scope():label=TARGET)"
echo ""

echo "4️⃣ Checking Backend Buckets:"
echo "----------------------------"
gcloud compute backend-buckets list --format="table(name,bucketName,enableCdn)"
echo ""

echo "5️⃣ Checking GCS Bucket Contents:"
echo "--------------------------------"
BUCKET_NAME="admin-ui-site-prod"
echo "Bucket: gs://$BUCKET_NAME"
gsutil ls -l gs://$BUCKET_NAME/ | head -20
echo ""

echo "6️⃣ Checking Cloud Run Services:"
echo "-------------------------------"
gcloud run services list --platform=managed --format="table(name,status.url,status.conditions[0].type,status.conditions[0].status)"
echo ""

echo "7️⃣ Checking DNS Records (if using Cloud DNS):"
echo "--------------------------------------------"
gcloud dns managed-zones list --format="table(name,dnsName,visibility)"
echo ""

echo "8️⃣ Testing Site Accessibility:"
echo "------------------------------"
# Test the load balancer IP directly
LB_IP=$(gcloud compute addresses describe admin-ui-site-lb-ip --global --format="value(address)" 2>/dev/null || echo "NOT_FOUND")
if [ "$LB_IP" != "NOT_FOUND" ]; then
    echo "Load Balancer IP: $LB_IP"
    echo "Testing HTTP response:"
    curl -I -s -m 5 http://$LB_IP | head -5
    echo ""
    echo "Testing HTTPS response:"
    curl -I -s -m 5 https://$LB_IP | head -5
else
    echo "❌ Load balancer IP not found!"
fi
echo ""

echo "9️⃣ Checking IAM Permissions:"
echo "----------------------------"
echo "Service accounts with roles:"
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.members,bindings.role)" | grep serviceAccount | head -20
echo ""

echo "🔟 Recent Error Summary:"
echo "----------------------"
echo "Checking for recent errors in logs..."
gcloud logging read "severity=ERROR AND timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')\"" --limit=10 --format="table(timestamp,resource.type,textPayload)" 2>/dev/null || echo "No recent errors found" 
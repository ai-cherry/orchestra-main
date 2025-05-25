#!/bin/bash

echo "🎨 Admin UI Deployment Check"
echo "==========================="
echo ""

PROJECT_ID="cherry-ai-project"
gcloud config set project $PROJECT_ID

echo "1️⃣ Checking Pulumi Stack Status:"
echo "--------------------------------"
cd infra/admin_ui_site 2>/dev/null
if [ -d ".pulumi" ]; then
    echo "Pulumi project found. Current stack:"
    pulumi stack ls 2>/dev/null || echo "Unable to list stacks"
    echo ""
    echo "Stack outputs:"
    pulumi stack output 2>/dev/null || echo "Unable to get outputs"
else
    echo "❌ No Pulumi project found in infra/admin_ui_site"
fi
cd - > /dev/null
echo ""

echo "2️⃣ Checking GCS Bucket:"
echo "----------------------"
BUCKET_NAME="admin-ui-site-prod"
echo "Bucket: gs://$BUCKET_NAME"
echo "Checking if bucket exists:"
gsutil ls gs://$BUCKET_NAME 2>&1 | head -5
echo ""
echo "Checking bucket permissions:"
gsutil iam get gs://$BUCKET_NAME 2>/dev/null | grep -A5 "allUsers" || echo "No public access configured"
echo ""

echo "3️⃣ Checking Load Balancer Configuration:"
echo "---------------------------------------"
# Find the backend bucket
BACKEND_BUCKET=$(gcloud compute backend-buckets list --filter="bucketName:$BUCKET_NAME" --format="value(name)" 2>/dev/null)
if [ -n "$BACKEND_BUCKET" ]; then
    echo "Backend bucket: $BACKEND_BUCKET"
    gcloud compute backend-buckets describe $BACKEND_BUCKET --format="yaml(bucketName,enableCdn,cdnPolicy)"
else
    echo "❌ No backend bucket found for $BUCKET_NAME"
fi
echo ""

echo "4️⃣ Checking HTTPS Configuration:"
echo "--------------------------------"
# Find URL maps using this backend
URL_MAP=$(gcloud compute url-maps list --format="value(name)" --filter="defaultService:$BACKEND_BUCKET" 2>/dev/null | head -1)
if [ -n "$URL_MAP" ]; then
    echo "URL Map: $URL_MAP"
    # Find target HTTPS proxy
    HTTPS_PROXY=$(gcloud compute target-https-proxies list --format="value(name)" --filter="urlMap:$URL_MAP" 2>/dev/null | head -1)
    if [ -n "$HTTPS_PROXY" ]; then
        echo "HTTPS Proxy: $HTTPS_PROXY"
        gcloud compute target-https-proxies describe $HTTPS_PROXY --format="yaml(sslCertificates,urlMap)"
    fi
fi
echo ""

echo "5️⃣ Checking GitHub Actions Deployment:"
echo "-------------------------------------"
echo "Recent workflow runs (if accessible):"
gh workflow view admin-ui.yml 2>/dev/null || echo "GitHub CLI not configured or workflow not found"
echo ""

echo "6️⃣ Quick Deployment Fix Commands:"
echo "---------------------------------"
echo "If the infrastructure is missing, run these commands in Google Cloud Shell:"
echo ""
echo "# 1. Clone the repository"
echo "git clone https://github.com/yourusername/orchestra-main.git"
echo "cd orchestra-main"
echo ""
echo "# 2. Set up Pulumi"
echo "export PULUMI_CONFIG_PASSPHRASE=your-passphrase"
echo "cd infra/admin_ui_site"
echo "pulumi stack select prod"
echo ""
echo "# 3. Deploy infrastructure"
echo "pulumi up -y"
echo ""
echo "# 4. Build and deploy the admin UI"
echo "cd ../../admin-interface"
echo "npm install && npm run build"
echo "gsutil -m rsync -r -d dist/ gs://admin-ui-site-prod/"
echo "" 
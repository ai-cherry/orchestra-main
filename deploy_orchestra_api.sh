#!/bin/bash
# deploy_orchestra_api.sh
# Canonical, simple, and stable deployment script for Orchestra API on GCP
# - Builds Docker image using Google Cloud Build (no local Docker needed)
# - Pushes to Artifact Registry
# - Deploys to Cloud Run
# - Ensures Redis is present
# - Prints a checklist for ongoing evaluation

set -e

# Configurable variables
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
SERVICE_NAME="orchestra-api"
IMAGE_NAME="orchestra-api"
ARTIFACT_REPO="ai-orchestra"
REDIS_INSTANCE="orchestra-redis"
REDIS_REGION="us-central1"
REDIS_TIER="BASIC"
REDIS_SIZE_GB=1

# 1. Authenticate with GCP (assumes gcloud is already authenticated)
echo "Authenticating with GCP..."
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
gcloud config set artifacts/location "$REGION"

# 2. Ensure requirements.txt is present in build context
echo "Copying requirements/base.txt to orchestra_api/requirements.txt..."
cp requirements/base.txt orchestra_api/requirements.txt

# 3. Build and push Docker image using Google Cloud Build
IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$IMAGE_NAME:latest"
echo "Building and pushing Docker image with Google Cloud Build..."
gcloud builds submit ./orchestra_api --tag "$IMAGE_URI"

# 4. Deploy to Cloud Run using the pushed image
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_URI" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300

# 5. Ensure Redis instance exists (create if missing)
echo "Checking for Redis instance..."
if ! gcloud redis instances describe "$REDIS_INSTANCE" --region="$REDIS_REGION" >/dev/null 2>&1; then
  echo "Redis instance not found. Creating..."
  gcloud redis instances create "$REDIS_INSTANCE" \
    --size="$REDIS_SIZE_GB" \
    --region="$REDIS_REGION" \
    --tier="$REDIS_TIER"
else
  echo "Redis instance '$REDIS_INSTANCE' already exists."
fi

# 6. Print checklist for ongoing evaluation
cat <<EOF

==========================
DEPLOYMENT COMPLETE

Checklist for Ongoing Evaluation:
- [ ] Confirm Cloud Run service '$SERVICE_NAME' is running and healthy.
- [ ] Confirm Redis instance '$REDIS_INSTANCE' is available in region '$REDIS_REGION'.
- [ ] Confirm secrets are synced via Secret Manager.
- [ ] Run 'gcp_environment_audit.sh' after major changes.
- [ ] Monitor logs and metrics in GCP Console.
- [ ] Update this script and documentation as needed.

This workflow is 100% GCP-native: Google Cloud Build → Artifact Registry → Cloud Run. No local Docker, no Docker Cloud, no Docker Hub. Maximum stability and simplicity.
==========================

EOF

#!/bin/bash
# Deploy to Cloud Run script

set -e

# Configuration
export PROJECT_ID="cherry-ai.me"
export PROJECT_NUMBER="525398941159"
export REGION="us-central1"
export SERVICE_ACCOUNT="vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"
export REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/orchestra"

# Build and push the Docker image
echo "Building and pushing Docker image..."
docker build -t "${REGISTRY}/api:latest" .
docker push "${REGISTRY}/api:latest"

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy orchestra \
  --image="${REGISTRY}/api:latest" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="${SERVICE_ACCOUNT}" \
  --project="${PROJECT_ID}" \
  --allow-unauthenticated

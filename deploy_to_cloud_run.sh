#!/bin/bash
# Deploy to Google Cloud Run

set -e

# Validate required environment variables
if [ -z "$GCP_PROJECT_ID" ] || [ -z "$SERVICE_NAME" ]; then
    echo "Error: GCP_PROJECT_ID and SERVICE_NAME must be set."
    exit 1
fi

# Deploy the service
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

echo "Deployment to Cloud Run completed successfully."

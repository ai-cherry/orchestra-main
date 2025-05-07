#!/bin/bash

# Deployment Script for Phidata Agent to Cloud Run
# Project: orchestra-main
# Target Project ID: agi-baby-cherry
# Region: us-central1

echo "Starting deployment process for Phidata Agent to Cloud Run..."

# Step 1: Authenticate with Google Cloud SDK
echo "Authenticating with Google Cloud SDK..."
gcloud auth login
gcloud config set project agi-baby-cherry

# Step 2: Build Docker Image for Phidata Agent
echo "Building Docker image for Phidata Agent..."
# Navigate to the directory containing the Dockerfile
cd packages/agents
# Build the Docker image
docker build -f phidata-agent.Dockerfile -t us-docker.pkg.dev/agi-baby-cherry/phidata/agent:latest .
# Push the image to Google Container Registry
docker push us-docker.pkg.dev/agi-baby-cherry/phidata/agent:latest

# Step 3: Deploy to Cloud Run
echo "Deploying Phidata Agent to Cloud Run..."
gcloud run deploy phidata-agent \
  --image=us-docker.pkg.dev/agi-baby-cherry/phidata/agent:latest \
  --service-account=vertex-agent@agi-baby-cherry.iam.gserviceaccount.com \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=agi-baby-cherry" \
  --memory=512Mi \
  --cpu=1

echo "Deployment to Cloud Run completed. Phidata Agent is now running at the assigned URL."
echo "Check Cloud Run console for the service URL and logs."
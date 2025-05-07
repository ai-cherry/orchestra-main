#!/bin/bash

# Deployment Script for Phidata Agent to Cloud Run
# Project: orchestra-main
# Target Project ID: cherry-ai-project
# Region: us-west4

echo "Starting deployment process for Phidata Agent to Cloud Run..."

# Step 1: Authenticate with Google Cloud SDK
echo "Authenticating with Google Cloud SDK..."
gcloud auth login
gcloud config set project cherry-ai-project

# Step 2: Build Docker Image for Phidata Agent
echo "Building Docker image for Phidata Agent..."
# Navigate to the directory containing the Dockerfile
cd packages/agents
# Build the Docker image
docker build -f phidata-agent.Dockerfile -t us-docker.pkg.dev/cherry-ai-project/phidata/agent:latest .
# Push the image to Google Container Registry
docker push us-docker.pkg.dev/cherry-ai-project/phidata/agent:latest

# Step 3: Deploy to Cloud Run
echo "Deploying Phidata Agent to Cloud Run..."
gcloud run deploy phidata-agent \
  --image=us-docker.pkg.dev/cherry-ai-project/phidata/agent:latest \
  --service-account=vertex-agent@cherry-ai-project.iam.gserviceaccount.com \
  --region=us-west4 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=cherry-ai-project" \
  --memory=512Mi \
  --cpu=1

echo "Deployment to Cloud Run completed. Phidata Agent is now running at the assigned URL."
echo "Check Cloud Run console for the service URL and logs."
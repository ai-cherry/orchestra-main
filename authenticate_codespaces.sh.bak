#!/bin/bash
# GitHub Codespaces authentication script for GCP

set -e

# Configuration
export PROJECT_ID="cherry-ai.me"
export PROJECT_NUMBER="525398941159"
export REGION="us-central1"
export SERVICE_ACCOUNT="vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"

# Authenticate with GCP
echo "Authenticating with GCP..."
gcloud auth login

# Configure Docker for Artifact Registry
echo "Configuring Docker authentication..."
gcloud auth configure-docker us-central1-docker.pkg.dev

# Set default project
echo "Setting default project..."
gcloud config set project ${PROJECT_ID}

# Set default region
echo "Setting default region..."
gcloud config set compute/region ${REGION}

# Verify authentication
echo "Verifying authentication..."
gcloud auth list
gcloud config list

# Test access to Artifact Registry
echo "Testing Artifact Registry access..."
gcloud artifacts repositories list --project=${PROJECT_ID} --location=${REGION}

echo "Authentication complete!"

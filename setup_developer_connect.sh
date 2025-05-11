#!/bin/bash

# Setup Developer Connect for Gemini Code Assist
# This script registers the current repository with Developer Connect

echo "Setting up Developer Connect for repository integration..."

# Set project variables
PROJECT_ID=cherry-ai-project
REGION=us-central1
REPO_NAME=orchestra-main
GITHUB_USER=$(git config user.name || echo "developer")

# Authenticate with gcloud if needed
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q @ ; then
  echo "Not authenticated with gcloud. Please run 'gcloud auth login' first."
  exit 1
fi

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID
gcloud services enable developerconnect.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudaicompanion.googleapis.com --project=$PROJECT_ID

# Register the repository with Developer Connect
echo "Registering repository with Developer Connect..."
gcloud alpha developer-connect repos register github_$REPO_NAME \
  --gitlab-host-uri="https://github.com" \
  --project=$PROJECT_ID \
  --region=$REGION

# Enable Gemini Code Assist for the repository
echo "Enabling Gemini Code Assist for the repository..."
gcloud alpha genai code customize enable \
  --project=$PROJECT_ID \
  --region=$REGION \
  --repos=github_$REPO_NAME

echo "Developer Connect setup complete. Gemini Code Assist should now have access to your repository."
echo ""
echo "To verify the setup, run:"
echo "gcloud alpha genai code customize list --project=$PROJECT_ID --region=$REGION"

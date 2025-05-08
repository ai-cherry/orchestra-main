#!/bin/bash
# direct_auth.sh - Simplified GCP authentication

set -e  # Exit on error

# Set environment variables
export PROJECT_ID="cherry-ai-project"
export REGION="us-west4"

# Define cleanup function
cleanup() {
  if [ -f "master-sa.json" ]; then
    rm -f master-sa.json
    echo "🧹 Cleaned up temporary files"
  fi
}

# Register cleanup on exit
trap cleanup EXIT

# Basic validation
if [[ ! "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]]; then
  echo "❌ Invalid project ID format"
  exit 1
fi

# Create service account key file from environment variable
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
  # Use more secure temporary file handling
  TEMP_KEY_FILE=$(mktemp)
  chmod 600 "$TEMP_KEY_FILE"
  echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_KEY_FILE"
  export GOOGLE_APPLICATION_CREDENTIALS="$TEMP_KEY_FILE"
  
  # Authenticate with gcloud
  echo "🔑 Authenticating with GCP..."
  if ! gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"; then
    echo "❌ Authentication failed"
    exit 1
  fi
  
  gcloud config set project "$PROJECT_ID"
  gcloud config set compute/region "$REGION"
  
  echo "✅ Authentication successful with master service account"
else
  echo "❌ GCP_MASTER_SERVICE_JSON environment variable not set"
  exit 1
fi

# Enable required APIs in one command
echo "🔌 Enabling required APIs..."
if ! gcloud services enable compute.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  vpcaccess.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com; then
  
  echo "❌ Failed to enable some APIs. Check permissions and try again."
  exit 1
fi

echo "✅ All required APIs enabled"
echo "🚀 GCP environment ready for use"
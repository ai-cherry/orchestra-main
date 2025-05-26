#!/bin/bash

echo "=== Fixing Google Cloud Authentication ==="
echo

# Check current configuration
echo "Current configuration:"
gcloud config list
echo

# Option 1: Use your personal account (recommended for Cloud Shell)
echo "Option 1: Authenticate with your Google account"
echo "Run: gcloud auth login"
echo

# Option 2: Use Application Default Credentials (for Cloud Shell)
echo "Option 2: Use Application Default Credentials"
echo "Run: gcloud auth application-default login"
echo

# Option 3: Use a service account key file
echo "Option 3: Use a service account key file"
echo "If you have a service account key file (.json), run:"
echo "gcloud auth activate-service-account --key-file=/path/to/key.json"
echo

# For Cloud Shell, usually the best approach is:
echo "=== Recommended for Cloud Shell ==="
echo "1. First, login with your Google account:"
echo "   gcloud auth login"
echo
echo "2. Set the project:"
echo "   gcloud config set project cherry-ai-project"
echo
echo "3. Verify authentication:"
echo "   gcloud auth list"
echo

# Quick fix attempt
echo "=== Attempting Quick Fix ==="
# In Cloud Shell, we should already be authenticated
if [ "$CLOUD_SHELL" = "true" ]; then
    echo "Detected Cloud Shell environment"
    echo "Setting project..."
    gcloud config set project cherry-ai-project

    echo "Current auth status:"
    gcloud auth list

    echo
    echo "If you see no active account, run: gcloud auth login"
else
    echo "Not in Cloud Shell. Please authenticate manually."
fi

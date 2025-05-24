#!/bin/bash

# Entrypoint script for Phidata Agent on Cloud Run
# This script initializes the environment, fetches API keys from GCP Secret Manager,
# and starts the Phidata agent service.

echo "Starting Phidata Agent initialization on Cloud Run..."

# Step 1: Authenticate with Google Cloud using service account
echo "Authenticating with Google Cloud..."
# GOOGLE_APPLICATION_CREDENTIALS should be set by Cloud Run environment variable
# or mounted as a secret volume
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "ERROR: GOOGLE_APPLICATION_CREDENTIALS not set. Please configure in Cloud Run environment."
  exit 1
fi

# Step 2: Fetch API keys from GCP Secret Manager
echo "Fetching API keys from GCP Secret Manager..."
# Fetch Portkey API key
PORTKEY_API_KEY=$(gcloud secrets versions access latest --secret="PORTKEY_API_KEY" --project="$PROJECT_ID")
if [ -z "$PORTKEY_API_KEY" ]; then
  echo "WARNING: Could not fetch PORTKEY_API_KEY from Secret Manager. Some functionalities may be limited."
else
  export PORTKEY_API_KEY
  echo "Portkey API key successfully fetched and set."
fi

# Fetch OpenRouter API key
OPENROUTER_API_KEY=$(gcloud secrets versions access latest --secret="OPENROUTER_API_KEY" --project="$PROJECT_ID")
if [ -z "$OPENROUTER_API_KEY" ]; then
  echo "WARNING: Could not fetch OPENROUTER_API_KEY from Secret Manager. Some functionalities may be limited."
else
  export OPENROUTER_API_KEY
  echo "OpenRouter API key successfully fetched and set."
fi

# Step 3: Start the Phidata Agent service
echo "Starting Phidata Agent service..."
# Assuming the agent is started with a Python command
# Replace with the actual command to start your Phidata agent
exec python -m packages.agents.src.phidata.wrapper --host 0.0.0.0 --port 8080

echo "Phidata Agent service started on port 8080."

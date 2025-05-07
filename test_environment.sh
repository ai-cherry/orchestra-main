#!/bin/bash

# Set environment variables
export GCP_PROJECT_ID=cherry-ai-project
export GOOGLE_CLOUD_PROJECT=cherry-ai-project
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export RUN_INTEGRATION_TESTS=true

# Check if credentials exist
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "Credentials file found at $GOOGLE_APPLICATION_CREDENTIALS"
else
  echo "ERROR: Credentials file not found at $GOOGLE_APPLICATION_CREDENTIALS"
  exit 1
fi

# Run tests in virtual environment
source .venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
python -m pytest tests/integration/test_storage.py::TestFirestoreIntegration -v


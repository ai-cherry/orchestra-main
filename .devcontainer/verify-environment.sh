#!/bin/bash
set -e

echo "Verifying AI Orchestra development environment..."

# Check Python version
python --version

# Check Poetry version
poetry --version

# Check Terraform version
terraform --version

# Check gcloud CLI
gcloud --version

# Verify GCP authentication
if [ -n "$GCP_SA_KEY_JSON" ]; then
  echo "GCP service account key found, activating..."
  echo "$GCP_SA_KEY_JSON" > /tmp/gcp-key.json
  gcloud auth activate-service-account --key-file=/tmp/gcp-key.json
  rm /tmp/gcp-key.json
elif [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "GOOGLE_APPLICATION_CREDENTIALS is set, using for authentication"
else
  echo "No GCP credentials found, authentication may be required"
fi

# Set default project
gcloud config set project cherry-ai-project

# Check if Poetry virtual environment is activated
if [ -d ".venv" ]; then
  echo "Poetry virtual environment found"
else
  echo "Warning: Poetry virtual environment not found"
fi

# Check for common dependencies
echo "Checking for required Python packages..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" || echo "FastAPI not installed"
python -c "import pydantic; print(f'Pydantic version: {pydantic.__version__}')" || echo "Pydantic not installed"
python -c "import google.cloud; print('Google Cloud SDK available')" || echo "Google Cloud SDK not installed"

echo "Environment verification complete!"
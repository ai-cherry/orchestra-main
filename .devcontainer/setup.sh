#!/bin/bash
# Setup script for AI Orchestra development environment

set -e

echo "Setting up AI Orchestra development environment..."

# Install dependencies
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
poetry --version

# Configure Poetry
echo "Configuring Poetry..."
poetry config virtualenvs.in-project true

# Install project dependencies
echo "Installing project dependencies..."
poetry install

# Configure gcloud if credentials are available
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
  echo "Configuring gcloud..."
  echo $GCP_MASTER_SERVICE_JSON > /tmp/gcp-credentials.json
  gcloud auth activate-service-account --key-file=/tmp/gcp-credentials.json
  gcloud config set project cherry-ai-project
  gcloud config set run/region us-west4
  gcloud auth configure-docker us-docker.pkg.dev
  rm /tmp/gcp-credentials.json
else
  echo "GCP credentials not found. Skipping gcloud configuration."
fi

# Configure GitHub CLI if token is available
if [ -n "$GH_CLASSIC_PAT_TOKEN" ]; then
  echo "Configuring GitHub CLI..."
  echo $GH_CLASSIC_PAT_TOKEN | gh auth login --with-token
  gh config set editor vim
else
  echo "GitHub token not found. Skipping GitHub CLI configuration."
fi

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
poetry run pre-commit install

# Make scripts executable
echo "Making scripts executable..."
find ./scripts -type f -name "*.sh" -exec chmod +x {} \;
find ./scripts -type f -name "*.py" -exec chmod +x {} \;

# Create local environment file if it doesn't exist
if [ ! -f .env.local ]; then
  echo "Creating local environment file..."
  cat > .env.local << EOF
# Local environment variables
PROJECT_ID=cherry-ai-project
REGION=us-west4
ENVIRONMENT=dev
EOF
fi

echo "Setup complete! Your AI Orchestra development environment is ready."

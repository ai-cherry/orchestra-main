#!/bin/bash
# ci_cd_secrets_setup.sh
# Example script showing how to use create_secret.sh in a CI/CD pipeline
# This script demonstrates setting up required secrets for a deployment

set -e  # Exit on any error

# Base directory for scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if a tool is installed
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is required but not installed"
        exit 1
    fi
}

# Check required tools
check_tool gcloud
check_tool jq

# Parse arguments
ENVIRONMENT=${1:-production}
GCP_PROJECT_ID=${2:-"cherry-ai-project"}

echo "Setting up secrets for $ENVIRONMENT environment in project $GCP_PROJECT_ID"

# Ensure Secret Manager API is enabled
gcloud services enable secretmanager.googleapis.com --project="$GCP_PROJECT_ID"

# Example: Generate a random API key
RANDOM_API_KEY=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
"$SCRIPT_DIR/create_secret.sh" "EXAMPLE_API_KEY" "$RANDOM_API_KEY" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"

# Example: Save kubeconfig for Kubernetes deployments
if [ -f "$HOME/.kube/config" ]; then
    echo "Setting up Kubernetes config secret..."
    KUBE_CONFIG=$(cat "$HOME/.kube/config")
    "$SCRIPT_DIR/create_secret.sh" "KUBE_CONFIG" "$KUBE_CONFIG" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"
fi

# Example: Save database credentials
echo "Setting up database secrets..."
DB_USER="app_user"
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9!@#$%^&*()' | head -c 16)
DB_HOST="db.example.com"
DB_PORT="5432"
DB_NAME="app_database"

# Create individual secrets
"$SCRIPT_DIR/create_secret.sh" "DB_USER" "$DB_USER" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"
"$SCRIPT_DIR/create_secret.sh" "DB_PASSWORD" "$DB_PASSWORD" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"
"$SCRIPT_DIR/create_secret.sh" "DB_HOST" "$DB_HOST" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"
"$SCRIPT_DIR/create_secret.sh" "DB_PORT" "$DB_PORT" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"
"$SCRIPT_DIR/create_secret.sh" "DB_NAME" "$DB_NAME" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"

# Also create a combined JSON connection string for applications that prefer it
DB_CONNECTION_JSON=$(cat <<EOF
{
  "user": "$DB_USER",
  "password": "$DB_PASSWORD",
  "host": "$DB_HOST",
  "port": $DB_PORT,
  "database": "$DB_NAME",
  "ssl": true,
  "connectionTimeoutMs": 5000,
  "maxConnections": 10
}
EOF
)

"$SCRIPT_DIR/create_secret.sh" "DB_CONNECTION" "$DB_CONNECTION_JSON" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"

# Example: Save service account key if available in CI/CD environment variables
if [ -n "$SERVICE_ACCOUNT_KEY" ]; then
    echo "Setting up service account key secret..."
    "$SCRIPT_DIR/create_secret.sh" "SERVICE_ACCOUNT_KEY" "$SERVICE_ACCOUNT_KEY" "$GCP_PROJECT_ID" "user-managed" "$ENVIRONMENT" "us-west4,us-west1"
fi

# Example: Save other CI/CD secrets from environment variables
for SECRET_NAME in DOCKER_USERNAME DOCKER_PASSWORD GITHUB_TOKEN NPM_TOKEN; do
    if [ -n "${!SECRET_NAME}" ]; then
        echo "Saving $SECRET_NAME to Secret Manager..."
        "$SCRIPT_DIR/create_secret.sh" "$SECRET_NAME" "${!SECRET_NAME}" "$GCP_PROJECT_ID" "automatic" "$ENVIRONMENT"
    fi
done

echo "CI/CD secrets setup complete for $ENVIRONMENT environment!"
echo "Secrets are now available in Secret Manager and can be accessed in deployments"

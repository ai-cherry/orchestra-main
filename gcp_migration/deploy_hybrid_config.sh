#!/bin/bash
#
# Deploy Hybrid Configuration for AI Orchestra
#
# This script deploys and configures the hybrid environment for AI Orchestra
# across GitHub Codespaces, GCP Cloud Workstations, and Cloud Run.
#
# Usage:
#   ./deploy_hybrid_config.sh [--project=PROJECT_ID] [--location=LOCATION] [--env=ENV]
#

set -e

# Default values
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
LOCATION=${LOCATION:-"us-central1"}
ENV=${ENV:-"dev"}
CONFIG_DIR="./config"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --project=*)
      PROJECT_ID="${arg#*=}"
      shift
      ;;
    --location=*)
      LOCATION="${arg#*=}"
      shift
      ;;
    --env=*)
      ENV="${arg#*=}"
      shift
      ;;
    --config-dir=*)
      CONFIG_DIR="${arg#*=}"
      shift
      ;;
    *)
      # Unknown option
      echo "Unknown option: $arg"
      exit 1
      ;;
  esac
done

echo "Deploying hybrid configuration for AI Orchestra"
echo "Project ID: $PROJECT_ID"
echo "Location: $LOCATION"
echo "Environment: $ENV"
echo "Config Directory: $CONFIG_DIR"

# Functions
function check_gcloud_auth() {
  echo "Checking gcloud authentication..."
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "Not authenticated with gcloud. Please run 'gcloud auth login'."
    exit 1
  fi

  # Set project
  gcloud config set project $PROJECT_ID
  echo "Using Google Cloud project: $PROJECT_ID"
}

function check_environment() {
  echo "Detecting environment..."

  # Check if running in Cloud Run
  if [ -n "$K_SERVICE" ]; then
    echo "Running in Cloud Run"
    ENV_TYPE="cloud_run"
  # Check if running in GitHub Codespaces
  elif [ "$CODESPACES" = "true" ] || [ -n "$CODESPACE_NAME" ]; then
    echo "Running in GitHub Codespaces"
    ENV_TYPE="codespaces"
  # Check if running in GCP Cloud Workstation
  elif [ -d "/google/workstations" ]; then
    echo "Running in GCP Cloud Workstation"
    ENV_TYPE="workstation"
  else
    echo "Running in local environment"
    ENV_TYPE="local"
  fi

  echo "Environment type: $ENV_TYPE"
}

function ensure_config_directory() {
  echo "Ensuring configuration directory exists..."
  mkdir -p "$CONFIG_DIR"
  
  # Create base config files if they don't exist
  if [ ! -f "$CONFIG_DIR/common.json" ]; then
    echo "Creating common.json configuration..."
    cat > "$CONFIG_DIR/common.json" << EOF
{
  "project_id": "$PROJECT_ID",
  "location": "$LOCATION",
  "environment": "$ENV"
}
EOF
  fi
}

function create_environment_configs() {
  echo "Creating environment-specific configurations..."
  
  # Create local config
  if [ ! -f "$CONFIG_DIR/local.json" ]; then
    echo "Creating local.json configuration..."
    cat > "$CONFIG_DIR/local.json" << EOF
{
  "use_local_auth": true,
  "endpoints": {
    "admin-api": "http://localhost:8000",
    "memory": "http://localhost:8001",
    "agent": "http://localhost:8002",
    "mcp": "http://localhost:8003"
  }
}
EOF
  fi
  
  # Create codespaces config
  if [ ! -f "$CONFIG_DIR/codespaces.json" ]; then
    echo "Creating codespaces.json configuration..."
    cat > "$CONFIG_DIR/codespaces.json" << EOF
{
  "use_wif_auth": true,
  "codespaces_endpoints": {
    "admin-api": "http://localhost:8000",
    "memory": "http://localhost:8001",
    "agent": "http://localhost:8002",
    "mcp": "http://localhost:8003"
  }
}
EOF
  fi
  
  # Create workstation config
  if [ ! -f "$CONFIG_DIR/workstation.json" ]; then
    echo "Creating workstation.json configuration..."
    cat > "$CONFIG_DIR/workstation.json" << EOF
{
  "use_adc_auth": true,
  "workstation_id": "ai-orchestra-ws"
}
EOF
  fi
  
  # Create cloud_run config
  if [ ! -f "$CONFIG_DIR/cloud_run.json" ]; then
    echo "Creating cloud_run.json configuration..."
    cat > "$CONFIG_DIR/cloud_run.json" << EOF
{
  "use_adc_auth": true,
  "enable_cloud_logging": true,
  "enable_cloud_monitoring": true
}
EOF
  fi
}

function setup_gcp_resources() {
  if [ "$ENV_TYPE" == "cloud_run" ]; then
    echo "Skipping GCP resource setup in Cloud Run environment"
    return
  fi
  
  echo "Setting up GCP resources for hybrid configuration..."
  
  # Create Cloud Storage bucket for configuration
  BUCKET_NAME="$PROJECT_ID-$ENV-config"
  if ! gsutil ls -b "gs://$BUCKET_NAME" 2>/dev/null; then
    echo "Creating Cloud Storage bucket for configuration: $BUCKET_NAME"
    gsutil mb -l $LOCATION "gs://$BUCKET_NAME"
  else
    echo "Cloud Storage bucket already exists: $BUCKET_NAME"
  fi
  
  # Sync configuration to bucket
  echo "Syncing configuration to Cloud Storage..."
  gsutil -m rsync -r "$CONFIG_DIR" "gs://$BUCKET_NAME/config"
  
  # Setup Secret Manager for sensitive configurations
  echo "Setting up Secret Manager for hybrid configuration..."
  if ! gcloud secrets describe "hybrid-config-key" &>/dev/null; then
    echo "Creating hybrid-config-key secret..."
    echo "orchestra-$(date +%s)" | gcloud secrets create "hybrid-config-key" --data-file=-
  else
    echo "Secret hybrid-config-key already exists"
  fi
}

function configure_cloud_run() {
  # Only execute if in development environments  
  if [ "$ENV_TYPE" == "cloud_run" ]; then
    echo "Skipping Cloud Run configuration in Cloud Run environment"
    return
  fi
  
  echo "Configuring Cloud Run services for hybrid configuration..."
  
  # Update admin-api service
  if gcloud run services describe "admin-api" --platform managed --region=$LOCATION &>/dev/null; then
    echo "Configuring admin-api service..."
    gcloud run services update "admin-api" \
      --platform managed \
      --region=$LOCATION \
      --update-env-vars="ORCHESTRA_CONFIG_BUCKET=$PROJECT_ID-$ENV-config" \
      --update-secrets="ORCHESTRA_CONFIG_KEY=hybrid-config-key:latest"
  else
    echo "admin-api service does not exist, skipping configuration"
  fi
  
  # Update memory service
  if gcloud run services describe "memory" --platform managed --region=$LOCATION &>/dev/null; then
    echo "Configuring memory service..."
    gcloud run services update "memory" \
      --platform managed \
      --region=$LOCATION \
      --update-env-vars="ORCHESTRA_CONFIG_BUCKET=$PROJECT_ID-$ENV-config" \
      --update-secrets="ORCHESTRA_CONFIG_KEY=hybrid-config-key:latest"
  else
    echo "memory service does not exist, skipping configuration"
  fi
}

function setup_local_environment() {
  if [ "$ENV_TYPE" != "local" ] && [ "$ENV_TYPE" != "codespaces" ]; then
    echo "Skipping local environment setup in $ENV_TYPE environment"
    return
  fi
  
  echo "Setting up local environment variables..."
  
  # Add environment variables to .env file
  if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    touch .env
  fi
  
  # Update environment variables
  grep -q "ORCHESTRA_PROJECT_ID=" .env || echo "ORCHESTRA_PROJECT_ID=$PROJECT_ID" >> .env
  grep -q "ORCHESTRA_LOCATION=" .env || echo "ORCHESTRA_LOCATION=$LOCATION" >> .env
  grep -q "ORCHESTRA_ENV=" .env || echo "ORCHESTRA_ENV=$ENV" >> .env
  grep -q "ORCHESTRA_CONFIG_DIR=" .env || echo "ORCHESTRA_CONFIG_DIR=$CONFIG_DIR" >> .env
  
  echo "Local environment setup complete"
}

function deploy_hybrid_active_configuration() {
  echo "Deploying hybrid active configuration..."
  
  # Set up environment type
  export ENV_TYPE=$ENV_TYPE
  
  # Create indicator file for environment type detection
  echo $ENV_TYPE > "$CONFIG_DIR/.env_type"
  
  if [ "$ENV_TYPE" != "cloud_run" ]; then
    # Sync configuration to Cloud Storage
    gsutil -m rsync -r "$CONFIG_DIR" "gs://$PROJECT_ID-$ENV-config/config"
  fi
  
  echo "Hybrid active configuration deployed"
  echo "Environment type: $ENV_TYPE"
  echo "Configuration directory: $CONFIG_DIR"
  echo "GCS config path: gs://$PROJECT_ID-$ENV-config/config"
}

# Main execution
check_environment
ensure_config_directory
create_environment_configs

if [ "$ENV_TYPE" != "cloud_run" ]; then
  check_gcloud_auth
  setup_gcp_resources
  configure_cloud_run
fi

setup_local_environment
deploy_hybrid_active_configuration

echo "Hybrid configuration deployment complete!"
echo "To use the hybrid configuration in your code:"
echo "  from gcp_migration.hybrid_config import get_config"
echo "  config = get_config()"
echo "  endpoint = config.get_endpoint('service-name')"
echo ""
echo "Test the configuration with:"
echo "  python -m gcp_migration.hybrid_config --list-connections"
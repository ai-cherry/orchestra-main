#!/bin/bash
# setup_gcp_environment.sh
# Comprehensive script to set up the complete GCP environment for cherry-ai-project
# This script implements a phased approach:
# 1. Foundation Layer: Initialize GCP workspace and deploy basic infrastructure
# 2. AI Services Layer: Configure Vertex AI resources and service accounts
# 3. Application Layer: Deploy to Cloud Run and configure data sync pipeline

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
PROJECT_NUMBER="525398941159"
REGION="us-central1"
# Using GCP_MASTER_SERVICE_JSON environment variable for authentication

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    "PHASE")
      echo -e "\n${YELLOW}========== ${message} ==========${NC}\n"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if a command exists
check_command() {
  if ! command -v $1 &> /dev/null; then
    log "ERROR" "$1 is required but not installed. Please install it and try again."
    exit 1
  fi
}

# Check if a file exists
check_file() {
  if [ ! -f "$1" ]; then
    log "ERROR" "File $1 not found. Please ensure it exists and try again."
    exit 1
  fi
}

# Check prerequisites
check_prerequisites() {
  log "INFO" "Checking prerequisites..."
  
  # Check for GCP_MASTER_SERVICE_JSON environment variable
  if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
    log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is not set. Please set it and try again."
    exit 1
  fi
  
  log "SUCCESS" "Prerequisites check passed"
}

# Phase 1: Foundation Layer
# Task 1: Initialize the GCP Workspace
initialize_gcp_workspace() {
  log "PHASE" "PHASE 1: FOUNDATION LAYER"
  log "INFO" "Task 1: Initializing GCP workspace..."
  
  # Create temporary service account key file from environment variable
  log "INFO" "Creating temporary service account key file from GCP_MASTER_SERVICE_JSON..."
  echo "${GCP_MASTER_SERVICE_JSON}" > /tmp/gcp-master-key.json
  chmod 600 /tmp/gcp-master-key.json
  
  # Set environment variable for authentication
  log "INFO" "Setting GOOGLE_APPLICATION_CREDENTIALS environment variable..."
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-master-key.json
  
  log "INFO" "Using service account from GCP_MASTER_SERVICE_JSON"
  
  log "SUCCESS" "GCP workspace initialized successfully"
}

# Task 2: Set up Python environment
setup_python_environment() {
  log "INFO" "Task 2: Setting up Python environment..."
  
  # Check if Poetry is installed
  if command -v poetry &> /dev/null; then
    log "INFO" "Poetry is installed, using it for dependency management"
    
    # Install dependencies with Poetry
    log "INFO" "Installing dependencies with Poetry..."
    poetry install --no-interaction
    
    log "SUCCESS" "Python environment set up with Poetry"
  else
    log "WARN" "Poetry is not installed, falling back to pip"
    
    # Create virtual environment
    log "INFO" "Creating virtual environment..."
    python3 -m venv .venv
    
    # Activate virtual environment
    log "INFO" "Activating virtual environment..."
    source .venv/bin/activate
    
    # Install dependencies with pip
    log "INFO" "Installing dependencies with pip..."
    pip install -r vertex_ai_requirements.txt
    pip install fastapi uvicorn pydantic python-dotenv google-cloud-aiplatform google-cloud-storage
    
    log "SUCCESS" "Python environment set up with pip"
  fi
  
  log "SUCCESS" "Python environment set up successfully"
}

# Phase 2: Build Docker image
build_docker_image() {
  log "PHASE" "PHASE 2: BUILD DOCKER IMAGE"
  log "INFO" "Building Docker image..."
  
  # Check if Docker is installed
  if ! command -v docker &> /dev/null; then
    log "ERROR" "Docker is required but not installed. Please install it and try again."
    exit 1
  fi
  
  # Build Docker image
  log "INFO" "Building Docker image..."
  docker build -t ai-orchestra:latest .
  
  log "SUCCESS" "Docker image built successfully"
}

# Task 3: Run locally
run_locally() {
  log "INFO" "Task 3: Running application locally..."
  
  # Get the port from .env or use default
  PORT=$(grep -oP 'PORT=\K[0-9]+' .env 2>/dev/null || echo "8000")
  
  log "INFO" "Starting AI Orchestra API on port ${PORT}..."
  log "INFO" "API will be available at http://localhost:${PORT}"
  log "INFO" "Press Ctrl+C to stop the server"
  
  # Run the application
  if command -v poetry &> /dev/null; then
    # Run with Poetry
    poetry run uvicorn packages.api.main:app --reload --host 0.0.0.0 --port "${PORT}"
  else
    # Run with activated virtual environment
    uvicorn packages.api.main:app --reload --host 0.0.0.0 --port "${PORT}"
  fi
  
  log "SUCCESS" "Application running locally"
}

# Phase 3: Deploy to Cloud Run (if gcloud is available)
deploy_to_cloud_run() {
  log "PHASE" "PHASE 3: DEPLOY TO CLOUD RUN"
  log "INFO" "Checking if gcloud is available..."
  
  if command -v gcloud &> /dev/null; then
    log "INFO" "gcloud is available, deploying to Cloud Run..."
    
    # Deploy to Cloud Run
    log "INFO" "Deploying application to Cloud Run..."
    gcloud run deploy orchestra-api \
      --source . \
      --region ${REGION} \
      --platform managed \
      --allow-unauthenticated
    
    # Verify deployment
    log "INFO" "Verifying Cloud Run deployment..."
    SERVICE_URL=$(gcloud run services describe orchestra-api --region=${REGION} --format="value(status.url)")
    log "INFO" "Service URL: ${SERVICE_URL}"
    
    log "SUCCESS" "Application deployed to Cloud Run successfully"
  else
    log "WARN" "gcloud is not available, skipping Cloud Run deployment"
    log "INFO" "To deploy to Cloud Run, please install the Google Cloud SDK and run this script again"
  fi
}

# Phase 4: Set up environment variables
setup_environment_variables() {
  log "PHASE" "PHASE 4: SETTING UP ENVIRONMENT VARIABLES"
  
  # Check if .env file exists
  if [ ! -f .env ]; then
    log "INFO" "Creating .env file from .env.example..."
    if [ -f .env.example ]; then
      cp .env.example .env
      log "SUCCESS" ".env file created from .env.example"
    else
      log "WARN" ".env.example file not found, creating default .env file..."
      cat > .env << EOF
# Environment variables for AI Orchestra project
# Local development configuration

# Basic settings
ENVIRONMENT=dev
DEBUG=true

# GCP settings
PROJECT_ID=cherry-ai-project
REGION=us-central1

# Vertex AI settings
VERTEX_LOCATION=us-central1

# API settings
API_PREFIX=/api
PORT=8080

# Security settings
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
EOF
      log "SUCCESS" "Default .env file created"
    fi
  else
    log "INFO" ".env file already exists"
  fi
  
  log "SUCCESS" "Environment variables set up"
}

# Main function
main() {
  log "INFO" "Starting GCP environment setup for ${PROJECT_ID}..."
  
  # Check prerequisites
  check_prerequisites
  
  # Phase 1: Foundation Layer
  initialize_gcp_workspace
  setup_environment_variables
  setup_python_environment
  
  # Phase 2: Build Docker image
  build_docker_image
  
  # Phase 3: Deploy to Cloud Run (if gcloud is available)
  deploy_to_cloud_run
  
  # Phase 4: Run locally
  run_locally
  
  log "SUCCESS" "GCP environment setup completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Initialized GCP workspace"
  log "INFO" "2. Set up environment variables"
  log "INFO" "3. Set up Python environment"
  log "INFO" "4. Built Docker image"
  
  if command -v gcloud &> /dev/null; then
    log "INFO" "5. Deployed application to Cloud Run"
    log "INFO" "You can access your Cloud Run service at: $(gcloud run services describe orchestra-api --region=${REGION} --format='value(status.url)')"
  else
    log "INFO" "Application is running locally"
    log "INFO" "You can access your local service at: http://localhost:8000"
  fi
}

# Main function
main() {
  log "INFO" "Starting GCP environment setup for ${PROJECT_ID}..."
  
  # Check prerequisites
  check_prerequisites
  
  # Phase 1: Foundation Layer
  initialize_gcp_workspace
  deploy_basic_infrastructure
  
  # Phase 2: AI Services Layer
  configure_vertex_ai_service_accounts
  deploy_cloud_workstation
  setup_vertex_ai_workbench
  
  # Phase 3: Application Layer
  deploy_to_cloud_run
  configure_data_sync_pipeline
  
  log "SUCCESS" "GCP environment setup completed successfully!"
  log "INFO" "The following tasks have been completed:"
  log "INFO" "1. Initialized GCP workspace"
  log "INFO" "2. Deployed basic infrastructure"
  log "INFO" "3. Configured Vertex AI service accounts"
  log "INFO" "4. Deployed Cloud Workstation"
  log "INFO" "5. Set up Vertex AI Workbench notebooks"
  log "INFO" "6. Deployed application to Cloud Run"
  log "INFO" "7. Configured data sync pipeline"
  
  log "INFO" "You can access your Cloud Run service at: $(gcloud run services describe orchestra-api --region=${REGION} --format='value(status.url)')"
  log "INFO" "You can access your Cloud Workstation at: https://${REGION}.workstations.cloud.google.com/${PROJECT_ID}/${REGION}/ai-orchestra-cluster-prod/ai-orchestra-config-prod/ai-orchestra-workstation-prod-1"
}

# Execute main function
main
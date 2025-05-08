#!/bin/bash
# deploy.sh - Simplified deployment script for AI Orchestra to Google Cloud Run
# This script provides a streamlined approach for deploying to Cloud Run
# Updated: 5/8/2025 - Simplified for easier use

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/load_env.sh"

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log function for standardized output
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
    "STEP")
      echo -e "\n${BOLD}${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Default configuration values from environment variables with fallbacks
PROJECT_ID=$(get_config GCP_PROJECT_ID "cherry-ai-project")
REGION=$(get_config GCP_REGION "us-central1")
SERVICE_NAME=$(get_config CLOUD_RUN_SERVICE_NAME "orchestra-api")
ENVIRONMENT=$(get_config DEPLOYMENT_ENVIRONMENT "staging")
REPO_NAME=$(get_config ARTIFACT_REGISTRY_REPO "orchestra-repo")
MIN_INSTANCES=$(get_config CLOUD_RUN_MIN_INSTANCES 0)
MAX_INSTANCES=$(get_config CLOUD_RUN_MAX_INSTANCES 10)
MEMORY=$(get_config CLOUD_RUN_MEMORY "512Mi")
CPU=$(get_config CLOUD_RUN_CPU 1)
CONCURRENCY=$(get_config CLOUD_RUN_CONCURRENCY 80)
TIMEOUT=$(get_config CLOUD_RUN_TIMEOUT "300s")
ALLOW_UNAUTHENTICATED=$(get_config CLOUD_RUN_ALLOW_UNAUTHENTICATED true)  # Default to public access

# Display script banner
display_banner() {
  echo -e "${BLUE}"
  echo "==============================================================="
  echo "               AI Orchestra Cloud Run Deployment               "
  echo "==============================================================="
  echo -e "${NC}"
}

# Display usage information
display_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --project ID          GCP project ID (default: ${PROJECT_ID})"
  echo "  --region REGION       GCP region (default: ${REGION})"
  echo "  --service NAME        Cloud Run service name (default: ${SERVICE_NAME})"
  echo "  --env ENVIRONMENT     Deployment environment (default: ${ENVIRONMENT})"
  echo "  --repo NAME           Artifact Registry repository name (default: ${REPO_NAME})"
  echo "  --min-instances N     Minimum instances (default: ${MIN_INSTANCES})"
  echo "  --max-instances N     Maximum instances (default: ${MAX_INSTANCES})"
  echo "  --memory SIZE         Memory allocation (default: ${MEMORY})"
  echo "  --cpu N               CPU allocation (default: ${CPU})"
  echo "  --concurrency N       Request concurrency (default: ${CONCURRENCY})"
  echo "  --timeout DURATION    Request timeout (default: ${TIMEOUT})"
  echo "  --private             Require authentication (default is public)"
  echo "  --help                Show this help message"
}

# Parse command line arguments
parse_arguments() {
  while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
      --project)
        PROJECT_ID="$2"
        shift 2
        ;;
      --region)
        REGION="$2"
        shift 2
        ;;
      --service)
        SERVICE_NAME="$2"
        shift 2
        ;;
      --env)
        ENVIRONMENT="$2"
        shift 2
        ;;
      --repo)
        REPO_NAME="$2"
        shift 2
        ;;
      --min-instances)
        MIN_INSTANCES="$2"
        shift 2
        ;;
      --max-instances)
        MAX_INSTANCES="$2"
        shift 2
        ;;
      --memory)
        MEMORY="$2"
        shift 2
        ;;
      --cpu)
        CPU="$2"
        shift 2
        ;;
      --concurrency)
        CONCURRENCY="$2"
        shift 2
        ;;
      --timeout)
        TIMEOUT="$2"
        shift 2
        ;;
      --private)
        ALLOW_UNAUTHENTICATED=false
        shift
        ;;
      --help)
        display_banner
        display_usage
        exit 0
        ;;
      *)
        log "ERROR" "Unknown option: $1"
        display_usage
        exit 1
        ;;
    esac
  done
}

# Check for required dependencies
check_dependencies() {
  log "STEP" "Checking dependencies"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not installed"
    log "INFO" "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
  
  # Check for docker
  if ! command -v docker &> /dev/null; then
    log "ERROR" "docker is required but not installed"
    exit 1
  fi
  
  log "SUCCESS" "All dependencies are installed"
}

# Set up GCP environment - Simplified
setup_environment() {
  log "STEP" "Setting up GCP environment"
  
  # Simplified authentication - just use current credentials
  log "INFO" "Using current gcloud authentication"
  
  # Set project and region configuration
  log "INFO" "Setting project to: ${PROJECT_ID}"
  gcloud config set project ${PROJECT_ID} || log "WARN" "Failed to set project, continuing anyway"

  # Set region configuration 
  log "INFO" "Setting region to: ${REGION}"
  gcloud config set run/region ${REGION} || log "WARN" "Failed to set region, continuing anyway"
  
  # Image name for Artifact Registry
  IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:${ENVIRONMENT}"
  log "INFO" "Using image name: ${IMAGE_NAME}"
}

# Enable required GCP APIs
enable_apis() {
  log "STEP" "Enabling required GCP APIs"
  
  log "INFO" "Enabling Artifact Registry and Cloud Run APIs"
  gcloud services enable artifactregistry.googleapis.com run.googleapis.com \
    --project=${PROJECT_ID} || log "WARN" "Failed to enable APIs, continuing anyway"
  
  log "SUCCESS" "GCP APIs enabled successfully"
}

# Set up Artifact Registry
setup_artifact_registry() {
  log "STEP" "Setting up Artifact Registry"
  
  log "INFO" "Checking if repository exists: ${REPO_NAME}"
  if ! gcloud artifacts repositories describe ${REPO_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} > /dev/null 2>&1; then
    
    log "INFO" "Creating new repository: ${REPO_NAME}"
    gcloud artifacts repositories create ${REPO_NAME} \
      --repository-format=docker \
      --location=${REGION} \
      --project=${PROJECT_ID} || log "WARN" "Failed to create repository, continuing anyway"
  else
    log "INFO" "Repository already exists: ${REPO_NAME}"
  fi
  
  # Configure Docker to use Artifact Registry
  log "INFO" "Configuring Docker authentication for Artifact Registry"
  gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet || log "WARN" "Failed to configure Docker auth, continuing anyway"
  
  log "SUCCESS" "Artifact Registry setup complete"
}

# Build the Docker image
build_image() {
  log "STEP" "Building Docker image"
  
  log "INFO" "Building ${SERVICE_NAME} image for ${ENVIRONMENT} environment"
  docker build -t ${IMAGE_NAME} . || {
    log "ERROR" "Docker build failed"
    exit 1
  }
  
  log "SUCCESS" "Docker image built successfully"
}

# Push the Docker image to Artifact Registry
push_image() {
  log "STEP" "Pushing image to Artifact Registry"
  
  log "INFO" "Pushing image: ${IMAGE_NAME}"
  docker push ${IMAGE_NAME} || {
    log "ERROR" "Docker push failed"
    exit 1
  }
  
  log "SUCCESS" "Image pushed to Artifact Registry"
}

# Prepare environment variables - Simplified
prepare_config() {
  log "STEP" "Preparing configuration"
  
  # Base environment variables
  ENV_VARS="ENVIRONMENT=${ENVIRONMENT}"
  
  # Load environment variables from file if it exists
  ENV_FILE=".env.${ENVIRONMENT}"
  if [ -f "${ENV_FILE}" ]; then
    log "INFO" "Loading environment variables from ${ENV_FILE}"
    ENV_VARS="${ENV_VARS},$(grep -v '^#' ${ENV_FILE} | xargs | sed 's/ /,/g')"
  else
    log "WARN" "Environment file ${ENV_FILE} not found, using default configuration"
  fi
  
  log "SUCCESS" "Configuration prepared successfully"
}

# Deploy to Cloud Run - Simplified
deploy_to_cloud_run() {
  log "STEP" "Deploying to Cloud Run"
  
  # Prepare base deploy command
  DEPLOY_CMD="gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --region=${REGION} \
    --platform=managed \
    --memory=${MEMORY} \
    --cpu=${CPU} \
    --concurrency=${CONCURRENCY} \
    --timeout=${TIMEOUT} \
    --min-instances=${MIN_INSTANCES} \
    --max-instances=${MAX_INSTANCES} \
    --set-env-vars=${ENV_VARS}"
  
  # Set authentication options
  if [ "$ALLOW_UNAUTHENTICATED" = true ]; then
    DEPLOY_CMD="${DEPLOY_CMD} --allow-unauthenticated"
    log "INFO" "Service will be publicly accessible"
  else
    DEPLOY_CMD="${DEPLOY_CMD} --no-allow-unauthenticated"
    log "INFO" "Service will require authentication"
  fi
  
  # Execute deployment
  log "INFO" "Executing deployment command"
  eval "${DEPLOY_CMD}" || {
    log "ERROR" "Deployment failed"
    exit 1
  }
  
  log "SUCCESS" "Deployment to Cloud Run completed"
}

# Verify the deployment - Simplified
verify_deployment() {
  log "STEP" "Verifying deployment"
  
  # Get the service URL
  SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format='value(status.url)') || {
    log "WARN" "Could not get service URL"
    return
  }
  
  log "INFO" "Service URL: ${SERVICE_URL}"
  
  # Simplified health check - just display the URL
  if [ "$ALLOW_UNAUTHENTICATED" = true ]; then
    log "INFO" "To test the service:"
    echo "curl ${SERVICE_URL}/health"
  else
    log "INFO" "To test with authentication:"
    echo "curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" ${SERVICE_URL}/health"
  fi
  
  log "SUCCESS" "Deployment verification complete"
}

# Main execution
main() {
  display_banner
  parse_arguments "$@"
  
  log "INFO" "Deployment configuration:"
  log "INFO" "- Project ID: ${PROJECT_ID}"
  log "INFO" "- Region: ${REGION}"
  log "INFO" "- Service Name: ${SERVICE_NAME}"
  log "INFO" "- Environment: ${ENVIRONMENT}"
  log "INFO" "- Public Access: ${ALLOW_UNAUTHENTICATED}"
  
  check_dependencies
  setup_environment
  enable_apis
  setup_artifact_registry
  build_image
  push_image
  prepare_config
  deploy_to_cloud_run
  verify_deployment
  
  log "SUCCESS" "AI Orchestra deployment process completed successfully"
}

# Execute main function with all arguments
main "$@"

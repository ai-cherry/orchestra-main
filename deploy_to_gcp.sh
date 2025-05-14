#!/bin/bash
# Standardized GCP Deployment Script for AI Orchestra
# This script handles deployment of services to Google Cloud Platform,
# addressing all previously identified issues and providing a unified approach.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE="admin-api"
DOCKERFILE_PATH="services/admin-api/Dockerfile"
SOURCE_DIR="services/admin-api"
PLATFORM="managed"
MIN_INSTANCES=0
MAX_INSTANCES=10
CPU=1
MEMORY="1Gi"
TIMEOUT=300
CONCURRENCY=80
PORT=8080
ENV_VARS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE_PATH="$2"
      shift 2
      ;;
    --source-dir)
      SOURCE_DIR="$2"
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
    --env-vars)
      ENV_VARS="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project-id ID       GCP project ID (default: cherry-ai-project)"
      echo "  --region REGION       GCP region (default: us-central1)"
      echo "  --service NAME        Service name (default: admin-api)"
      echo "  --dockerfile PATH     Path to Dockerfile (default: services/admin-api/Dockerfile)"
      echo "  --source-dir DIR      Source directory (default: services/admin-api)"
      echo "  --min-instances N     Minimum instances (default: 0)"
      echo "  --max-instances N     Maximum instances (default: 10)"
      echo "  --memory SIZE         Memory allocation (default: 1Gi)"
      echo "  --cpu N               CPU allocation (default: 1)"
      echo "  --env-vars VARS       Environment variables (comma-separated key=value pairs)"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Function to check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Banner
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             AI Orchestra Deployment to GCP                     ║"
echo "║            Standardized Deployment Pipeline                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}Deployment Configuration:${NC}"
echo -e "  Project ID:      ${BOLD}${PROJECT_ID}${NC}"
echo -e "  Region:          ${BOLD}${REGION}${NC}"
echo -e "  Service:         ${BOLD}${SERVICE}${NC}"
echo -e "  Dockerfile:      ${BOLD}${DOCKERFILE_PATH}${NC}"
echo -e "  Source Dir:      ${BOLD}${SOURCE_DIR}${NC}"
echo -e "  Min Instances:   ${BOLD}${MIN_INSTANCES}${NC}"
echo -e "  Max Instances:   ${BOLD}${MAX_INSTANCES}${NC}"
echo -e "  Memory:          ${BOLD}${MEMORY}${NC}"
echo -e "  CPU:             ${BOLD}${CPU}${NC}"
echo ""

#-------------------------------------------
# STEP 1: Pre-deployment checks
#-------------------------------------------
echo -e "${YELLOW}${BOLD}STEP 1: Running pre-deployment checks...${NC}"

# Check if required commands exist
REQUIRED_COMMANDS=("gcloud" "docker" "poetry")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
  if ! command_exists "$cmd"; then
    echo -e "${RED}Error: $cmd is not installed but is required.${NC}"
    exit 1
  fi
done

# Ensure we're using the correct project
echo "Setting project to ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"

# Verify poetry.toml exists and has the proper format
if [ -f "${SOURCE_DIR}/pyproject.toml" ]; then
  if ! grep -q "\[tool.poetry\]" "${SOURCE_DIR}/pyproject.toml"; then
    echo -e "${RED}Error: pyproject.toml does not contain [tool.poetry] section.${NC}"
    echo -e "${YELLOW}Please make sure the pyproject.toml is properly formatted for Poetry.${NC}"
    exit 1
  else
    echo -e "${GREEN}✓ pyproject.toml is properly formatted for Poetry${NC}"
  fi
else
  echo -e "${RED}Error: pyproject.toml not found in ${SOURCE_DIR}${NC}"
  exit 1
fi

# Check if Dockerfile exists
if [ ! -f "${DOCKERFILE_PATH}" ]; then
  echo -e "${RED}Error: Dockerfile not found at ${DOCKERFILE_PATH}${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Dockerfile found${NC}"
fi

# Enable required APIs if not already enabled
echo "Ensuring required APIs are enabled..."
REQUIRED_APIS=("cloudbuild.googleapis.com" "run.googleapis.com" "artifactregistry.googleapis.com")
for api in "${REQUIRED_APIS[@]}"; do
  gcloud services enable "$api" --project="${PROJECT_ID}"
done

echo -e "${GREEN}✓ Pre-deployment checks passed${NC}"

#-------------------------------------------
# STEP 2: Build the Docker image
#-------------------------------------------
echo -e "\n${YELLOW}${BOLD}STEP 2: Building Docker image...${NC}"

# Set up some variables for the build
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE}:${TIMESTAMP}"

# Check if we need to create/update poetry.lock
if [ ! -f "${SOURCE_DIR}/poetry.lock" ]; then
  echo "No poetry.lock found, generating it..."
  (cd "${SOURCE_DIR}" && poetry lock)
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to generate poetry.lock${NC}"
    exit 1
  else
    echo -e "${GREEN}✓ Generated poetry.lock${NC}"
  fi
fi

# Build the Docker image with Cloud Build
echo "Building Docker image: ${IMAGE_NAME}"
gcloud builds submit --tag="${IMAGE_NAME}" "${SOURCE_DIR}" \
  --timeout=15m --project="${PROJECT_ID}"

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Docker build failed${NC}"
  echo -e "${YELLOW}Checking for common issues:${NC}"
  echo -e "1. Verify that pyproject.toml has [tool.poetry] section"
  echo -e "2. Ensure poetry.lock is up-to-date"
  echo -e "3. Check Dockerfile for correct COPY commands"
  exit 1
else
  echo -e "${GREEN}✓ Docker image built successfully: ${IMAGE_NAME}${NC}"
fi

#-------------------------------------------
# STEP 3: Deploy to Cloud Run
#-------------------------------------------
echo -e "\n${YELLOW}${BOLD}STEP 3: Deploying to Cloud Run...${NC}"

# Prepare environment variables arguments
ENV_ARGS=""
if [ -n "$ENV_VARS" ]; then
  IFS=',' read -ra ENV_PAIRS <<< "$ENV_VARS"
  for pair in "${ENV_PAIRS[@]}"; do
    ENV_ARGS="${ENV_ARGS} --set-env-vars=${pair}"
  done
fi

# Add deployment environment variable
ENV_ARGS="${ENV_ARGS} --set-env-vars=ENVIRONMENT=production"

# Deploy to Cloud Run
echo "Deploying ${SERVICE} to Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE}" \
  --image="${IMAGE_NAME}" \
  --platform="${PLATFORM}" \
  --region="${REGION}" \
  --min-instances="${MIN_INSTANCES}" \
  --max-instances="${MAX_INSTANCES}" \
  --cpu="${CPU}" \
  --memory="${MEMORY}" \
  --timeout="${TIMEOUT}s" \
  --concurrency="${CONCURRENCY}" \
  --port="${PORT}" \
  --allow-unauthenticated \
  ${ENV_ARGS} \
  --project="${PROJECT_ID}"

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Deployment to Cloud Run failed${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Successfully deployed ${SERVICE} to Cloud Run${NC}"
fi

#-------------------------------------------
# STEP 4: Post-deployment verification
#-------------------------------------------
echo -e "\n${YELLOW}${BOLD}STEP 4: Verifying deployment...${NC}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE}" \
  --platform="${PLATFORM}" \
  --region="${REGION}" \
  --format="value(status.url)" \
  --project="${PROJECT_ID}")

echo "Service URL: ${SERVICE_URL}"

# Wait for the service to be fully deployed
echo "Waiting for service to become available..."
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}" || echo "error")
  
  if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Service is up and responding with HTTP 200${NC}"
    break
  elif [ "$HTTP_STATUS" = "error" ]; then
    echo "Connection error, retrying..."
  else
    echo "Service returned HTTP ${HTTP_STATUS}, retrying..."
  fi
  
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
    echo "Attempt $RETRY_COUNT of $MAX_RETRIES, waiting 5 seconds..."
    sleep 5
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo -e "${YELLOW}Warning: Could not verify service is responding with HTTP 200${NC}"
  echo -e "${YELLOW}Please check the service manually at: ${SERVICE_URL}${NC}"
fi

#-------------------------------------------
# Deployment Summary
#-------------------------------------------
echo -e "\n${BLUE}${BOLD}Deployment Summary:${NC}"
echo -e "  Service:         ${BOLD}${SERVICE}${NC}"
echo -e "  URL:             ${BOLD}${SERVICE_URL}${NC}"
echo -e "  Project:         ${BOLD}${PROJECT_ID}${NC}"
echo -e "  Region:          ${BOLD}${REGION}${NC}"
echo -e "  Image:           ${BOLD}${IMAGE_NAME}${NC}"
echo -e "  Instances:       ${BOLD}${MIN_INSTANCES}-${MAX_INSTANCES}${NC}"
echo -e "  Memory:          ${BOLD}${MEMORY}${NC}"
echo -e "  CPU:             ${BOLD}${CPU}${NC}"

echo -e "\n${GREEN}${BOLD}Deployment completed successfully!${NC}"
echo -e "To view logs for your service, run:"
echo -e "  ${BLUE}gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE}\" --limit=10 --project=${PROJECT_ID}${NC}"
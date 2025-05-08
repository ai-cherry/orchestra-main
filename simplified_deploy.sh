#!/bin/bash
# simplified_deploy.sh - Streamlined deployment script for single-developer projects
# Prioritizes development velocity and simplicity over complex security measures

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Simple logging function
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
  exit 1
}

# Default values
PROJECT_ID=""
SERVICE_NAME="ai-orchestra"
REGION="us-central1"
ENV="dev"
SKIP_TESTS=false
SKIP_BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --service)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --env)
      ENV="$2"
      shift 2
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project PROJECT_ID  GCP Project ID (required)"
      echo "  --service NAME        Service name (default: ai-orchestra)"
      echo "  --region REGION       GCP Region (default: us-central1)"
      echo "  --env ENV             Environment (default: dev)"
      echo "  --skip-tests          Skip running tests"
      echo "  --skip-build          Skip building Docker image"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      ;;
  esac
done

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
  error "Project ID is required. Use --project to specify it."
fi

# Simplified GCP authentication
log "Authenticating with GCP..."
if [ -f "service-account-key.json" ]; then
  export GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
  log "Using service account key: service-account-key.json"
else
  log "No service account key found, using gcloud default credentials"
  # Try to get project from gcloud config
  if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
      error "Could not determine project ID. Please specify with --project."
    fi
    log "Using project from gcloud config: $PROJECT_ID"
  fi
fi

# Run tests if not skipped
if [ "$SKIP_TESTS" = false ]; then
  log "Running tests..."
  if command -v poetry &>/dev/null; then
    poetry run pytest -xvs tests/
  else
    python -m pytest -xvs tests/
  fi
fi

# Build and push Docker image if not skipped
if [ "$SKIP_BUILD" = false ]; then
  log "Building Docker image..."
  IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${ENV}"
  docker build -t "$IMAGE_NAME" .
  
  log "Pushing Docker image to GCR..."
  docker push "$IMAGE_NAME"
fi

# Deploy to Cloud Run
log "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}-${ENV}" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${ENV}" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --project "$PROJECT_ID"

# Get the deployed URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}-${ENV}" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format="value(status.url)")

log "Deployment complete!"
log "Service URL: $SERVICE_URL"

# Optional: Open the URL in a browser
if command -v open &>/dev/null; then
  log "Opening service URL in browser..."
  open "$SERVICE_URL"
elif command -v xdg-open &>/dev/null; then
  log "Opening service URL in browser..."
  xdg-open "$SERVICE_URL"
fi

log "Simplified deployment completed successfully!"
#!/bin/bash
# simplified_auth.sh - Streamlined GCP authentication for single-developer projects
# Prioritizes development velocity over complex security measures

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

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
  exit 1
}

# Default values
PROJECT_ID=""
KEY_FILE="service-account-key.json"
SKIP_VALIDATION=false
FORCE_REFRESH=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --key-file)
      KEY_FILE="$2"
      shift 2
      ;;
    --skip-validation)
      SKIP_VALIDATION=true
      shift
      ;;
    --force-refresh)
      FORCE_REFRESH=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project PROJECT_ID  GCP Project ID"
      echo "  --key-file FILE       Service account key file (default: service-account-key.json)"
      echo "  --skip-validation     Skip validation of credentials"
      echo "  --force-refresh       Force refresh of credentials"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      ;;
  esac
done

# Check if gcloud is installed
if ! command -v gcloud &>/dev/null; then
  error "gcloud CLI not found. Please install the Google Cloud SDK."
fi

# Try to get project ID if not provided
if [ -z "$PROJECT_ID" ]; then
  # Try to get from key file
  if [ -f "$KEY_FILE" ]; then
    if command -v jq &>/dev/null; then
      PROJECT_ID=$(jq -r '.project_id' "$KEY_FILE" 2>/dev/null)
      if [ -n "$PROJECT_ID" ] && [ "$PROJECT_ID" != "null" ]; then
        log "Using project ID from key file: $PROJECT_ID"
      fi
    fi
  fi
  
  # If still not set, try to get from gcloud config
  if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$PROJECT_ID" ] && [ "$PROJECT_ID" != "(unset)" ]; then
      log "Using project ID from gcloud config: $PROJECT_ID"
    else
      warn "Could not determine project ID. Some commands may fail."
    fi
  fi
fi

# Authenticate with service account key if available
if [ -f "$KEY_FILE" ]; then
  log "Authenticating with service account key: $KEY_FILE"
  
  # Set environment variable for application default credentials
  export GOOGLE_APPLICATION_CREDENTIALS="$(realpath "$KEY_FILE")"
  log "Set GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
  
  # Activate service account for gcloud
  if [ "$FORCE_REFRESH" = true ] || ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log "Activating service account for gcloud..."
    gcloud auth activate-service-account --key-file="$KEY_FILE"
  else
    log "Service account already activated for gcloud"
  fi
  
  # Set project if available
  if [ -n "$PROJECT_ID" ]; then
    log "Setting gcloud project to: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
  fi
else
  warn "Service account key file not found: $KEY_FILE"
  warn "Falling back to user authentication"
  
  # Check if user is logged in
  if [ "$FORCE_REFRESH" = true ] || ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log "Logging in with user account..."
    gcloud auth login
    
    # Also set up application default credentials
    log "Setting up application default credentials..."
    gcloud auth application-default login
  else
    log "User already logged in to gcloud"
  fi
  
  # Set project if available
  if [ -n "$PROJECT_ID" ]; then
    log "Setting gcloud project to: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
  fi
fi

# Validate authentication if not skipped
if [ "$SKIP_VALIDATION" = false ]; then
  log "Validating authentication..."
  
  # Test gcloud authentication
  log "Testing gcloud authentication..."
  if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    error "Failed to validate gcloud authentication"
  fi
  
  # Test application default credentials
  log "Testing application default credentials..."
  if [ -f "$KEY_FILE" ]; then
    # Simple test using curl and access token
    ACCESS_TOKEN=$(gcloud auth print-access-token 2>/dev/null)
    if [ -z "$ACCESS_TOKEN" ]; then
      warn "Could not get access token for validation"
    else
      # Test token with a simple API call
      if ! curl -s -f -H "Authorization: Bearer $ACCESS_TOKEN" "https://cloudresourcemanager.googleapis.com/v1/projects/$PROJECT_ID" &>/dev/null; then
        warn "Failed to validate access token"
      else
        log "Access token validated successfully"
      fi
    fi
  fi
fi

# Print authentication summary
log "Authentication completed successfully!"
log "Active account: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
if [ -n "$PROJECT_ID" ]; then
  log "Active project: $PROJECT_ID"
fi
if [ -f "$KEY_FILE" ]; then
  log "Using service account key: $KEY_FILE"
  log "GOOGLE_APPLICATION_CREDENTIALS is set for this terminal session"
  log "To use in other terminals, run: export GOOGLE_APPLICATION_CREDENTIALS=\"$(realpath "$KEY_FILE")\""
fi

# Print helpful next steps
log "Next steps:"
log "  - Run 'simplified_deploy.sh' to deploy your application"
log "  - Run 'python mcp_server/run_optimized_server.py' to start the optimized MCP server"
log "  - Run 'disable_restrictions.sh' to disable VS Code security restrictions"
#!/bin/bash
# Performance-optimized GitHub to GCP Secret Manager migration script
# This script migrates secrets from GitHub to Google Secret Manager

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display messages
info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Print title
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  GitHub to GCP Secret Manager Migration Tool  ${NC}"
echo -e "${BLUE}===============================================${NC}"
echo

# Parse command-line arguments
PROJECT_ID=""
ENV_FILE=".env"
AUTO_APPROVE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --auto-approve)
      AUTO_APPROVE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo
      echo "Options:"
      echo "  --project PROJECT_ID    The GCP project ID (required if not in gcloud config)"
      echo "  --env-file FILE         Path to .env file with secrets (default: .env)"
      echo "  --auto-approve          Skip confirmation prompts"
      echo "  --help                  Display this help message"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Determine project ID if not provided
if [ -z "$PROJECT_ID" ]; then
  info "No project ID provided, attempting to get from gcloud config..."
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
  
  if [ -z "$PROJECT_ID" ]; then
    error "No project ID provided and couldn't determine from gcloud config."
    error "Please provide a project ID with --project or set it with 'gcloud config set project'"
    exit 1
  fi
fi

info "Using GCP project: $PROJECT_ID"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  error "Environment file $ENV_FILE not found!"
  exit 1
fi

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
  error "gcloud CLI not found. Please install Google Cloud SDK."
  exit 1
fi

# Check for GCP authentication
if ! gcloud auth print-access-token &> /dev/null; then
  error "Not authenticated with GCP. Please run 'gcloud auth login' first."
  exit 1
fi

# Enable Secret Manager API if not already enabled
info "Checking if Secret Manager API is enabled..."
if ! gcloud services list --enabled --filter="name:secretmanager.googleapis.com" --project="$PROJECT_ID" | grep -q "secretmanager.googleapis.com"; then
  info "Enabling Secret Manager API..."
  gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"
  success "Secret Manager API enabled"
else
  success "Secret Manager API already enabled"
fi

# Load environment variables
info "Loading secrets from $ENV_FILE..."
# Count number of secrets in the file (excluding comments and empty lines)
SECRET_COUNT=$(grep -v '^#' "$ENV_FILE" | grep -v '^$' | wc -l)
info "Found $SECRET_COUNT secret(s) to migrate"

# Preview secrets to be migrated (without showing values)
echo -e "${BLUE}===============================================${NC}"
echo -e "${YELLOW}Secrets to be migrated:${NC}"
echo -e "${BLUE}===============================================${NC}"
grep -v '^#' "$ENV_FILE" | grep -v '^$' | cut -d '=' -f 1 | sort | awk '{print "  - " $1}'

# Confirm migration
if [ "$AUTO_APPROVE" != "true" ]; then
  echo
  read -p "Proceed with migration? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Migration aborted by user"
    exit 1
  fi
fi

# Main migration function
migrate_secret() {
  local name="$1"
  local value="$2"
  local options="${3:-}"
  local version="${4:-}"
  local secret_id="$name"
  
  # Check if secret exists
  if gcloud secrets describe "$secret_id" --project="$PROJECT_ID" &>/dev/null; then
    info "Secret $secret_id exists, adding new version..."
    echo -n "$value" | gcloud secrets versions add "$secret_id" --data-file=- --project="$PROJECT_ID" $options
    success "Updated secret $secret_id"
  else
    info "Creating new secret $secret_id..."
    echo -n "$value" | gcloud secrets create "$secret_id" --data-file=- --project="$PROJECT_ID" $options
    success "Created secret $secret_id"
  fi
}

# Counter for tracking progress
COUNTER=0
SUCCESS_COUNT=0
FAILURE_COUNT=0

# Process each secret in the .env file
echo
info "Starting secret migration..."
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  # Skip comments and empty lines
  [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
  
  # Trim whitespace from key and value
  key=$(echo "$key" | xargs)
  value=$(echo "$value" | xargs)
  
  # Progress counter
  ((COUNTER++))
  info "[$COUNTER/$SECRET_COUNT] Processing $key..."
  
  # Migrate the secret
  if migrate_secret "$key" "$value"; then
    ((SUCCESS_COUNT++))
  else
    ((FAILURE_COUNT++))
  fi
  
  # Add a small delay to avoid API rate limiting
  sleep 0.5
done < "$ENV_FILE"

# Print summary
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Migration Complete!${NC}"
echo -e "${BLUE}===============================================${NC}"
echo "Total secrets processed: $COUNTER"
echo "Successful migrations:   $SUCCESS_COUNT"
echo "Failed migrations:       $FAILURE_COUNT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
  warn "Some secrets failed to migrate. Please check the logs above."
  exit 1
else
  success "All secrets successfully migrated to GCP Secret Manager!"
fi

# Instructions for accessing secrets
echo
info "To access these secrets in your GCP Workstation:"
echo "  1. In Terraform: Use google_secret_manager_secret_version data source"
echo "  2. In container: Use Secret Manager environment variable references"
echo "     Example: GEMINI_API_KEY=sm://projects/${PROJECT_ID}/secrets/GEMINI_API_KEY/versions/latest"
echo "  3. In code: Use the Secret Manager client library"
echo
echo "For additional security, configure IAM permissions on individual secrets as needed."
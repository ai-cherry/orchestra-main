#!/bin/bash
# Comprehensive script to sync GitHub secrets to Google Cloud Secret Manager
# This script will:
# 1. Fetch GitHub secrets
# 2. Create a .env file with those secrets
# 3. Run migrate_secrets.sh to transfer them to Google Secret Manager

set -e

# ANSI color codes for better readability
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
echo -e "${BLUE}  GitHub Secrets to GCP Secret Manager Sync   ${NC}"
echo -e "${BLUE}===============================================${NC}"
echo

# Parse command-line arguments
PROJECT_ID=""
ENV_FILE=".env.github_secrets"
AUTO_APPROVE=false
GITHUB_REPO=""
GITHUB_TOKEN=""

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
    --github-repo)
      GITHUB_REPO="$2"
      shift 2
      ;;
    --github-token)
      GITHUB_TOKEN="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo
      echo "Options:"
      echo "  --project PROJECT_ID      The GCP project ID (required if not in gcloud config)"
      echo "  --env-file FILE           Path to output .env file (default: .env.github_secrets)"
      echo "  --github-repo REPO        GitHub repository in format 'owner/repo'"
      echo "  --github-token TOKEN      Personal access token with repo and secrets access"
      echo "  --auto-approve            Skip confirmation prompts"
      echo "  --help                    Display this help message"
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

# Check for GitHub token if not provided
if [ -z "$GITHUB_TOKEN" ]; then
  if [ -f "$HOME/.github_token" ]; then
    GITHUB_TOKEN=$(cat "$HOME/.github_token")
    info "Using GitHub token from $HOME/.github_token"
  else
    error "GitHub token not provided and couldn't find token file."
    error "Please provide a GitHub token with --github-token or create $HOME/.github_token"
    error "You need a GitHub token with 'repo' and 'admin:org' scopes."
    exit 1
  fi
fi

# Check if the GitHub repo is provided
if [ -z "$GITHUB_REPO" ]; then
  # Try to determine from git remote
  if command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
    GITHUB_REPO=$(git remote get-url origin | grep -o 'github.com[:/][^/]*/[^.]*' | sed 's/github.com[:/]//')
    info "Determined GitHub repo from git remote: $GITHUB_REPO"
  else
    error "GitHub repository not specified and couldn't determine from git."
    error "Please provide a GitHub repository with --github-repo"
    exit 1
  fi
fi

# Check for required tools
if ! command -v curl &> /dev/null; then
  error "curl not found. Please install curl."
  exit 1
fi

if ! command -v jq &> /dev/null; then
  error "jq not found. Please install jq."
  exit 1
fi

info "Step 1: Fetching GitHub secrets from $GITHUB_REPO"

# Make directory for secrets if it doesn't exist
SECRETS_DIR="$(dirname "$ENV_FILE")"
if [ "$SECRETS_DIR" != "." ] && [ ! -d "$SECRETS_DIR" ]; then
  mkdir -p "$SECRETS_DIR"
fi

# Create or clear the env file
> "$ENV_FILE"

# Get repository secrets
REPO_SECRETS=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$GITHUB_REPO/actions/secrets")

# Check if we got a valid response or error
if echo "$REPO_SECRETS" | jq -e '.message' &>/dev/null; then
  ERROR_MSG=$(echo "$REPO_SECRETS" | jq -r '.message')
  error "Failed to fetch repository secrets: $ERROR_MSG"
  exit 1
fi

# Extract secret names - we can't get the actual values, just names
SECRET_NAMES=$(echo "$REPO_SECRETS" | jq -r '.secrets[].name')
SECRET_COUNT=$(echo "$SECRET_NAMES" | wc -l)

info "Found $SECRET_COUNT secrets in GitHub repository."
echo

# If we couldn't fetch actual secrets, we'll need to list them and ask for values
echo -e "${YELLOW}GitHub API doesn't allow retrieving secret values.${NC}"
echo -e "${YELLOW}Please provide the values for each secret:${NC}"

for SECRET_NAME in $SECRET_NAMES; do
  # Skip empty names if any
  [ -z "$SECRET_NAME" ] && continue
  
  echo -e "${BLUE}Secret:${NC} $SECRET_NAME"
  if [ -t 0 ]; then  # Check if running in interactive terminal
    # Use read with -s for sensitive input (no echo)
    read -sp "Enter value: " SECRET_VALUE
    echo  # Add newline after hidden input
  else
    # Non-interactive mode, might be used in automation
    warn "Running in non-interactive mode. Will use placeholder for $SECRET_NAME."
    SECRET_VALUE="PLACEHOLDER_VALUE_FOR_$SECRET_NAME"
  fi
  
  # Add to env file
  echo "$SECRET_NAME=$SECRET_VALUE" >> "$ENV_FILE"
done

success "Created environment file with all secrets: $ENV_FILE"

# Display the migration plan
echo
info "Step 2: Migrating secrets to Google Secret Manager"
echo
echo -e "${BLUE}===============================================${NC}"
echo -e "${YELLOW}The following secrets will be migrated:${NC}"
echo -e "${BLUE}===============================================${NC}"
grep -v '^#' "$ENV_FILE" | cut -d '=' -f 1 | sort | awk '{print "  - " $1}'

# Confirm migration
if [ "$AUTO_APPROVE" != "true" ]; then
  echo
  read -p "Continue with migration to Google Secret Manager? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Migration aborted by user"
    exit 1
  fi
fi

# Run the migrate_secrets.sh script
MIGRATE_SCRIPT="scripts/migrate_secrets.sh"
if [ ! -f "$MIGRATE_SCRIPT" ]; then
  MIGRATE_SCRIPT="./migrate_secrets.sh"
  if [ ! -f "$MIGRATE_SCRIPT" ]; then
    error "Could not find migrate_secrets.sh script."
    error "Please ensure the script exists at scripts/migrate_secrets.sh or ./migrate_secrets.sh"
    exit 1
  fi
fi

info "Running secret migration script..."
bash "$MIGRATE_SCRIPT" --project "$PROJECT_ID" --env-file "$ENV_FILE" --auto-approve

# Clean up
if [ "$AUTO_APPROVE" == "true" ]; then
  info "Cleaning up temporary env file..."
  rm -f "$ENV_FILE"
  success "Temporary env file removed."
else
  warn "Temporary env file still exists at: $ENV_FILE"
  warn "You may want to delete it after verifying the migration."
fi

echo
success "GitHub secrets have been successfully synced to Google Secret Manager!"
echo
info "Next steps:"
echo "  1. Verify secrets in Google Secret Manager: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo "  2. Update your applications to use Secret Manager references"
echo "  3. Set appropriate IAM permissions for accessing these secrets"

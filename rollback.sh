#!/bin/bash
# rollback.sh - Rollback script for AI Orchestra project
#
# This script provides rollback capabilities for the AI Orchestra project deployment
# It can revert changes to previous versions in case of deployment issues

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
ENV="dev"
COMPONENT="all"  # Options: all, mcp-server, main-app, infrastructure
VERSION=""       # If empty, will roll back to the previous version

# Display banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                 AI Orchestra Rollback Script                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse command line arguments
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
    --env)
      ENV="$2"
      shift 2
      ;;
    --component)
      COMPONENT="$2"
      shift 2
      ;;
    --version)
      VERSION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project PROJECT_ID       GCP project ID (default: cherry-ai-project)"
      echo "  --region REGION            GCP region (default: us-central1)"
      echo "  --env ENV                  Environment (dev, staging, prod) (default: dev)"
      echo "  --component COMPONENT      Component to roll back (all, mcp-server, main-app, infrastructure) (default: all)"
      echo "  --version VERSION          Version to roll back to (default: previous version)"
      echo "  --help                     Display this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $key${NC}"
      exit 1
      ;;
  esac
done

# Function to display step information
step() {
  echo -e "${GREEN}➤ $1${NC}"
}

# Function to display information
info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

# Function to display warnings
warn() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to display errors and exit
error() {
  echo -e "${RED}✖ $1${NC}"
  exit 1
}

# Function to prompt for confirmation
confirm() {
  local message=$1
  local response

  echo -e "${YELLOW}${message} (y/n)${NC}"
  read -r response

  if [[ "$response" =~ ^[Yy]$ ]]; then
    return 0  # true
  else
    return 1  # false
  fi
}

# Check for required environment variables
if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
  echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable is not set.${NC}"
  echo "Please set it to the content of your GCP service account key JSON."
  exit 1
fi

# Authenticate with GCP
step "Authenticating with Google Cloud Platform"
echo "$GCP_MASTER_SERVICE_JSON" > /tmp/gcp-key.json
gcloud auth activate-service-account --key-file=/tmp/gcp-key.json || error "Failed to authenticate with GCP"
gcloud config set project "$PROJECT_ID" || error "Failed to set GCP project"
info "Successfully authenticated with GCP"

# Function to roll back MCP Server
rollback_mcp_server() {
  step "Rolling back MCP Server"

  # Get the current version
  CURRENT_VERSION=$(gcloud run services describe "mcp-server-$ENV" --region="$REGION" --format="value(status.latestReadyRevision.name)")
  info "Current version: $CURRENT_VERSION"

  # Get the previous version if not specified
  if [[ -z "$VERSION" ]]; then
    # List all revisions and get the second one (previous version)
    REVISIONS=$(gcloud run revisions list --service="mcp-server-$ENV" --region="$REGION" --format="value(name)" | sort -r)
    VERSION=$(echo "$REVISIONS" | sed -n '2p')

    if [[ -z "$VERSION" ]]; then
      error "No previous version found for MCP Server"
    fi
  fi

  info "Rolling back to version: $VERSION"

  # Roll back to the specified version
  gcloud run services update-traffic "mcp-server-$ENV" \
    --region="$REGION" \
    --to-revisions="$VERSION=100" || error "Failed to roll back MCP Server"

  info "Successfully rolled back MCP Server to version: $VERSION"
}

# Function to roll back main application
rollback_main_app() {
  step "Rolling back main application"

  # Get the current version
  CURRENT_VERSION=$(gcloud run services describe "orchestra-api-$ENV" --region="$REGION" --format="value(status.latestReadyRevision.name)")
  info "Current version: $CURRENT_VERSION"

  # Get the previous version if not specified
  if [[ -z "$VERSION" ]]; then
    # List all revisions and get the second one (previous version)
    REVISIONS=$(gcloud run revisions list --service="orchestra-api-$ENV" --region="$REGION" --format="value(name)" | sort -r)
    VERSION=$(echo "$REVISIONS" | sed -n '2p')

    if [[ -z "$VERSION" ]]; then
      error "No previous version found for main application"
    fi
  fi

  info "Rolling back to version: $VERSION"

  # Roll back to the specified version
  gcloud run services update-traffic "orchestra-api-$ENV" \
    --region="$REGION" \
    --to-revisions="$VERSION=100" || error "Failed to roll back main application"

  info "Successfully rolled back main application to version: $VERSION"
}

# Function to roll back infrastructure
rollback_infrastructure() {
  step "Rolling back infrastructure"

  if confirm "Rolling back infrastructure can be destructive. Are you sure you want to proceed?"; then
    cd terraform

    # Check if there's a backup state file
    if [[ ! -f "terraform.tfstate.backup" ]]; then
      error "No backup state file found for infrastructure"
    fi

    # Restore the backup state file
    info "Restoring backup state file"
    cp terraform.tfstate.backup terraform.tfstate

    # Apply the restored state
    info "Applying restored state"
    terraform apply -auto-approve || error "Failed to apply restored state"

    cd ..

    info "Successfully rolled back infrastructure"
  else
    warn "Skipping infrastructure rollback"
  fi
}

# Perform rollback based on component
case "$COMPONENT" in
  "all")
    if confirm "This will roll back all components (MCP Server, main application, and infrastructure). Are you sure you want to proceed?"; then
      rollback_mcp_server
      rollback_main_app
      rollback_infrastructure
    else
      warn "Rollback cancelled"
      exit 0
    fi
    ;;
  "mcp-server")
    if confirm "This will roll back the MCP Server. Are you sure you want to proceed?"; then
      rollback_mcp_server
    else
      warn "Rollback cancelled"
      exit 0
    fi
    ;;
  "main-app")
    if confirm "This will roll back the main application. Are you sure you want to proceed?"; then
      rollback_main_app
    else
      warn "Rollback cancelled"
      exit 0
    fi
    ;;
  "infrastructure")
    if confirm "This will roll back the infrastructure. Are you sure you want to proceed?"; then
      rollback_infrastructure
    else
      warn "Rollback cancelled"
      exit 0
    fi
    ;;
  *)
    error "Invalid component: $COMPONENT. Valid options are: all, mcp-server, main-app, infrastructure"
    ;;
esac

# Clean up temporary files
rm -f /tmp/gcp-key.json

# Completion message
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Rollback Successful!                        ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo -e "${BLUE}Project ID: ${NC}$PROJECT_ID"
echo -e "${BLUE}Region: ${NC}$REGION"
echo -e "${BLUE}Environment: ${NC}$ENV"
echo -e "${BLUE}Component: ${NC}$COMPONENT"
echo -e "${BLUE}Version: ${NC}$VERSION"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Verify the rolled back components are working as expected"
echo -e "2. Investigate the issues that led to the rollback"
echo -e "3. Fix the issues and redeploy when ready"
echo ""
echo -e "${GREEN}Thank you for using the AI Orchestra rollback script!${NC}"

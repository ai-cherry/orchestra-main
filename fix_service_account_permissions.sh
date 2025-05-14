#!/bin/bash
# fix_service_account_permissions.sh - Fix service account permissions for GCP services
#
# This script grants necessary roles to service accounts used by Cloud Run and other services,
# including the Compute Engine default service account which needs logging permissions.
#
# Usage:
#   ./fix_service_account_permissions.sh [SERVICE_ACCOUNT_EMAIL] [PROJECT_ID]
#
# Example:
#   ./fix_service_account_permissions.sh "525398941159-compute@developer.gserviceaccount.com" "cherry-ai-project"

set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
DEFAULT_SA="525398941159-compute@developer.gserviceaccount.com"
SERVICE_ACCOUNT=${1:-$DEFAULT_SA}
PROJECT_ID=${2:-"cherry-ai-project"}

echo -e "${BLUE}${BOLD}Service Account Permissions Fix Tool${NC}"
echo -e "${BLUE}Fixing service account permissions for ${SERVICE_ACCOUNT}...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud command is not installed or not in PATH${NC}"
    echo "Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo -e "${BLUE}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project "${PROJECT_ID}"

# Define necessary roles for Cloud Run service accounts
ROLES=(
    "roles/logging.logWriter"     # Required for logging
    "roles/storage.objectViewer"  # For accessing storage objects
    "roles/artifactregistry.writer" # For pushing/pulling container images
    "roles/run.admin"            # For deploying to Cloud Run
)

# Grant each role to the service account
for ROLE in "${ROLES[@]}"; do
    echo -e "${YELLOW}Granting ${ROLE} to ${SERVICE_ACCOUNT}...${NC}"
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="${ROLE}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully granted ${ROLE} to ${SERVICE_ACCOUNT}${NC}"
    else
        echo -e "${RED}Failed to grant ${ROLE} to ${SERVICE_ACCOUNT}${NC}"
        exit 1
    fi
done

# Verify the roles have been assigned
echo -e "${BLUE}Verifying role assignments...${NC}"
ASSIGNED_ROLES=$(gcloud projects get-iam-policy "${PROJECT_ID}" \
    --filter="bindings.members:${SERVICE_ACCOUNT}" \
    --format="value(bindings.role)")

echo -e "${GREEN}${BOLD}Successfully updated service account permissions!${NC}"
echo -e "${GREEN}The service account ${SERVICE_ACCOUNT} now has the following roles:${NC}"

for ROLE in "${ROLES[@]}"; do
    if [[ "${ASSIGNED_ROLES}" == *"${ROLE}"* ]]; then
        echo -e "  - ${ROLE}"
    fi
done

echo ""
echo -e "${YELLOW}These permissions should resolve the Cloud Build logging issues.${NC}"
#!/bin/bash
# check_permissions.sh - Check if the service account has the necessary permissions for deploying to Cloud Run

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
SERVICE_ACCOUNT="codespaces-powerful-sa@cherry-ai-project.iam.gserviceaccount.com"
PROJECT_ID="cherry-ai-project"

echo -e "${BLUE}=== Checking Permissions for Service Account ===${NC}"
echo -e "Service Account: ${SERVICE_ACCOUNT}"
echo -e "Project ID: ${PROJECT_ID}"
echo

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if gcloud is installed
if ! command_exists gcloud; then
  echo -e "${RED}Error: gcloud is not installed${NC}"
  exit 1
fi

# Check if authenticated
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$ACTIVE_ACCOUNT" ]; then
  echo -e "${RED}Error: Not authenticated with gcloud${NC}"
  echo -e "Please run 'gcloud auth login' or 'gcloud auth activate-service-account' first"
  exit 1
fi

echo -e "${YELLOW}Currently authenticated as: ${ACTIVE_ACCOUNT}${NC}"
echo

# Check if the service account exists
echo -e "${YELLOW}Checking if service account exists...${NC}"
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
  echo -e "${GREEN}✓ Service account exists${NC}"
else
  echo -e "${RED}✗ Service account does not exist or you don't have permission to view it${NC}"
  exit 1
fi

# Check if the service account is enabled
echo -e "${YELLOW}Checking if service account is enabled...${NC}"
SA_STATUS=$(gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" --format="json" | jq -r '.disabled // false')
if [ "$SA_STATUS" = "true" ]; then
  echo -e "${RED}✗ Service account is disabled${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Service account is enabled${NC}"
fi

# Check for required roles
echo -e "${YELLOW}Checking for required roles...${NC}"
REQUIRED_ROLES=(
  "roles/run.admin"
  "roles/storage.admin"
  "roles/iam.serviceAccountUser"
  "roles/artifactregistry.admin"
)

# Get the IAM policy for the project
IAM_POLICY=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json)

# Check each required role
for role in "${REQUIRED_ROLES[@]}"; do
  echo -e "Checking for role: ${role}"
  
  # Check if the service account has the role
  if echo "$IAM_POLICY" | jq -e --arg sa "serviceAccount:$SERVICE_ACCOUNT" --arg role "$role" '.bindings[] | select(.role == $role) | .members[] | select(. == $sa)' &>/dev/null; then
    echo -e "${GREEN}✓ Service account has role: ${role}${NC}"
  else
    echo -e "${RED}✗ Service account does not have role: ${role}${NC}"
    echo -e "   To grant this role, run:"
    echo -e "   gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SERVICE_ACCOUNT --role=$role"
  fi
done

# Check if Cloud Run API is enabled
echo -e "\n${YELLOW}Checking if Cloud Run API is enabled...${NC}"
if gcloud services list --enabled --filter="name:run.googleapis.com" --project="$PROJECT_ID" | grep -q "run.googleapis.com"; then
  echo -e "${GREEN}✓ Cloud Run API is enabled${NC}"
else
  echo -e "${RED}✗ Cloud Run API is not enabled${NC}"
  echo -e "   To enable it, run:"
  echo -e "   gcloud services enable run.googleapis.com --project=$PROJECT_ID"
fi

# Check if Container Registry API is enabled
echo -e "\n${YELLOW}Checking if Container Registry API is enabled...${NC}"
if gcloud services list --enabled --filter="name:containerregistry.googleapis.com" --project="$PROJECT_ID" | grep -q "containerregistry.googleapis.com"; then
  echo -e "${GREEN}✓ Container Registry API is enabled${NC}"
else
  echo -e "${RED}✗ Container Registry API is not enabled${NC}"
  echo -e "   To enable it, run:"
  echo -e "   gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID"
fi

# Check if Artifact Registry API is enabled
echo -e "\n${YELLOW}Checking if Artifact Registry API is enabled...${NC}"
if gcloud services list --enabled --filter="name:artifactregistry.googleapis.com" --project="$PROJECT_ID" | grep -q "artifactregistry.googleapis.com"; then
  echo -e "${GREEN}✓ Artifact Registry API is enabled${NC}"
else
  echo -e "${RED}✗ Artifact Registry API is not enabled${NC}"
  echo -e "   To enable it, run:"
  echo -e "   gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID"
fi

echo -e "\n${BLUE}=== Permission Check Complete ===${NC}"
echo -e "If any required roles or APIs are missing, please add them using the provided commands."
echo -e "Once all permissions are in place, you should be able to deploy to Cloud Run."
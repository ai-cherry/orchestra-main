#!/bin/bash
# Script to securely initialize secrets in Google Secret Manager
# This script should be run before applying the secure_vertex_figma_integration.tf file

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure the GCP project ID is provided
if [ -z "$1" ]; then
  echo -e "${RED}Error: Project ID not provided${NC}"
  echo "Usage: $0 <project-id>"
  exit 1
fi

PROJECT_ID=$1
echo -e "${GREEN}Initializing secrets for project: ${PROJECT_ID}${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo -e "${RED}Error: gcloud CLI is not installed${NC}"
  echo "Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q '@'; then
  echo -e "${RED}Error: Not authenticated with gcloud${NC}"
  echo "Please run: gcloud auth login"
  exit 1
fi

# Verify the project exists and user has access
if ! gcloud projects describe "${PROJECT_ID}" &> /dev/null; then
  echo -e "${RED}Error: Project ${PROJECT_ID} does not exist or you don't have access${NC}"
  exit 1
fi

# Check if Secret Manager API is enabled
if ! gcloud services list --project "${PROJECT_ID}" | grep -q 'secretmanager.googleapis.com'; then
  echo -e "${YELLOW}Secret Manager API is not enabled. Enabling it now...${NC}"
  gcloud services enable secretmanager.googleapis.com --project "${PROJECT_ID}"
  echo -e "${GREEN}Secret Manager API enabled${NC}"
fi

# Function to safely prompt for secret values
get_secret_value() {
  local secret_name=$1
  local default_value=$2
  local secret_value=""
  
  # If a default is provided via environment variable, use it
  env_var_name=$(echo $secret_name | tr '-' '_' | tr '[:lower:]' '[:upper:]')
  
  if [ ! -z "${!env_var_name}" ]; then
    secret_value="${!env_var_name}"
    echo -e "${YELLOW}Using ${env_var_name} from environment${NC}"
  else
    # Otherwise prompt the user
    read -s -p "Enter value for ${secret_name} (input hidden): " secret_value
    echo ""
    
    # If still empty and default provided, use default
    if [ -z "$secret_value" ] && [ ! -z "$default_value" ]; then
      echo -e "${YELLOW}Using default value for ${secret_name}${NC}"
      secret_value=$default_value
    fi
  fi
  
  # Verify we have a value
  if [ -z "$secret_value" ]; then
    echo -e "${RED}Error: No value provided for ${secret_name}${NC}"
    return 1
  fi
  
  echo "$secret_value"
}

# Function to create or update a secret
create_or_update_secret() {
  local secret_id=$1
  local project_id=$2
  local secret_value=$3
  
  # Check if secret exists
  if gcloud secrets describe ${secret_id} --project ${project_id} &> /dev/null; then
    echo -e "${YELLOW}Secret ${secret_id} already exists. Adding new version...${NC}"
  else
    # Create the secret
    echo -e "Creating secret: ${secret_id}..."
    gcloud secrets create ${secret_id} --replication-policy="automatic" --project ${project_id}
  fi
  
  # Add the secret version (pipe through command to avoid logging)
  echo -n "${secret_value}" | gcloud secrets versions add ${secret_id} --data-file=- --project ${project_id}
  
  echo -e "${GREEN}Successfully stored ${secret_id}${NC}"
}

echo -e "\n${YELLOW}WARNING: You will now be prompted for sensitive credentials.${NC}"
echo -e "${YELLOW}These values will not be displayed or logged, but will be stored in Secret Manager.${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to abort.${NC}\n"

# Prompt for each secret value securely
echo -e "Setting up Figma Personal Access Token (PAT)..."
FIGMA_PAT=$(get_secret_value "figma-personal-access-token" "")

echo -e "\nSetting up Vertex API Key..."
VERTEX_API_KEY=$(get_secret_value "vertex-api-key" "")

echo -e "\nSetting up GCP API Key..."
GCP_API_KEY=$(get_secret_value "gcp-api-key" "")

echo -e "\nSetting up OAuth Client Secret..."
OAUTH_CLIENT_SECRET=$(get_secret_value "oauth-client-secret" "")

# Store all secrets in Secret Manager
echo -e "\n${GREEN}Storing secrets in Secret Manager...${NC}"

create_or_update_secret "figma-personal-access-token" "${PROJECT_ID}" "${FIGMA_PAT}"
create_or_update_secret "vertex-api-key" "${PROJECT_ID}" "${VERTEX_API_KEY}"
create_or_update_secret "gcp-api-key" "${PROJECT_ID}" "${GCP_API_KEY}"
create_or_update_secret "oauth-client-secret" "${PROJECT_ID}" "${OAUTH_CLIENT_SECRET}"

echo -e "\n${GREEN}All secrets have been securely stored in Secret Manager.${NC}"
echo -e "${GREEN}You can now safely apply the Terraform configuration.${NC}"
echo -e "${YELLOW}Important: Rotate these credentials regularly and do not share them.${NC}"

# Cleanup any variables containing sensitive data
unset FIGMA_PAT VERTEX_API_KEY GCP_API_KEY OAUTH_CLIENT_SECRET

echo -e "\n${GREEN}Secret initialization complete!${NC}"

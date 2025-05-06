#!/bin/bash
# Wrapper script to set environment variables and run the service key creation script

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   SERVICE KEY CREATION SCRIPT WRAPPER   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Function to check if a script exists and is executable
check_script() {
  local script_name=$1
  
  if [ ! -f "$script_name" ]; then
    echo -e "${RED}Error: Script $script_name not found.${NC}"
    exit 1
  fi
  
  if [ ! -x "$script_name" ]; then
    echo -e "${YELLOW}Warning: Script $script_name is not executable. Making it executable...${NC}"
    chmod +x "$script_name"
  fi
  
  echo -e "${GREEN}Script $script_name is ready to run.${NC}"
}

# Check if the GitHub PAT is provided or exists
get_github_pat() {
  local github_pat="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"
  
  echo -e "${YELLOW}Using GitHub PAT for authentication...${NC}"
  
  if [ -z "$github_pat" ]; then
    echo -e "${RED}Error: GitHub Personal Access Token not provided.${NC}"
    exit 1
  fi
  
  echo "$github_pat"
}

# Create mock GCP keys for demonstration purposes
create_mock_keys() {
  echo -e "${YELLOW}Creating mock GCP service account keys for demonstration...${NC}"
  
  # Create a mock GCP project admin key
  cat > "mock_gcp_project_admin_key.json" << EOF
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "mock_private_key_id_for_project_admin",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "project-admin@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "mock_client_id_for_project_admin",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/project-admin%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  
  # Create a mock GCP secret management key
  cat > "mock_gcp_secret_management_key.json" << EOF
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "mock_private_key_id_for_secret_management",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "secret-management@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "mock_client_id_for_secret_management",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/secret-management%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  
  echo -e "${GREEN}Mock GCP service account keys created.${NC}"
}

# Main function
main() {
  echo -e "${YELLOW}Starting service key creation process...${NC}"
  
  # Check if the update_github_gcp_service_keys.sh script exists and is executable
  check_script "update_github_gcp_service_keys.sh"
  
  # Get the GitHub PAT
  GITHUB_PAT=$(get_github_pat)
  
  # Create mock GCP keys
  create_mock_keys
  
  # Set environment variables
  export GCP_PROJECT_ADMIN_KEY=$(cat mock_gcp_project_admin_key.json)
  export GCP_SECRET_MANAGEMENT_KEY=$(cat mock_gcp_secret_management_key.json)
  export GITHUB_PAT="$GITHUB_PAT"
  
  echo -e "${YELLOW}Environment variables set:${NC}"
  echo -e "  - GCP_PROJECT_ADMIN_KEY: [set]"
  echo -e "  - GCP_SECRET_MANAGEMENT_KEY: [set]"
  echo -e "  - GITHUB_PAT: [set]"
  
  echo -e "\n${YELLOW}Running service key creation script...${NC}"
  echo -e "${BLUE}=================================================================${NC}"
  
  # For demonstration purposes, instead of actually running the script, we'll just echo what would happen
  echo -e "${YELLOW}In a real environment, this would execute:${NC}"
  echo -e "  ./update_github_gcp_service_keys.sh"
  
  # Uncomment the line below to actually run the script
  # ./update_github_gcp_service_keys.sh
  
  echo -e "${BLUE}=================================================================${NC}"
  echo -e "${GREEN}${BOLD}Script execution demonstration completed.${NC}"
  echo -e "${YELLOW}For security reasons, the script execution was simulated.${NC}"
  echo -e "${YELLOW}In a real environment, you would need to:${NC}"
  echo -e "  1. Ensure the GitHub PAT has the required permissions"
  echo -e "  2. Ensure the GCP service account keys are properly configured"
  echo -e "  3. Remove the simulation code and uncomment the actual script execution line"
  
  # Clean up mock keys
  echo -e "\n${YELLOW}Cleaning up mock keys...${NC}"
  rm -f mock_gcp_project_admin_key.json mock_gcp_secret_management_key.json
  
  echo -e "${GREEN}Mock keys removed.${NC}"
}

# Execute the main function
main

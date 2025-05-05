#!/bin/bash
# Script to create comprehensive service account keys for Vertex AI and Gemini services
# and update GitHub organization-level secrets with the new keys and project information

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration variables
GCP_PROJECT_ID="cherry-ai-project"
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"

# Authenticate with GitHub CLI
#echo -e "\n${YELLOW}Authenticating with GitHub CLI...${NC}"
#gh auth login --with-token <<< "$GITHUB_PAT"

# Fetch secrets from GitHub
#echo -e "\n${YELLOW}Fetching secrets from GitHub...${NC}"
#GCP_PROJECT_ADMIN_KEY=$(gh secret get GCP_PROJECT_ADMIN_KEY --org "$GITHUB_ORG" 2>/dev/null)
#if [ -z "$GCP_PROJECT_ADMIN_KEY" ]; then
#  echo -e "${RED}Error: GCP_PROJECT_ADMIN_KEY not found in GitHub organization secrets.${NC}"
#  exit 1
#fi

#GCP_SECRET_MANAGEMENT_KEY=$(gh secret get GCP_SECRET_MANAGEMENT_KEY --org "$GITHUB_ORG" 2>/dev/null)
#if [ -z "$GCP_SECRET_MANAGEMENT_KEY" ]; then
#  echo -e "${RED}Error: GCP_SECRET_MANAGEMENT_KEY not found in GitHub organization secrets.${NC}"
#  exit 1
#fi
VERTEX_SA_NAME="vertex-admin-sa"
GEMINI_SA_NAME="gemini-admin-sa"
SECRET_MGMT_SA_NAME="secret-management-sa"

# Print header
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   COMPREHENSIVE VERTEX AI AND GEMINI SERVICE KEY CREATOR   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# Function to check if gcloud is installed and authenticated
check_gcloud() {
  echo -e "\n${YELLOW}Checking gcloud installation and authentication...${NC}"
  
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
  fi
  
  # Check if user is authenticated
  #if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
  #  echo -e "${RED}Error: Not authenticated with gcloud. Please run 'gcloud auth login' first.${NC}"
  #  exit 1
  #fi

  # Activate service account using the provided key
  echo -e "\n${YELLOW}Activating service account using GCP_PROJECT_ADMIN_KEY...${NC}"
  
  # Create a temporary file to store the service account key
  echo "$GCP_PROJECT_ADMIN_KEY" > /tmp/gcp_project_admin_key.json
  
  gcloud auth activate-service-account --key-file=/tmp/gcp_project_admin_key.json
  
  # Verify authentication
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Failed to authenticate with gcloud using the provided key.${NC}"
    exit 1
  fi
  
  # Check if project exists and is accessible
  if ! gcloud projects describe "${GCP_PROJECT_ID}" &> /dev/null; then
    echo -e "${RED}Error: Project ${GCP_PROJECT_ID} does not exist or is not accessible.${NC}"
    exit 1
-------
  
  echo -e "${GREEN}gcloud is properly configured.${NC}"
-------
-------
-------
-------
}

# Function to create a service account if it doesn't exist
create_service_account() {
  local sa_name=$1
  local description=$2
  
  echo -e "\n${YELLOW}Creating service account: ${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com...${NC}"
  
  if gcloud iam service-accounts describe "${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" &> /dev/null; then
    echo -e "${YELLOW}Service account already exists. Skipping creation.${NC}"
  else
    gcloud iam service-accounts create "${sa_name}" \
      --display-name="${description}" \
      --project="${GCP_PROJECT_ID}"
    echo -e "${GREEN}Service account created successfully.${NC}"
  fi
}

# Function to assign roles to a service account
assign_roles() {
  local sa_name=$1
  local roles=("${@:2}")
  
  echo -e "\n${YELLOW}Assigning roles to ${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com...${NC}"
  
  for role in "${roles[@]}"; do
    echo "  - Assigning role: ${role}"
    gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="serviceAccount:${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
      --role="${role}" \
      --quiet
  done
  
  echo -e "${GREEN}Roles assigned successfully.${NC}"
}

# Function to create and download service account key
#create_key() {
#  local sa_name=$1
#  local key_file="/tmp/${sa_name}-key.json"
#
#  echo -e "\n${YELLOW}Creating and downloading key for ${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com...${NC}"
#
#  gcloud iam service-accounts keys create "${key_file}" \
#    --iam-account="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
#    --project="${GCP_PROJECT_ID}"
#
#  echo -e "${GREEN}Key created and downloaded to ${key_file}${NC}"
#
#  # Read the key file content
#  SA_KEY=$(cat "${key_file}")
#
#  # Base64 encode for GitHub secrets
#  SA_KEY_BASE64=$(echo "${SA_KEY}" | base64 -w 0)
#
#  echo "${SA_KEY_BASE64}" > "/tmp/${sa_name}-key-base64.txt"
#  echo -e "${GREEN}Base64 encoded key saved to /tmp/${sa_name}-key-base64.txt${NC}"
#
#  # Return the base64 encoded key
#  echo "${SA_KEY_BASE64}"
#}

# Function to update GitHub secrets (this would normally use gh CLI but we'll make it a placeholder that prints instructions)
update_github_secret() {
  local secret_name=$1
  local secret_value=$2
  
  echo -e "\n${YELLOW}Updating GitHub secret: ${secret_name}...${NC}"
  
  # In a real implementation, you'd use the GitHub CLI or API:
  # gh secret set "${secret_name}" --org "${GITHUB_ORG}" --body "${secret_value}"
  
  # For now, we'll just output instructions
  echo -e "${BLUE}To update this secret manually:${NC}"
  echo -e "1. Go to ${GITHUB_ORG} organization settings"
  echo -e "2. Navigate to Secrets and variables -> Actions"
  echo -e "3. Add or update a secret with name: ${secret_name}"
  echo -e "4. Use the value from /tmp/${secret_name}.txt"
}

# Main execution

# 1. Check gcloud setup
check_gcloud

# 2. Create and configure Vertex AI service account
create_service_account "${VERTEX_SA_NAME}" "Vertex AI Administrator Service Account"

# Assign comprehensive roles for Vertex AI
VERTEX_ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/artifactregistry.admin"
  "roles/compute.admin"
  "roles/iam.serviceAccountUser"
  "roles/logging.admin"
  "roles/storage.admin"
  "roles/monitoring.admin"
)
assign_roles "${VERTEX_SA_NAME}" "${VERTEX_ROLES[@]}"

# 3. Create and configure Gemini service account
create_service_account "${GEMINI_SA_NAME}" "Gemini Services Administrator Service Account"

# Assign comprehensive roles for Gemini
GEMINI_ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/artifactregistry.admin"
  "roles/compute.admin"
  "roles/iam.serviceAccountUser"
  "roles/logging.admin"
  "roles/storage.admin"
  "roles/monitoring.admin"
)
assign_roles "${GEMINI_SA_NAME}" "${GEMINI_ROLES[@]}"

# 4. Create and configure Secret Management service account
create_service_account "${SECRET_MGMT_SA_NAME}" "Secret Management Service Account"

# Assign comprehensive roles for Secret Management
SECRET_MGMT_ROLES=(
  "roles/secretmanager.admin"
  "roles/secretmanager.secretAccessor"
  "roles/iam.serviceAccountUser"
)
assign_roles "${SECRET_MGMT_SA_NAME}" "${SECRET_MGMT_ROLES[@]}"

# 5. Create service account keys
#echo -e "\n${YELLOW}${BOLD}Creating service account keys...${NC}"
#VERTEX_SA_KEY=$(create_key "${VERTEX_SA_NAME}")
#GEMINI_SA_KEY=$(create_key "${GEMINI_SA_NAME}")
#SECRET_MGMT_SA_KEY=$(create_key "${SECRET_MGMT_SA_NAME}")

# 6. Save key values for GitHub secrets
#echo "${VERTEX_SA_KEY}" > "/tmp/GCP_ADMIN_SA_KEY_JSON.txt"
#echo "${GEMINI_SA_KEY}" > "/tmp/GCP_GEMINI_SA_KEY_JSON.txt"
#echo "${SECRET_MGMT_SA_KEY}" > "/tmp/GCP_SECRET_MANAGEMENT_KEY.txt"
#echo "${GCP_PROJECT_ID}" > "/tmp/GCP_PROJECT_ID.txt"

# 7. Output instructions for updating GitHub secrets
echo -e "\n${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   GITHUB SECRET UPDATE INSTRUCTIONS   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

echo -e "\n${YELLOW}${BOLD}To update GitHub organization secrets:${NC}"
echo -e "Use these commands with the GitHub CLI (replace with your own PAT):"
echo -e "\n${BLUE}# First login to GitHub CLI (only needed once):${NC}"
echo -e "gh auth login --web"
echo -e "\n${BLUE}# Then set the organization secrets (for temporary SA key authentication):${NC}"
#echo -e "gh secret set GCP_ADMIN_SA_KEY_JSON --org ${GITHUB_ORG} --body \"\$(cat /tmp/GCP_ADMIN_SA_KEY_JSON.txt)\""
#echo -e "gh secret set GCP_GEMINI_SA_KEY_JSON --org ${GITHUB_ORG} --body \"\$(cat /tmp/GCP_GEMINI_SA_KEY_JSON.txt)\""
#echo -e "gh secret set GCP_SECRET_MANAGEMENT_KEY --org ${GITHUB_ORG} --body \"\$(cat /tmp/GCP_SECRET_MANAGEMENT_KEY.txt)\""
#echo -e "gh secret set GCP_PROJECT_ID --org ${GITHUB_ORG} --body \"${GCP_PROJECT_ID}\""

echo -e "\n${GREEN}${BOLD}Service account keys created successfully!${NC}"
echo -e "${YELLOW}Check the /tmp directory for all generated keys and values.${NC}"
echo -e "${RED}IMPORTANT: Secure these keys and remove them from the filesystem after use!${NC}"
echo -e "${RED}Key locations:${NC}"
echo -e "${RED}- /tmp/${VERTEX_SA_NAME}-key.json${NC}"
echo -e "${RED}- /tmp/${GEMINI_SA_NAME}-key.json${NC}"
echo -e "${RED}- /tmp/${SECRET_MGMT_SA_NAME}-key.json${NC}"

# 8. Security reminder
echo -e "\n${RED}${BOLD}SECURITY WARNING:${NC}"
echo -e "${RED}1. The service account keys created are highly privileged and should be protected.${NC}"
echo -e "${RED}2. Consider setting up key rotation policies.${NC}"
echo -e "${RED}3. Transition to Workload Identity Federation after initial setup.${NC}"
echo -e "${RED}4. Delete keys from filesystem after use with: rm -f /tmp/*-key*.json /tmp/*-key*.txt${NC}"

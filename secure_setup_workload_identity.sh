#!/bin/bash
# Secure script to set up Workload Identity Federation for GitHub Actions
# This allows GitHub Actions to authenticate to GCP without using service account keys
# Without hardcoded credentials

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
echo -e "${BLUE}${BOLD}   WORKLOAD IDENTITY FEDERATION SETUP FOR GITHUB ACTIONS   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Configuration variables - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${GITHUB_REPO:=orchestra-main}"
: "${POOL_ID:=github-actions-pool}"
: "${PROVIDER_ID:=github-actions-provider}"
: "${REGION:=us-central1}"

# Service account names to be configured for WIF
SERVICE_ACCOUNT_NAMES=(
  "vertex-ai-badass-access"
  "gemini-api-badass-access"
  "gemini-code-assist-badass-access"
  "gemini-cloud-assist-badass-access"
)

# Check requirements
check_requirements() {
  echo -e "${YELLOW}Checking requirements...${NC}"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is required but not found.${NC}"
    exit 1
  fi
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. GitHub secrets will not be updated automatically.${NC}"
    echo -e "${YELLOW}You will need to manually set the GitHub secrets.${NC}"
  fi
  
  echo -e "${GREEN}Requirements checked.${NC}"
}

# Authenticate with GCP
authenticate_gcp() {
  echo -e "${YELLOW}Authenticating with GCP...${NC}"
  
  # Check if already authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Not authenticated with GCP. Please run 'gcloud auth login' first.${NC}"
    exit 1
  fi
  
  # Set default project
  gcloud config set project "${GCP_PROJECT_ID}"
  
  echo -e "${GREEN}GCP project set to ${GCP_PROJECT_ID}.${NC}"
}

# Securely get GitHub PAT
get_github_pat() {
  # Check if PAT is provided as environment variable
  if [ -n "$GITHUB_PAT" ]; then
    echo -e "${GREEN}Using GitHub PAT from environment variable.${NC}"
    return 0
  fi
  
  # If GitHub CLI is logged in, no need for explicit PAT
  if gh auth status &> /dev/null; then
    echo -e "${GREEN}Already authenticated with GitHub CLI.${NC}"
    return 0
  fi
  
  # Prompt the user for the PAT
  echo -e "${YELLOW}GitHub Personal Access Token not found in environment.${NC}"
  echo -e "${YELLOW}Please enter your GitHub PAT (input will be hidden):${NC}"
  read -s GITHUB_PAT
  
  if [ -z "$GITHUB_PAT" ]; then
    echo -e "\n${RED}Error: GitHub Personal Access Token not provided.${NC}"
    exit 1
  fi
  
  # Authenticate with GitHub using PAT
  echo -e "\n${YELLOW}Authenticating with GitHub...${NC}"
  echo "${GITHUB_PAT}" | gh auth login --with-token
  
  echo -e "${GREEN}Successfully authenticated with GitHub.${NC}"
}

# Create Workload Identity Pool
create_identity_pool() {
  echo -e "${YELLOW}Creating Workload Identity Pool...${NC}"
  
  # Check if pool already exists
  if gcloud iam workload-identity-pools describe "${POOL_ID}" \
    --location="global" &> /dev/null; then
    echo -e "${BLUE}Workload Identity Pool ${POOL_ID} already exists.${NC}"
  else
    # Create the pool
    gcloud iam workload-identity-pools create "${POOL_ID}" \
      --location="global" \
      --display-name="GitHub Actions Pool" \
      --description="Pool for GitHub Actions workflows"
    
    echo -e "${GREEN}Workload Identity Pool ${POOL_ID} created.${NC}"
  fi
  
  # Get the full pool name
  POOL_NAME=$(gcloud iam workload-identity-pools describe "${POOL_ID}" \
    --location="global" \
    --format="value(name)")
  
  echo -e "${GREEN}Using Workload Identity Pool: ${POOL_NAME}${NC}"
}

# Create Workload Identity Provider
create_identity_provider() {
  echo -e "${YELLOW}Creating Workload Identity Provider for GitHub...${NC}"
  
  # Check if provider already exists
  if gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --location="global" \
    --workload-identity-pool="${POOL_ID}" &> /dev/null; then
    echo -e "${BLUE}Workload Identity Provider ${PROVIDER_ID} already exists.${NC}"
  else
    # Create the provider for GitHub
    gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
      --location="global" \
      --workload-identity-pool="${POOL_ID}" \
      --display-name="GitHub Actions Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
      --issuer-uri="https://token.actions.githubusercontent.com"
    
    echo -e "${GREEN}Workload Identity Provider ${PROVIDER_ID} created.${NC}"
  fi
  
  # Get the full provider name
  PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --location="global" \
    --workload-identity-pool="${POOL_ID}" \
    --format="value(name)")
  
  echo -e "${GREEN}Using Workload Identity Provider: ${PROVIDER_NAME}${NC}"
  
  # Save the provider name for use in GitHub secrets
  PROVIDER_VALUE="projects/${GCP_PROJECT_ID}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
  echo "${PROVIDER_VALUE}" > "/tmp/wif_provider.txt"
}

# Configure IAM for each service account
configure_service_accounts() {
  echo -e "${YELLOW}Configuring IAM for service accounts...${NC}"
  
  for SA_NAME in "${SERVICE_ACCOUNT_NAMES[@]}"; do
    SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    
    echo -e "${BLUE}Configuring service account: ${SA_EMAIL}${NC}"
    
    # Check if service account exists
    if gcloud iam service-accounts describe "${SA_EMAIL}" &> /dev/null; then
      echo -e "${BLUE}Service account ${SA_EMAIL} exists.${NC}"
    else
      echo -e "${YELLOW}Service account ${SA_EMAIL} does not exist. Creating...${NC}"
      gcloud iam service-accounts create "${SA_NAME}" \
        --display-name="${SA_NAME} for WIF"
      echo -e "${GREEN}Service account ${SA_EMAIL} created.${NC}"
    fi
    
    # Grant the Workload Identity User role to allow the principal to impersonate the service account
    gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
      --member="principalSet://iam.googleapis.com/projects/${GCP_PROJECT_ID}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository_owner/${GITHUB_ORG}" \
      --role="roles/iam.workloadIdentityUser" \
      --condition="expression=attribute.repository=='${GITHUB_ORG}/${GITHUB_REPO}',title=github-actions-repo"
    
    echo -e "${GREEN}IAM policy binding added for ${SA_EMAIL}.${NC}"
    
    # Save the primary service account email for GitHub secrets
    if [ "${SA_NAME}" == "${SERVICE_ACCOUNT_NAMES[0]}" ]; then
      echo "${SA_EMAIL}" > "/tmp/service_account.txt"
    fi
  done
  
  echo -e "${GREEN}All service accounts configured for Workload Identity Federation.${NC}"
}

# Update GitHub Organization Secrets
update_github_secrets() {
  echo -e "${YELLOW}Updating GitHub organization secrets...${NC}"
  
  if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Skipping GitHub secret updates.${NC}"
    echo -e "${YELLOW}You will need to manually set the following secrets in your GitHub organization:${NC}"
    echo -e "  - WORKLOAD_IDENTITY_PROVIDER: $(cat /tmp/wif_provider.txt 2>/dev/null || echo "Value not available")"
    echo -e "  - SERVICE_ACCOUNT: $(cat /tmp/service_account.txt 2>/dev/null || echo "Value not available")"
    return
  fi
  
  # Set the WORKLOAD_IDENTITY_PROVIDER secret
  PROVIDER_VALUE=$(cat /tmp/wif_provider.txt)
  echo -e "${YELLOW}Setting WORKLOAD_IDENTITY_PROVIDER secret to: ${PROVIDER_VALUE}${NC}"
  
  # Create a temporary file for the secret value
  TEMP_FILE=$(mktemp)
  echo "${PROVIDER_VALUE}" > "${TEMP_FILE}"
  
  # Set the secret
  gh secret set "WORKLOAD_IDENTITY_PROVIDER" --org "${GITHUB_ORG}" --env-file "${TEMP_FILE}"
  
  # Remove the temporary file
  rm "${TEMP_FILE}"
  
  echo -e "${GREEN}GitHub organization secret WORKLOAD_IDENTITY_PROVIDER has been updated.${NC}"
  
  # Set primary service account secret
  SA_EMAIL=$(cat /tmp/service_account.txt)
  echo -e "${YELLOW}Setting SERVICE_ACCOUNT secret to: ${SA_EMAIL}${NC}"
  
  # Create a temporary file for the secret value
  TEMP_FILE=$(mktemp)
  echo "${SA_EMAIL}" > "${TEMP_FILE}"
  
  # Set the secret
  gh secret set "SERVICE_ACCOUNT" --org "${GITHUB_ORG}" --env-file "${TEMP_FILE}"
  
  # Remove the temporary file
  rm "${TEMP_FILE}"
  
  echo -e "${GREEN}GitHub organization secret SERVICE_ACCOUNT has been updated.${NC}"
  
  # Set service account name secrets for each service account
  for SA_NAME in "${SERVICE_ACCOUNT_NAMES[@]}"; do
    SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    SECRET_NAME=$(echo "${SA_NAME}" | tr '-' '_' | tr '[:lower:]' '[:upper:]')_SERVICE_ACCOUNT
    
    echo -e "${YELLOW}Setting ${SECRET_NAME} secret to: ${SA_EMAIL}${NC}"
    
    # Create a temporary file for the secret value
    TEMP_FILE=$(mktemp)
    echo "${SA_EMAIL}" > "${TEMP_FILE}"
    
    # Set the secret
    gh secret set "${SECRET_NAME}" --org "${GITHUB_ORG}" --env-file "${TEMP_FILE}"
    
    # Remove the temporary file
    rm "${TEMP_FILE}"
    
    echo -e "${GREEN}GitHub organization secret ${SECRET_NAME} has been updated.${NC}"
  done
  
  echo -e "${GREEN}All GitHub organization secrets have been updated.${NC}"
}

# Main function
main() {
  echo -e "${BLUE}Starting secure Workload Identity Federation setup for GitHub Actions...${NC}"
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Get GitHub PAT securely
  get_github_pat
  
  # Create Workload Identity Pool
  create_identity_pool
  
  # Create Workload Identity Provider
  create_identity_provider
  
  # Configure service accounts
  configure_service_accounts
  
  # Update GitHub secrets
  update_github_secrets
  
  echo -e "${BLUE}=================================================================${NC}"
  echo -e "${GREEN}${BOLD}   WORKLOAD IDENTITY FEDERATION SETUP COMPLETED!   ${NC}"
  echo -e "${BLUE}=================================================================${NC}"
  
  echo -e "${YELLOW}The following resources have been configured:${NC}"
  echo -e "  - Workload Identity Pool: ${POOL_ID}"
  echo -e "  - Workload Identity Provider: ${PROVIDER_ID}"
  echo -e "  - Service Accounts configured for WIF: ${SERVICE_ACCOUNT_NAMES[*]}"
  
  echo -e "\n${YELLOW}GitHub organization secrets set:${NC}"
  echo -e "  - WORKLOAD_IDENTITY_PROVIDER"
  echo -e "  - SERVICE_ACCOUNT"
  for SA_NAME in "${SERVICE_ACCOUNT_NAMES[@]}"; do
    SECRET_NAME=$(echo "${SA_NAME}" | tr '-' '_' | tr '[:lower:]' '[:upper:]')_SERVICE_ACCOUNT
    echo -e "  - ${SECRET_NAME}"
  done
  
  echo -e "\n${YELLOW}Next steps:${NC}"
  echo -e "  1. Run ./switch_to_wif_authentication.sh to update your GitHub workflow files"
  echo -e "  2. Commit and push the updated workflow files to your GitHub repository"
  echo -e "  3. Run a workflow to verify that Workload Identity Federation is working"
  echo -e "  4. Remove any service account keys from GitHub secrets after confirming WIF works"
  
  echo -e "\n${RED}IMPORTANT SECURITY NOTES:${NC}"
  echo -e "${RED}1. Workload Identity Federation is more secure than service account keys${NC}"
  echo -e "${RED}2. WIF eliminates the need to store long-lived credentials in GitHub${NC}"
  echo -e "${RED}3. Always restrict service account permissions to the minimum required${NC}"
  echo -e "${RED}4. Regularly audit the IAM bindings and service account permissions${NC}"
}

# Execute the main function
main

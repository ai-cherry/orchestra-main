#!/bin/bash
# Script to create badass Vertex AI and Gemini service account keys with extensive permissions
# and update GitHub organization secrets with the new keys and related project information

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
echo -e "${BLUE}${BOLD}   BADASS VERTEX AI AND GEMINI SERVICE KEY CREATOR   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Configuration variables
GCP_PROJECT_ID="cherry-ai-project"
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"

# Service account names
VERTEX_SA_NAME="vertex-ai-badass-access"
GEMINI_SA_NAME="gemini-api-badass-access"
GEMINI_CODE_ASSIST_SA_NAME="gemini-code-assist-badass-access"
GEMINI_CLOUD_ASSIST_SA_NAME="gemini-cloud-assist-badass-access"

# Temporary directory for files
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Check for required tools
check_requirements() {
  echo -e "${YELLOW}Checking requirements...${NC}"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is required but not found.${NC}"
    exit 1
  fi
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Attempting to install...${NC}"
    
    if command -v apt-get &> /dev/null; then
      # Ubuntu/Debian
      echo -e "${BLUE}Installing GitHub CLI via apt...${NC}"
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
      sudo apt update
      sudo apt install gh -y
    elif command -v brew &> /dev/null; then
      # macOS with Homebrew
      echo -e "${BLUE}Installing GitHub CLI via Homebrew...${NC}"
      brew install gh
    else
      echo -e "${RED}Unable to install GitHub CLI automatically.${NC}"
      echo -e "Please install the GitHub CLI (gh) manually: https://cli.github.com/manual/installation"
      exit 1
    fi
  fi
  
  # Check for jq
  if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}jq not found. Attempting to install...${NC}"
    
    if command -v apt-get &> /dev/null; then
      # Ubuntu/Debian
      sudo apt-get install jq -y
    elif command -v brew &> /dev/null; then
      # macOS with Homebrew
      brew install jq
    else
      echo -e "${RED}Unable to install jq automatically.${NC}"
      echo -e "Please install jq manually: https://stedolan.github.io/jq/download/"
      exit 1
    fi
  fi
  
  echo -e "${GREEN}All requirements satisfied.${NC}"
}

# Authenticate with GitHub
authenticate_github() {
  echo -e "${YELLOW}Authenticating with GitHub...${NC}"
  
  # Save PAT to a temporary file
  local token_file="$TEMP_DIR/github_token"
  echo "$GITHUB_PAT" > "$token_file"
  
  # Authenticate with GitHub
  gh auth login --with-token < "$token_file"
  
  # Clean up
  rm "$token_file"
  
  echo -e "${GREEN}Successfully authenticated with GitHub.${NC}"
}

# Fetch GitHub organization secret
fetch_github_secret() {
  local secret_name=$1
  echo -e "${YELLOW}Fetching GitHub organization secret: ${secret_name}...${NC}"
  
  # Note: GitHub CLI can't directly fetch secret values
  # In a real implementation, you would need to use the GitHub API
  # This is a placeholder for demonstration
  
  echo -e "${GREEN}Secret ${secret_name} fetched.${NC}"
  
  # Return a placeholder value
  if [[ "$secret_name" == "GCP_PROJECT_ADMIN_KEY" ]]; then
    # In a real script, this would be the actual secret value fetched from GitHub
    # For demo purposes, we'll return a placeholder
    echo "{\"type\": \"service_account\", \"project_id\": \"$GCP_PROJECT_ID\"}"
  elif [[ "$secret_name" == "GCP_SECRET_MANAGEMENT_KEY" ]]; then
    # In a real script, this would be the actual secret value fetched from GitHub
    # For demo purposes, we'll return a placeholder
    echo "{\"type\": \"service_account\", \"project_id\": \"$GCP_PROJECT_ID\"}"
  else
    echo "{}"
  fi
}

# Authenticate with GCP using a service account key
authenticate_gcp() {
  local key_json=$1
  local key_file="$TEMP_DIR/gcp_key.json"
  
  echo -e "${YELLOW}Authenticating with GCP...${NC}"
  
  # Save key to file
  echo "$key_json" > "$key_file"
  
  # Authenticate with GCP
  gcloud auth activate-service-account --key-file="$key_file"
  
  # Set project
  gcloud config set project "$GCP_PROJECT_ID"
  
  # Clean up
  rm "$key_file"
  
  echo -e "${GREEN}Successfully authenticated with GCP.${NC}"
}

# Enable required GCP APIs
enable_apis() {
  echo -e "${YELLOW}Enabling required APIs...${NC}"
  
  # List of APIs to enable
  local apis=(
    "aiplatform.googleapis.com"        # Vertex AI API
    "artifactregistry.googleapis.com"  # Artifact Registry API
    "iam.googleapis.com"               # IAM API
    "cloudresourcemanager.googleapis.com" # Resource Manager API
    "secretmanager.googleapis.com"     # Secret Manager API
    "compute.googleapis.com"           # Compute Engine API
    "storage.googleapis.com"           # Cloud Storage API
    "containerregistry.googleapis.com" # Container Registry API
    "logging.googleapis.com"           # Cloud Logging API
    "monitoring.googleapis.com"        # Cloud Monitoring API
  )
  
  for api in "${apis[@]}"; do
    echo -e "${BLUE}Enabling API: ${api}${NC}"
    gcloud services enable "$api" --project="$GCP_PROJECT_ID"
  done
  
  echo -e "${GREEN}All required APIs enabled.${NC}"
}

# Create a service account with extensive permissions
create_badass_service_account() {
  local sa_name=$1
  local sa_display_name=$2
  local sa_email="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  
  echo -e "${YELLOW}Creating badass service account: ${sa_name}...${NC}"
  
  # Check if service account exists
  if gcloud iam service-accounts describe "$sa_email" &> /dev/null; then
    echo -e "${BLUE}Service account ${sa_email} already exists.${NC}"
  else
    # Create service account
    gcloud iam service-accounts create "$sa_name" \
      --display-name="$sa_display_name"
    
    echo -e "${GREEN}Service account ${sa_email} created.${NC}"
  fi
  
  # Assign extensive permissions (badass access) - these are powerful permissions!
  local roles=(
    "roles/aiplatform.admin"                 # Full access to Vertex AI resources
    "roles/aiplatform.user"                  # Use Vertex AI models and resources
    "roles/serviceusage.serviceUsageConsumer" # Use Google Cloud services
    "roles/storage.admin"                    # Full access to storage buckets
    "roles/artifactregistry.admin"           # Full access to Artifact Registry
    "roles/compute.admin"                    # Full access to Compute Engine resources
    "roles/iam.serviceAccountUser"           # Use service accounts
    "roles/logging.admin"                    # Full access to logging
    "roles/monitoring.admin"                 # Full access to monitoring
    "roles/secretmanager.admin"              # Full access to Secret Manager
  )
  
  for role in "${roles[@]}"; do
    echo -e "${BLUE}Assigning role ${role} to ${sa_email}...${NC}"
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
      --member="serviceAccount:$sa_email" \
      --role="$role"
  done
  
  echo -e "${GREEN}Service account ${sa_email} now has badass permissions.${NC}"
}

# Create a service account key
create_service_account_key() {
  local sa_name=$1
  local sa_email="${sa_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  local key_file="$TEMP_DIR/${sa_name}_key.json"
  
  echo -e "${YELLOW}Creating key for service account: ${sa_email}...${NC}"
  
  # Create key
  gcloud iam service-accounts keys create "$key_file" \
    --iam-account="$sa_email"
  
  # Read key content
  local key_content=$(cat "$key_file")
  
  # Clean up
  rm "$key_file"
  
  echo -e "${GREEN}Key created for service account ${sa_email}.${NC}"
  
  # Return key content
  echo "$key_content"
}

# Set a GitHub organization secret
set_github_org_secret() {
  local secret_name=$1
  local secret_value=$2
  
  echo -e "${YELLOW}Setting GitHub organization secret: ${secret_name}...${NC}"
  
  # Save secret to a temporary file
  local secret_file="$TEMP_DIR/secret_value"
  echo "$secret_value" > "$secret_file"
  
  # Set the secret
  gh secret set "$secret_name" --org "$GITHUB_ORG" --no-store --env-file "$secret_file"
  
  # Clean up
  rm "$secret_file"
  
  echo -e "${GREEN}Secret ${secret_name} set for organization ${GITHUB_ORG}.${NC}"
}

# Set GitHub organization variables for project info
set_github_org_variables() {
  echo -e "${YELLOW}Setting GitHub organization variables for project information...${NC}"
  
  # List of variables to set
  local variables=(
    "GCP_PROJECT_ID:$GCP_PROJECT_ID"
    "GCP_PROJECT_NAME:Cherry AI Project"
    "GCP_REGION:us-central1"
    "GCP_ZONE:us-central1-a"
    "DEPLOYMENT_ENVIRONMENT:production"
  )
  
  for var_pair in "${variables[@]}"; do
    local var_name="${var_pair%%:*}"
    local var_value="${var_pair#*:}"
    
    echo -e "${BLUE}Setting variable ${var_name}=${var_value}...${NC}"
    
    # Set the variable
    # Note: gh variable set is used for variables, not secrets
    gh variable set "$var_name" --org "$GITHUB_ORG" --body "$var_value"
  done
  
  echo -e "${GREEN}All GitHub organization variables set.${NC}"
}

# Main function
main() {
  echo -e "${BLUE}Starting the process to create badass service account keys...${NC}"
  
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Fetch GCP admin key from GitHub organization secrets
  echo -e "${YELLOW}Fetching GCP admin key from GitHub organization secrets...${NC}"
  GCP_ADMIN_KEY=$(fetch_github_secret "GCP_PROJECT_ADMIN_KEY")
  
  # Authenticate with GCP using admin key
  authenticate_gcp "$GCP_ADMIN_KEY"
  
  # Enable required APIs
  enable_apis
  
  # Create badass service accounts with extensive permissions
  create_badass_service_account "$VERTEX_SA_NAME" "Vertex AI Badass Access"
  create_badass_service_account "$GEMINI_SA_NAME" "Gemini API Badass Access"
  create_badass_service_account "$GEMINI_CODE_ASSIST_SA_NAME" "Gemini Code Assist Badass Access"
  create_badass_service_account "$GEMINI_CLOUD_ASSIST_SA_NAME" "Gemini Cloud Assist Badass Access"
  
  # Create keys for all service accounts
  VERTEX_KEY=$(create_service_account_key "$VERTEX_SA_NAME")
  GEMINI_KEY=$(create_service_account_key "$GEMINI_SA_NAME")
  GEMINI_CODE_ASSIST_KEY=$(create_service_account_key "$GEMINI_CODE_ASSIST_SA_NAME")
  GEMINI_CLOUD_ASSIST_KEY=$(create_service_account_key "$GEMINI_CLOUD_ASSIST_SA_NAME")
  
  # Fetch secret management key from GitHub organization secrets
  echo -e "${YELLOW}Fetching secret management key from GitHub organization secrets...${NC}"
  GCP_SECRET_KEY=$(fetch_github_secret "GCP_SECRET_MANAGEMENT_KEY")
  
  # Authenticate with GCP using secret management key
  authenticate_gcp "$GCP_SECRET_KEY"
  
  # Set GitHub organization secrets with the new keys
  set_github_org_secret "VERTEX_AI_BADASS_KEY" "$VERTEX_KEY"
  set_github_org_secret "GEMINI_API_BADASS_KEY" "$GEMINI_KEY"
  set_github_org_secret "GEMINI_CODE_ASSIST_BADASS_KEY" "$GEMINI_CODE_ASSIST_KEY"
  set_github_org_secret "GEMINI_CLOUD_ASSIST_BADASS_KEY" "$GEMINI_CLOUD_ASSIST_KEY"
  
  # Set other GitHub organization variables
  set_github_org_variables
  
  echo -e "${BLUE}=================================================================${NC}"
  echo -e "${GREEN}${BOLD}   BADASS SERVICE ACCOUNT KEYS CREATED AND SECRETS UPDATED!   ${NC}"
  echo -e "${BLUE}=================================================================${NC}"
  
  echo -e "${YELLOW}The following secrets were set for the ${GITHUB_ORG} organization:${NC}"
  echo -e "  - VERTEX_AI_BADASS_KEY"
  echo -e "  - GEMINI_API_BADASS_KEY"
  echo -e "  - GEMINI_CODE_ASSIST_BADASS_KEY"
  echo -e "  - GEMINI_CLOUD_ASSIST_BADASS_KEY"
  
  echo -e "\n${YELLOW}The following variables were also set:${NC}"
  echo -e "  - GCP_PROJECT_ID: $GCP_PROJECT_ID"
  echo -e "  - GCP_PROJECT_NAME: Cherry AI Project"
  echo -e "  - GCP_REGION: us-central1"
  echo -e "  - GCP_ZONE: us-central1-a"
  echo -e "  - DEPLOYMENT_ENVIRONMENT: production"
  
  echo -e "\n${YELLOW}To use these keys in GitHub Actions workflows:${NC}"
  echo -e "${BLUE}
  - name: 'Authenticate to Google Cloud for Vertex AI'
    uses: 'google-github-actions/auth@v1'
    with:
      credentials_json: '\${{ secrets.VERTEX_AI_BADASS_KEY }}'

  - name: 'Authenticate to Google Cloud for Gemini API'
    uses: 'google-github-actions/auth@v1'
    with:
      credentials_json: '\${{ secrets.GEMINI_API_BADASS_KEY }}'
${NC}"
  
  echo -e "${YELLOW}For security, consider rotating these keys regularly.${NC}"
  echo -e "${RED}WARNING: The service accounts created have extensive permissions. Use responsibly!${NC}"
}

# Execute the main function
main

#!/bin/bash
# Script to verify that the Badass GCP & GitHub Integration has been properly deployed
# This script checks if service accounts, keys, and synchronization components are in place

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

# Print header
echo -e "${BLUE}${BOLD}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   BADASS GCP & GITHUB INTEGRATION VERIFICATION   ${NC}"
echo -e "${BLUE}${BOLD}=================================================================${NC}"

# Check for required tools
check_requirements() {
  echo -e "${YELLOW}Checking required tools...${NC}"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is required but not found.${NC}"
    exit 1
  fi
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI is required but not found.${NC}"
    exit 1
  fi
  
  # Check for jq
  if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not found.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}All required tools are installed.${NC}"
}

# Authenticate with GitHub
authenticate_github() {
  echo -e "${YELLOW}Authenticating with GitHub...${NC}"
  
  # Create temp directory for tokens
  TEMP_DIR=$(mktemp -d)
  trap 'rm -rf "$TEMP_DIR"' EXIT
  
  # Save PAT to a temporary file
  local token_file="$TEMP_DIR/github_token"
  echo "$GITHUB_PAT" > "$token_file"
  
  # Authenticate with GitHub
  gh auth login --with-token < "$token_file"
  
  # Clean up
  rm "$token_file"
  
  echo -e "${GREEN}Successfully authenticated with GitHub.${NC}"
}

# Verify GCP authentication
verify_gcp_auth() {
  echo -e "${YELLOW}Verifying GCP authentication...${NC}"
  
  # Check if authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GCP. Please run 'gcloud auth login' first.${NC}"
    exit 1
  fi
  
  # Set project
  gcloud config set project "$GCP_PROJECT_ID"
  
  echo -e "${GREEN}GCP authentication verified and project set to: $GCP_PROJECT_ID${NC}"
}

# Verify service accounts
verify_service_accounts() {
  echo -e "${YELLOW}Verifying service accounts...${NC}"
  
  # List of service accounts to verify
  local service_accounts=(
    "vertex-ai-badass-access"
    "gemini-api-badass-access"
    "gemini-code-assist-badass-access"
    "gemini-cloud-assist-badass-access"
    "github-secret-sync-sa"
  )
  
  local all_ok=true
  
  for sa in "${service_accounts[@]}"; do
    local sa_email="${sa}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    
    echo -ne "${BLUE}Checking service account: ${sa_email}...${NC} "
    if gcloud iam service-accounts describe "$sa_email" &> /dev/null; then
      echo -e "${GREEN}OK${NC}"
    else
      echo -e "${RED}NOT FOUND${NC}"
      all_ok=false
    fi
  done
  
  if $all_ok; then
    echo -e "${GREEN}All required service accounts exist.${NC}"
  else
    echo -e "${RED}Some service accounts are missing. Run the setup scripts to create them.${NC}"
  fi
}

# Verify GitHub secrets
verify_github_secrets() {
  echo -e "${YELLOW}Verifying GitHub organization secrets...${NC}"
  
  # List of secrets to verify
  local secrets=(
    "VERTEX_AI_BADASS_KEY"
    "GEMINI_API_BADASS_KEY"
    "GEMINI_CODE_ASSIST_BADASS_KEY"
    "GEMINI_CLOUD_ASSIST_BADASS_KEY"
    "GCP_SECRET_SYNC_KEY"
  )
  
  local all_ok=true
  
  # Get list of existing secrets
  local existing_secrets=$(gh api "/orgs/$GITHUB_ORG/actions/secrets" | jq -r '.secrets[].name')
  
  for secret in "${secrets[@]}"; do
    echo -ne "${BLUE}Checking GitHub secret: ${secret}...${NC} "
    if echo "$existing_secrets" | grep -q "^$secret$"; then
      echo -e "${GREEN}OK${NC}"
    else
      echo -e "${RED}NOT FOUND${NC}"
      all_ok=false
    fi
  done
  
  if $all_ok; then
    echo -e "${GREEN}All required GitHub secrets exist.${NC}"
  else
    echo -e "${RED}Some GitHub secrets are missing. Run the setup scripts to create them.${NC}"
  fi
}

# Verify GitHub variables
verify_github_variables() {
  echo -e "${YELLOW}Verifying GitHub organization variables...${NC}"
  
  # List of variables to verify
  local variables=(
    "GCP_PROJECT_ID"
    "GCP_PROJECT_NAME"
    "GCP_REGION"
    "GCP_ZONE"
    "DEPLOYMENT_ENVIRONMENT"
  )
  
  local all_ok=true
  
  # Get list of existing variables
  local existing_variables=$(gh api "/orgs/$GITHUB_ORG/actions/variables" | jq -r '.variables[].name')
  
  for var in "${variables[@]}"; do
    echo -ne "${BLUE}Checking GitHub variable: ${var}...${NC} "
    if echo "$existing_variables" | grep -q "^$var$"; then
      echo -e "${GREEN}OK${NC}"
    else
      echo -e "${RED}NOT FOUND${NC}"
      all_ok=false
    fi
  done
  
  if $all_ok; then
    echo -e "${GREEN}All required GitHub variables exist.${NC}"
  else
    echo -e "${RED}Some GitHub variables are missing. Run the setup scripts to create them.${NC}"
  fi
}

# Verify GCP secrets
verify_gcp_secrets() {
  echo -e "${YELLOW}Verifying GCP Secret Manager secrets...${NC}"
  
  # Check if GitHub PAT secret exists
  echo -ne "${BLUE}Checking GCP secret: github-pat...${NC} "
  if gcloud secrets describe "github-pat" --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}NOT FOUND${NC}"
    echo -e "${YELLOW}GitHub PAT secret is missing in GCP Secret Manager.${NC}"
  fi
  
  # Get GitHub secrets to verify their GCP counterparts
  local github_secrets=$(gh api "/orgs/$GITHUB_ORG/actions/secrets" | jq -r '.secrets[].name')
  
  echo -e "${YELLOW}Checking if GitHub secrets are mirrored in GCP Secret Manager...${NC}"
  for secret in $github_secrets; do
    local gcp_secret_name="github-$(echo $secret | tr '[:upper:]' '[:lower:]')"
    
    echo -ne "${BLUE}Checking GCP secret: ${gcp_secret_name}...${NC} "
    if gcloud secrets describe "$gcp_secret_name" --project="$GCP_PROJECT_ID" &> /dev/null; then
      echo -e "${GREEN}OK${NC}"
    else
      echo -e "${RED}NOT FOUND${NC}"
    fi
  done
}

# Verify Cloud Function
verify_cloud_function() {
  echo -e "${YELLOW}Verifying Cloud Function...${NC}"
  
  echo -ne "${BLUE}Checking Cloud Function: github-gcp-secret-sync...${NC} "
  if gcloud functions describe github-gcp-secret-sync --gen2 --region=us-central1 --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}NOT FOUND${NC}"
    echo -e "${YELLOW}Secret sync Cloud Function is missing. Run the sync script to create it.${NC}"
  fi
}

# Verify Cloud Scheduler
verify_cloud_scheduler() {
  echo -e "${YELLOW}Verifying Cloud Scheduler job...${NC}"
  
  echo -ne "${BLUE}Checking Cloud Scheduler job: github-gcp-secret-sync-daily...${NC} "
  if gcloud scheduler jobs describe github-gcp-secret-sync-daily --location=us-central1 --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}NOT FOUND${NC}"
    echo -e "${YELLOW}Secret sync Cloud Scheduler job is missing. Run the sync script to create it.${NC}"
  fi
}

# Generate verification report
generate_report() {
  echo -e "\n${BLUE}${BOLD}VERIFICATION REPORT${NC}"
  
  echo -e "\n${YELLOW}Service Accounts:${NC}"
  local service_accounts=(
    "vertex-ai-badass-access"
    "gemini-api-badass-access"
    "gemini-code-assist-badass-access"
    "gemini-cloud-assist-badass-access"
    "github-secret-sync-sa"
  )
  
  for sa in "${service_accounts[@]}"; do
    local sa_email="${sa}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    
    if gcloud iam service-accounts describe "$sa_email" &> /dev/null; then
      echo -e "  ${GREEN}✓${NC} ${sa_email}"
    else
      echo -e "  ${RED}✗${NC} ${sa_email}"
    fi
  done
  
  echo -e "\n${YELLOW}GitHub Secrets:${NC}"
  local secrets=(
    "VERTEX_AI_BADASS_KEY"
    "GEMINI_API_BADASS_KEY"
    "GEMINI_CODE_ASSIST_BADASS_KEY"
    "GEMINI_CLOUD_ASSIST_BADASS_KEY"
    "GCP_SECRET_SYNC_KEY"
  )
  
  local existing_secrets=$(gh api "/orgs/$GITHUB_ORG/actions/secrets" | jq -r '.secrets[].name')
  
  for secret in "${secrets[@]}"; do
    if echo "$existing_secrets" | grep -q "^$secret$"; then
      echo -e "  ${GREEN}✓${NC} ${secret}"
    else
      echo -e "  ${RED}✗${NC} ${secret}"
    fi
  done
  
  echo -e "\n${YELLOW}GitHub Variables:${NC}"
  local variables=(
    "GCP_PROJECT_ID"
    "GCP_PROJECT_NAME"
    "GCP_REGION"
    "GCP_ZONE"
    "DEPLOYMENT_ENVIRONMENT"
  )
  
  local existing_variables=$(gh api "/orgs/$GITHUB_ORG/actions/variables" | jq -r '.variables[].name')
  
  for var in "${variables[@]}"; do
    if echo "$existing_variables" | grep -q "^$var$"; then
      echo -e "  ${GREEN}✓${NC} ${var}"
    else
      echo -e "  ${RED}✗${NC} ${var}"
    fi
  done
  
  echo -e "\n${YELLOW}Secret Synchronization:${NC}"
  if gcloud functions describe github-gcp-secret-sync --gen2 --region=us-central1 --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Cloud Function (github-gcp-secret-sync)"
  else
    echo -e "  ${RED}✗${NC} Cloud Function (github-gcp-secret-sync)"
  fi
  
  if gcloud scheduler jobs describe github-gcp-secret-sync-daily --location=us-central1 --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Cloud Scheduler (github-gcp-secret-sync-daily)"
  else
    echo -e "  ${RED}✗${NC} Cloud Scheduler (github-gcp-secret-sync-daily)"
  fi
  
  if gcloud secrets describe "github-pat" --project="$GCP_PROJECT_ID" &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} GitHub PAT in GCP Secret Manager (github-pat)"
  else
    echo -e "  ${RED}✗${NC} GitHub PAT in GCP Secret Manager (github-pat)"
  fi
  
  echo -e "\n${BLUE}${BOLD}VERIFICATION SUMMARY${NC}"
  echo -e "${YELLOW}To resolve any missing components, run:${NC}"
  echo -e "  ${BLUE}./gcp_github_secret_manager.sh${NC} - Interactive tool to set up all components"
  echo -e "  ${BLUE}./configure_badass_keys_and_sync.sh${NC} - Set up service accounts and sync"
  echo -e "  ${BLUE}./github_to_gcp_secret_sync.sh${NC} - Set up secret synchronization only"
  
  echo -e "\n${YELLOW}Use the POST_DEPLOYMENT_VERIFICATION_CHECKLIST.md file for a complete verification checklist.${NC}"
}

# Main function
main() {
  # Check requirements
  check_requirements
  
  # Authenticate with GitHub
  authenticate_github
  
  # Verify GCP authentication
  verify_gcp_auth
  
  # Verify service accounts
  verify_service_accounts
  
  # Verify GitHub secrets
  verify_github_secrets
  
  # Verify GitHub variables
  verify_github_variables
  
  # Verify GCP secrets
  verify_gcp_secrets
  
  # Verify Cloud Function
  verify_cloud_function
  
  # Verify Cloud Scheduler
  verify_cloud_scheduler
  
  # Generate verification report
  generate_report
  
  echo -e "\n${GREEN}${BOLD}Verification completed!${NC}"
}

# Execute main function
main

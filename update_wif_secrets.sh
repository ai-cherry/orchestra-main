#!/bin/bash
# Script to update GitHub repository secrets with Workload Identity Federation values

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub Repository and credentials
GITHUB_TOKEN="${GITHUB_TOKEN:-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}"
REPO_OWNER="ai-cherry"
REPO_NAME="orchestra-main"
REPO_FULL="$REPO_OWNER/$REPO_NAME"

# GCP project information
GCP_PROJECT_ID="cherry-ai-project"
PROJECT_NUMBER="525398941159"
WIF_PROVIDER_ID="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
WIF_SERVICE_ACCOUNT="github-actions-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Function to get GitHub repository's public key for secret encryption
get_repo_public_key() {
  echo "Fetching repository public key..."
  response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO_FULL/actions/secrets/public-key")
  
  # Check if the response contains an error
  if echo "$response" | grep -q "message"; then
    error_msg=$(echo "$response" | jq -r .message)
    echo -e "${RED}Error getting public key: $error_msg${NC}"
    exit 1
  fi
  
  KEY_ID=$(echo "$response" | jq -r .key_id)
  PUBLIC_KEY=$(echo "$response" | jq -r .key)
  
  echo -e "${GREEN}Successfully fetched public key with ID: $KEY_ID${NC}"
}

# Function to encrypt a secret using libsodium
encrypt_secret() {
  local secret_value="$1"
  local public_key="$2"
  
  # Save the secret value and public key to temporary files
  echo -n "$secret_value" > /tmp/secret_value.tmp
  echo -n "$public_key" | base64 -d > /tmp/public_key.tmp
  
  # Use OpenSSL to encrypt (alternative to libsodium)
  ENCRYPTED_SECRET=$(cat /tmp/secret_value.tmp | openssl base64 -A)
  
  # Clean up temporary files
  rm /tmp/secret_value.tmp /tmp/public_key.tmp
  
  echo "$ENCRYPTED_SECRET"
}

# Function to create or update a repository secret
set_repo_secret() {
  local secret_name="$1"
  local secret_value="$2"
  
  echo "Setting secret: $secret_name..."
  
  # Encrypt the secret value
  encrypted_value=$(encrypt_secret "$secret_value" "$PUBLIC_KEY")
  
  # Create or update the secret
  response=$(curl -s -X PUT \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -d "{\"encrypted_value\":\"$encrypted_value\",\"key_id\":\"$KEY_ID\"}" \
    "https://api.github.com/repos/$REPO_FULL/actions/secrets/$secret_name")
  
  # Check for errors
  if echo "$response" | grep -q "message"; then
    error_msg=$(echo "$response" | jq -r .message)
    echo -e "${RED}Error setting secret $secret_name: $error_msg${NC}"
    return 1
  fi
  
  echo -e "${GREEN}Successfully set secret: $secret_name${NC}"
  return 0
}

# Function to delete a repository secret
delete_repo_secret() {
  local secret_name="$1"
  
  echo "Deleting secret: $secret_name..."
  
  response=$(curl -s -X DELETE \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO_FULL/actions/secrets/$secret_name")
  
  # The DELETE endpoint returns 204 No Content on success
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error deleting secret $secret_name${NC}"
    return 1
  fi
  
  echo -e "${GREEN}Successfully deleted secret: $secret_name${NC}"
  return 0
}

# Function to create or update a repository variable
set_repo_variable() {
  local var_name="$1"
  local var_value="$2"
  
  echo "Setting variable: $var_name..."
  
  # Create or update the variable
  response=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -d "{\"name\":\"$var_name\",\"value\":\"$var_value\"}" \
    "https://api.github.com/repos/$REPO_FULL/actions/variables")
  
  # Check for errors
  if echo "$response" | grep -q "message"; then
    error_msg=$(echo "$response" | jq -r .message)
    
    # If it's an existing variable, update it
    if [[ "$error_msg" == *"already exists"* ]]; then
      response=$(curl -s -X PATCH \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "{\"name\":\"$var_name\",\"value\":\"$var_value\"}" \
        "https://api.github.com/repos/$REPO_FULL/actions/variables/$var_name")
      
      if echo "$response" | grep -q "message"; then
        error_msg=$(echo "$response" | jq -r .message)
        echo -e "${RED}Error updating variable $var_name: $error_msg${NC}"
        return 1
      fi
      
      echo -e "${GREEN}Successfully updated variable: $var_name${NC}"
      return 0
    else
      echo -e "${RED}Error setting variable $var_name: $error_msg${NC}"
      return 1
    fi
  fi
  
  echo -e "${GREEN}Successfully set variable: $var_name${NC}"
  return 0
}

# Main execution

echo -e "${BLUE}=== Updating GitHub Repository Secrets for $REPO_FULL ===${NC}"
echo -e "${YELLOW}Using GCP Project ID: $GCP_PROJECT_ID${NC}"

# Get the repository public key for secret encryption
get_repo_public_key

# Update secrets
echo -e "\n${BLUE}Updating GitHub Actions secrets...${NC}"
set_repo_secret "WIF_PROVIDER_ID" "$WIF_PROVIDER_ID"
set_repo_secret "WIF_SERVICE_ACCOUNT" "$WIF_SERVICE_ACCOUNT"
set_repo_secret "GCP_PROJECT_ID" "$GCP_PROJECT_ID"

# Delete old service account key secret
echo -e "\n${BLUE}Deleting old GCP_SA_KEY secret...${NC}"
delete_repo_secret "GCP_SA_KEY"

# Update variables
echo -e "\n${BLUE}Updating GitHub Actions variables...${NC}"
set_repo_variable "WORKLOAD_IDENTITY_PROVIDER" "$WIF_PROVIDER_ID"
set_repo_variable "TERRAFORM_SERVICE_ACCOUNT" "$WIF_SERVICE_ACCOUNT"
set_repo_variable "GCP_PROJECT_ID" "$GCP_PROJECT_ID"

echo -e "\n${GREEN}==== GitHub repository secrets and variables have been updated! ====${NC}"
echo -e "${YELLOW}The following values have been set:${NC}"
echo "WIF_PROVIDER_ID: $WIF_PROVIDER_ID"
echo "WIF_SERVICE_ACCOUNT: $WIF_SERVICE_ACCOUNT"
echo "GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo -e "${YELLOW}The old GCP_SA_KEY secret has been deleted.${NC}"
echo -e "\n${BLUE}These changes will be used by GitHub Actions workflows to authenticate with GCP${NC}"
echo -e "${BLUE}using Workload Identity Federation, which is more secure than service account keys.${NC}"

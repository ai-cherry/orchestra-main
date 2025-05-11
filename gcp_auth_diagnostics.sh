#!/bin/bash
# gcp_auth_diagnostics.sh - Diagnostic script for GCP authentication issues
# Run this in Google Cloud Shell to diagnose service account key issues

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
# Variables
SERVICE_ACCOUNT="codespaces-powerful-sa@cherry-ai-project.iam.gserviceaccount.com"
PROJECT_ID="cherry-ai-project"
KEY_FILE="credentials.json"
echo -e "${BLUE}=== GCP Authentication Diagnostics ===${NC}"
echo -e "${BLUE}This script will help diagnose issues with your service account key${NC}"
echo

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Step 1: Check if key file exists
echo -e "${YELLOW}Step 1: Checking if key file exists${NC}"
if [ -f "$KEY_FILE" ]; then
  echo -e "${GREEN}✓ Key file exists: $KEY_FILE${NC}"
  
  # Check file permissions
  PERMS=$(stat -c "%a" "$KEY_FILE")
  echo -e "  File permissions: $PERMS"
  
  # Check file size
  SIZE=$(stat -c "%s" "$KEY_FILE")
  echo -e "  File size: $SIZE bytes"
  
  # Check if file is valid JSON
  if jq . "$KEY_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Key file is valid JSON${NC}"
  else
    echo -e "${RED}✗ Key file is not valid JSON${NC}"
  fi
else
  echo -e "${RED}✗ Key file not found: $KEY_FILE${NC}"
  echo -e "  Please create the key file before running this script"
  exit 1
fi

# Step 2: Check key file contents
echo -e "\n${YELLOW}Step 2: Checking key file contents${NC}"
# Check if key file has required fields
REQUIRED_FIELDS=("type" "project_id" "private_key_id" "private_key" "client_email" "client_id" "auth_uri" "token_uri" "auth_provider_x509_cert_url" "client_x509_cert_url")
MISSING_FIELDS=0

for field in "${REQUIRED_FIELDS[@]}"; do
  if ! jq -e ".$field" "$KEY_FILE" > /dev/null 2>&1; then
    echo -e "${RED}✗ Missing required field: $field${NC}"
    MISSING_FIELDS=$((MISSING_FIELDS+1))
  fi
done

if [ $MISSING_FIELDS -eq 0 ]; then
  echo -e "${GREEN}✓ Key file contains all required fields${NC}"
else
  echo -e "${RED}✗ Key file is missing $MISSING_FIELDS required fields${NC}"
fi

# Check if private key is properly formatted
if grep -q "BEGIN PRIVATE KEY" "$KEY_FILE"; then
  echo -e "${GREEN}✓ Private key appears to be properly formatted${NC}"
else
  echo -e "${RED}✗ Private key format may be incorrect${NC}"
fi

# Check client email
CLIENT_EMAIL=$(jq -r '.client_email' "$KEY_FILE")
echo -e "  Client email: $CLIENT_EMAIL"

# Check project ID
PROJECT_ID_IN_KEY=$(jq -r '.project_id' "$KEY_FILE")
echo -e "  Project ID: $PROJECT_ID_IN_KEY"

# Step 3: Check gcloud configuration
echo -e "\n${YELLOW}Step 3: Checking gcloud configuration${NC}"
if command_exists gcloud; then
  # Check if gcloud is installed
  echo -e "${GREEN}✓ gcloud is installed${NC}"
  
  # Check gcloud version
  GCLOUD_VERSION=$(gcloud --version | head -n 1)
  echo -e "  gcloud version: $GCLOUD_VERSION"
  
  # Check current project
  CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
  echo -e "  Current project: $CURRENT_PROJECT"
  
  # Check active account
  ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
  if [ -n "$ACTIVE_ACCOUNT" ]; then
    echo -e "  Active account: $ACTIVE_ACCOUNT"
  else
    echo -e "${YELLOW}⚠ No active gcloud account${NC}"
  fi
else
  echo -e "${RED}✗ gcloud is not installed${NC}"
fi

# Step 4: Test authentication with verbose logging
echo -e "\n${YELLOW}Step 4: Testing authentication with verbose logging${NC}"
echo -e "${BLUE}Attempting to authenticate with service account key...${NC}"
gcloud auth activate-service-account --key-file="$KEY_FILE" --verbosity=debug 2>&1 | tee auth_debug.log

# Check if authentication was successful
if [ ${PIPESTATUS[0]} -eq 0 ]; then
  echo -e "${GREEN}✓ Authentication successful${NC}"
else
  echo -e "${RED}✗ Authentication failed${NC}"
  echo -e "  Debug log saved to auth_debug.log"
  
  # Extract error message
  ERROR_MSG=$(grep -A 3 "ERROR:" auth_debug.log | head -n 4)
  echo -e "  Error message: $ERROR_MSG"
fi

# Step 5: Check service account status
echo -e "\n${YELLOW}Step 5: Checking service account status${NC}"
if [ -n "$ACTIVE_ACCOUNT" ] && [ "$ACTIVE_ACCOUNT" != "$CLIENT_EMAIL" ]; then
  echo -e "${BLUE}Using existing authenticated account to check service account status...${NC}"
  
  # Check if service account exists
  if gcloud iam service-accounts describe "$CLIENT_EMAIL" --project="$PROJECT_ID_IN_KEY" &>/dev/null; then
    echo -e "${GREEN}✓ Service account exists${NC}"
    
    # Check if service account is disabled
    SA_STATUS=$(gcloud iam service-accounts describe "$CLIENT_EMAIL" --project="$PROJECT_ID_IN_KEY" --format="json" | jq -r '.disabled // false')
    if [ "$SA_STATUS" = "true" ]; then
      echo -e "${RED}✗ Service account is disabled${NC}"
    else
      echo -e "${GREEN}✓ Service account is enabled${NC}"
    fi
    
    # List service account keys
    echo -e "${BLUE}Listing service account keys...${NC}"
    gcloud iam service-accounts keys list --iam-account="$CLIENT_EMAIL" --project="$PROJECT_ID_IN_KEY"
  else
    echo -e "${RED}✗ Service account does not exist or you don't have permission to view it${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Cannot check service account status without authentication${NC}"
  echo -e "  Please authenticate with a user account that has permission to view service accounts"
fi

# Step 6: Check for organization policies that might restrict service account key usage
echo -e "\n${YELLOW}Step 6: Checking for organization policies${NC}"
if [ -n "$ACTIVE_ACCOUNT" ]; then
  echo -e "${BLUE}Checking for organization policies that might restrict service account key usage...${NC}"
  
  # Check for constraints/iam.disableServiceAccountKeyCreation
  if gcloud resource-manager org-policies describe constraints/iam.disableServiceAccountKeyCreation --project="$PROJECT_ID_IN_KEY" &>/dev/null; then
    POLICY=$(gcloud resource-manager org-policies describe constraints/iam.disableServiceAccountKeyCreation --project="$PROJECT_ID_IN_KEY" --format="json")
    if echo "$POLICY" | jq -e '.booleanPolicy.enforced == true' &>/dev/null; then
      echo -e "${RED}✗ Organization policy prevents service account key creation${NC}"
    else
      echo -e "${GREEN}✓ No organization policy preventing service account key creation${NC}"
    fi
  else
    echo -e "${GREEN}✓ No organization policy preventing service account key creation${NC}"
  fi
  
  # Check for constraints/iam.disableServiceAccountKeyUpload
  if gcloud resource-manager org-policies describe constraints/iam.disableServiceAccountKeyUpload --project="$PROJECT_ID_IN_KEY" &>/dev/null; then
    POLICY=$(gcloud resource-manager org-policies describe constraints/iam.disableServiceAccountKeyUpload --project="$PROJECT_ID_IN_KEY" --format="json")
    if echo "$POLICY" | jq -e '.booleanPolicy.enforced == true' &>/dev/null; then
      echo -e "${RED}✗ Organization policy prevents service account key upload${NC}"
    else
      echo -e "${GREEN}✓ No organization policy preventing service account key upload${NC}"
    fi
  else
    echo -e "${GREEN}✓ No organization policy preventing service account key upload${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Cannot check organization policies without authentication${NC}"
fi

# Step 7: Check for common issues
echo -e "\n${YELLOW}Step 7: Checking for common issues${NC}"

# Check for newlines in private key
if jq -r '.private_key' "$KEY_FILE" | grep -q '\\n'; then
  echo -e "${RED}✗ Private key contains escaped newlines (\\n) instead of actual newlines${NC}"
  echo -e "  This is a common issue when copying keys. Try recreating the key file."
else
  echo -e "${GREEN}✓ Private key format looks good${NC}"
fi

# Check for extra characters
if grep -q -E '[^[:print:]]' "$KEY_FILE"; then
  echo -e "${RED}✗ Key file contains non-printable characters${NC}"
  echo -e "  This can happen when copying keys. Try recreating the key file."
else
  echo -e "${GREEN}✓ No non-printable characters detected${NC}"
fi

# Summary
echo -e "\n${BLUE}=== Diagnostic Summary ===${NC}"
echo -e "Key file: $KEY_FILE"
echo -e "Client email: $CLIENT_EMAIL"
echo -e "Project ID: $PROJECT_ID_IN_KEY"

if [ -f "auth_debug.log" ]; then
  echo -e "\n${BLUE}Debug log saved to auth_debug.log${NC}"
  echo -e "Review this file for more detailed error information."
fi

echo -e "\n${BLUE}=== Recommendations ===${NC}"
echo -e "1. If authentication failed, try recreating the service account key in the Google Cloud Console."
echo -e "2. Ensure the service account has the necessary permissions for the operations you're trying to perform."
echo -e "3. Check if the service account is enabled and not restricted by organization policies."
echo -e "4. If using the key in a different environment, ensure it's properly copied without corruption."
echo -e "5. Consider using Workload Identity Federation instead of service account keys for better security."

echo -e "\n${BLUE}=== End of Diagnostics ===${NC}"
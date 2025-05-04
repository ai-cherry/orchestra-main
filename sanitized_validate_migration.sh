#!/bin/bash
# sanitized_validate_migration.sh
#
# SANITIZED VERSION: This script replaces sensitive information with placeholders
# for security purposes. Replace placeholders with your actual values before use.

set -e

# Configuration - REPLACE WITH YOUR ACTUAL VALUES
GCP_PROJECT_ID="YOUR_PROJECT_ID"        # e.g., "my-project-123"
GCP_ORG_ID="YOUR_ORGANIZATION_ID"       # e.g., "123456789012"
SERVICE_ACCOUNT_EMAIL="YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com"
BUCKET_NAME="YOUR_PROJECT_ID-bucket"    # Name of your GCP storage bucket

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_success() {
  echo -e "${GREEN}✅ PASS: $1${NC}"
}

log_failure() {
  echo -e "${RED}❌ FAIL: $1${NC}"
  FAILED=true
}

log_info() {
  echo -e "${BLUE}$1${NC}"
}

log_step() {
  echo -e "\n${YELLOW}===== $1 =====${NC}"
}

# Step 1: Verify organization membership
log_step "Verifying organization membership"
ORG_CHECK=$(gcloud projects describe ${GCP_PROJECT_ID} --format="value(parent.id)" 2>/dev/null || echo "failed")

if [ "$ORG_CHECK" = "$GCP_ORG_ID" ]; then
  log_success "Project is correctly in organization ${GCP_ORG_ID}"
else
  log_failure "Project is not in the correct organization. Current parent: $ORG_CHECK"
fi

# Step 2: Check Vertex AI service agent role
log_step "Checking Vertex AI service agent role"
SVC_AGENT_CHECK=$(gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" 2>/dev/null | grep "aiplatform.serviceAgent" || echo "")

if [ -n "$SVC_AGENT_CHECK" ]; then
  log_success "Vertex AI service agent role is properly assigned"
else
  log_failure "Vertex AI service agent role is missing"
fi

# Step 3: Check storage roles
log_step "Checking storage access"
STORAGE_ROLE_CHECK=$(gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" 2>/dev/null | grep "storage.admin" || echo "")

if [ -n "$STORAGE_ROLE_CHECK" ]; then
  log_success "Storage admin role is properly assigned"
else
  log_failure "Storage admin role is missing"
fi

# Step 4: Check bucket access (if bucket exists)
log_step "Testing bucket access"
if gsutil ls gs://${BUCKET_NAME} &>/dev/null; then
  log_success "Successfully accessed bucket gs://${BUCKET_NAME}"
else
  log_info "Note: Bucket gs://${BUCKET_NAME} does not exist or is not accessible"
  log_info "Creating a test bucket to verify storage permissions..."
  
  # Create a test bucket with a unique name
  TEST_BUCKET="${GCP_PROJECT_ID}-validation-$(date +%s)"
  if gsutil mb -p ${GCP_PROJECT_ID} gs://${TEST_BUCKET} &>/dev/null; then
    log_success "Successfully created test bucket gs://${TEST_BUCKET}"
    gsutil rb gs://${TEST_BUCKET} &>/dev/null
  else
    log_failure "Failed to create test bucket. Storage permissions may be missing"
  fi
fi

# Step 5: Verify workstation setup (if deployed)
log_step "Checking workstation configuration"
CLUSTER_LIST=$(gcloud workstations clusters list --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "")

if [[ "$CLUSTER_LIST" == *"ai-development"* ]]; then
  log_success "Workstation cluster 'ai-development' exists"
  
  # Check configuration
  CONFIG_LIST=$(gcloud workstations configs list --cluster=ai-development --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "")
  
  if [[ "$CONFIG_LIST" == *"ai-dev-config"* ]]; then
    log_success "Workstation configuration 'ai-dev-config' exists"
  else
    log_failure "Workstation configuration 'ai-dev-config' not found"
  fi
else
  log_info "Workstation cluster 'ai-development' not found or not yet deployed"
fi

# Final Summary
log_step "Validation Complete"

if [ "${FAILED}" = "true" ]; then
  echo -e "${RED}Some validation checks failed. Please review the logs above.${NC}"
  exit 1
else
  echo -e "${GREEN}All validation checks passed successfully!${NC}"
  echo -e "${BLUE}Your GCP project is correctly configured with all required permissions.${NC}"
fi

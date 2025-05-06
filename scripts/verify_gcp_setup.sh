#!/bin/bash
# verify_gcp_setup.sh - Verify GCP infrastructure setup
# This script verifies that the GCP infrastructure has been correctly set up

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${REGION:=us-central1}"
: "${MASTER_SA_NAME:=gcp-master-admin}"
: "${VERTEX_SA_NAME:=vertex-power-user}"
: "${GEMINI_SA_NAME:=gemini-power-user}"

# Log function with timestamps
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${GREEN}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    "FAIL")
      echo -e "${RED}[${timestamp}] [FAIL] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Check if a command succeeds
command_succeeds() {
  "$@" &> /dev/null
  return $?
}

# Verify GCP project
verify_gcp_project() {
  log "INFO" "Verifying GCP project..."
  
  if command_succeeds gcloud projects describe "${GCP_PROJECT_ID}"; then
    log "SUCCESS" "GCP project ${GCP_PROJECT_ID} exists and is accessible"
    return 0
  else
    log "FAIL" "GCP project ${GCP_PROJECT_ID} does not exist or is not accessible"
    return 1
  fi
}

# Verify required APIs are enabled
verify_apis() {
  log "INFO" "Verifying required APIs are enabled..."
  
  local apis=(
    "iamcredentials.googleapis.com"
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "secretmanager.googleapis.com"
    "aiplatform.googleapis.com"
    "artifactregistry.googleapis.com"
    "run.googleapis.com"
    "compute.googleapis.com"
    "storage.googleapis.com"
  )
  
  local all_enabled=true
  
  for api in "${apis[@]}"; do
    if command_succeeds gcloud services list --project="${GCP_PROJECT_ID}" --filter="config.name:${api}" --format="value(config.name)"; then
      log "SUCCESS" "API ${api} is enabled"
    else
      log "FAIL" "API ${api} is not enabled"
      all_enabled=false
    fi
  done
  
  if [ "${all_enabled}" = true ]; then
    return 0
  else
    return 1
  fi
}

# Verify service accounts
verify_service_accounts() {
  log "INFO" "Verifying service accounts..."
  
  local service_accounts=(
    "${MASTER_SA_NAME}"
    "${VERTEX_SA_NAME}"
    "${GEMINI_SA_NAME}"
  )
  
  local all_exist=true
  
  for sa in "${service_accounts[@]}"; do
    if command_succeeds gcloud iam service-accounts describe "${sa}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --project="${GCP_PROJECT_ID}"; then
      log "SUCCESS" "Service account ${sa}@${GCP_PROJECT_ID}.iam.gserviceaccount.com exists"
    else
      log "FAIL" "Service account ${sa}@${GCP_PROJECT_ID}.iam.gserviceaccount.com does not exist"
      all_exist=false
    fi
  done
  
  if [ "${all_exist}" = true ]; then
    return 0
  else
    return 1
  fi
}

# Verify Secret Manager secrets
verify_secrets() {
  log "INFO" "Verifying Secret Manager secrets..."
  
  local secrets=(
    "master-service-account-key"
    "vertex-power-key"
    "gemini-power-key"
  )
  
  local all_exist=true
  
  for secret in "${secrets[@]}"; do
    if command_succeeds gcloud secrets describe "${secret}" --project="${GCP_PROJECT_ID}"; then
      log "SUCCESS" "Secret ${secret} exists"
    else
      log "FAIL" "Secret ${secret} does not exist"
      all_exist=false
    fi
  done
  
  if [ "${all_exist}" = true ]; then
    return 0
  else
    return 1
  fi
}

# Verify Terraform state bucket
verify_terraform_state_bucket() {
  log "INFO" "Verifying Terraform state bucket..."
  
  local bucket="${GCP_PROJECT_ID}-terraform-state"
  
  if command_succeeds gcloud storage buckets describe "gs://${bucket}"; then
    log "SUCCESS" "Terraform state bucket gs://${bucket} exists"
    return 0
  else
    log "FAIL" "Terraform state bucket gs://${bucket} does not exist"
    return 1
  fi
}

# Verify Vertex AI access
verify_vertex_ai_access() {
  log "INFO" "Verifying Vertex AI access..."
  
  if command_succeeds gcloud ai models list --project="${GCP_PROJECT_ID}" --region="${REGION}" --limit=1; then
    log "SUCCESS" "Access to Vertex AI models"
    return 0
  else
    log "FAIL" "Cannot access Vertex AI models"
    return 1
  fi
}

# Verify GitHub secrets
verify_github_secrets() {
  log "INFO" "Verifying GitHub secrets..."
  
  if ! command_exists gh; then
    log "WARN" "GitHub CLI not found, skipping GitHub secrets verification"
    return 0
  fi
  
  if ! command_succeeds gh auth status; then
    log "WARN" "Not authenticated with GitHub, skipping GitHub secrets verification"
    return 0
  fi
  
  local secrets=(
    "GCP_MASTER_SERVICE_JSON"
    "GCP_VERTEX_POWER_KEY"
    "GCP_GEMINI_POWER_KEY"
    "GCP_PROJECT_ID"
    "GCP_REGION"
  )
  
  local all_exist=true
  local org_repo="${GITHUB_ORG}/${GITHUB_REPO}"
  
  for secret in "${secrets[@]}"; do
    if command_succeeds gh secret list --repo "${org_repo}" | grep -q "${secret}"; then
      log "SUCCESS" "GitHub secret ${secret} exists"
    else
      log "FAIL" "GitHub secret ${secret} does not exist"
      all_exist=false
    fi
  done
  
  if [ "${all_exist}" = true ]; then
    return 0
  else
    return 1
  fi
}

# Run all verification checks
run_all_checks() {
  log "INFO" "Running all verification checks..."
  
  local total_checks=0
  local passed_checks=0
  local failed_checks=0
  local check_results=()
  
  # Run each check and collect results
  for check_func in verify_gcp_project verify_apis verify_service_accounts verify_secrets verify_terraform_state_bucket verify_vertex_ai_access verify_github_secrets; do
    total_checks=$((total_checks + 1))
    
    if ${check_func}; then
      passed_checks=$((passed_checks + 1))
      check_results+=("${GREEN}✓${NC} ${check_func}")
    else
      failed_checks=$((failed_checks + 1))
      check_results+=("${RED}✗${NC} ${check_func}")
    fi
    
    # Add a separator between checks
    echo ""
  done
  
  # Print summary
  echo -e "\n${BOLD}Verification Summary:${NC}"
  echo -e "Total checks: ${total_checks}"
  echo -e "Passed: ${GREEN}${passed_checks}${NC}"
  echo -e "Failed: ${RED}${failed_checks}${NC}"
  
  # Print detailed results
  echo -e "\n${BOLD}Verification Results:${NC}"
  for result in "${check_results[@]}"; do
    echo -e "  ${result}"
  done
  
  # Return success if all checks passed
  if [ ${failed_checks} -eq 0 ]; then
    log "SUCCESS" "All verification checks passed!"
    return 0
  else
    log "FAIL" "${failed_checks} verification checks failed"
    return 1
  fi
}

# Main function
main() {
  log "INFO" "Starting GCP infrastructure verification..."
  
  # Check for gcloud
  if ! command_exists gcloud; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Please install it: https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
  
  # Run all verification checks
  run_all_checks
  
  log "INFO" "GCP infrastructure verification completed"
}

# Execute main function
main
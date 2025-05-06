#!/bin/bash
# verify_gcp_setup.sh - Verify the GCP infrastructure setup

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
    "TEST")
      echo -e "${BLUE}[${timestamp}] [TEST] ${message}${NC}"
      ;;
    "PASS")
      echo -e "${GREEN}[${timestamp}] [PASS] ${message}${NC}"
      ;;
    "FAIL")
      echo -e "${RED}[${timestamp}] [FAIL] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check requirements
check_requirements() {
  log "INFO" "Checking requirements..."
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Please install it: https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
}

# Authenticate with GCP
authenticate_gcp() {
  log "INFO" "Authenticating with GCP..."
  
  # Check if GCP_MASTER_SERVICE_JSON is set
  if [[ -n "${GCP_MASTER_SERVICE_JSON}" ]]; then
    # Create a temporary file for the service account key
    local temp_file=$(mktemp)
    echo "${GCP_MASTER_SERVICE_JSON}" > "${temp_file}"
    
    # Authenticate with the service account key
    gcloud auth activate-service-account --key-file="${temp_file}"
    
    # Clean up
    rm -f "${temp_file}"
  else
    log "WARN" "GCP_MASTER_SERVICE_JSON not set, using default authentication"
    # Use default authentication (Application Default Credentials)
    gcloud auth application-default login --no-launch-browser
  fi
  
  # Set the project
  gcloud config set project "${GCP_PROJECT_ID}"
  
  log "SUCCESS" "Successfully authenticated with GCP"
}

# Test GCP project access
test_gcp_project_access() {
  log "TEST" "Testing GCP project access..."
  
  if gcloud projects describe "${GCP_PROJECT_ID}" &>/dev/null; then
    log "PASS" "GCP project access test passed"
    return 0
  else
    log "FAIL" "GCP project access test failed"
    return 1
  fi
}

# Test APIs enabled
test_apis_enabled() {
  log "TEST" "Testing APIs enabled..."
  
  local apis=(
    "secretmanager.googleapis.com"
    "iam.googleapis.com"
    "aiplatform.googleapis.com"
    "storage.googleapis.com"
    "cloudbuild.googleapis.com"
    "iamcredentials.googleapis.com"
    "workloadidentity.googleapis.com"
  )
  
  local failed=0
  
  for api in "${apis[@]}"; do
    if gcloud services list --enabled --filter="name:${api}" --format="value(name)" | grep -q "${api}"; then
      log "PASS" "API ${api} is enabled"
    else
      log "FAIL" "API ${api} is not enabled"
      failed=1
    fi
  done
  
  if [ ${failed} -eq 0 ]; then
    log "PASS" "APIs enabled test passed"
    return 0
  else
    log "FAIL" "APIs enabled test failed"
    return 1
  fi
}

# Test service accounts
test_service_accounts() {
  log "TEST" "Testing service accounts..."
  
  local service_accounts=(
    "vertex-power-user@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    "gemini-power-user@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    "github-actions@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  )
  
  local failed=0
  
  for sa in "${service_accounts[@]}"; do
    if gcloud iam service-accounts describe "${sa}" &>/dev/null; then
      log "PASS" "Service account ${sa} exists"
    else
      log "FAIL" "Service account ${sa} does not exist"
      failed=1
    fi
  done
  
  if [ ${failed} -eq 0 ]; then
    log "PASS" "Service accounts test passed"
    return 0
  else
    log "FAIL" "Service accounts test failed"
    return 1
  fi
}

# Test Secret Manager secrets
test_secret_manager_secrets() {
  log "TEST" "Testing Secret Manager secrets..."
  
  local secrets=(
    "vertex-power-key"
    "gemini-power-key"
  )
  
  local failed=0
  
  for secret in "${secrets[@]}"; do
    if gcloud secrets describe "${secret}" &>/dev/null; then
      log "PASS" "Secret ${secret} exists"
    else
      log "FAIL" "Secret ${secret} does not exist"
      failed=1
    fi
  done
  
  if [ ${failed} -eq 0 ]; then
    log "PASS" "Secret Manager secrets test passed"
    return 0
  else
    log "FAIL" "Secret Manager secrets test failed"
    return 1
  fi
}

# Test Workload Identity Federation
test_workload_identity_federation() {
  log "TEST" "Testing Workload Identity Federation..."
  
  # Check if Workload Identity Pool exists
  if gcloud iam workload-identity-pools describe github-actions-pool --location=global &>/dev/null; then
    log "PASS" "Workload Identity Pool exists"
  else
    log "FAIL" "Workload Identity Pool does not exist"
    return 1
  fi
  
  # Check if Workload Identity Provider exists
  if gcloud iam workload-identity-pools providers describe github-actions-provider \
    --workload-identity-pool=github-actions-pool \
    --location=global &>/dev/null; then
    log "PASS" "Workload Identity Provider exists"
  else
    log "FAIL" "Workload Identity Provider does not exist"
    return 1
  fi
  
  log "PASS" "Workload Identity Federation test passed"
  return 0
}

# Test Vertex AI access
test_vertex_ai_access() {
  log "TEST" "Testing Vertex AI access..."
  
  if gcloud ai models list --region="${REGION}" &>/dev/null; then
    log "PASS" "Vertex AI access test passed"
    return 0
  else
    log "FAIL" "Vertex AI access test failed"
    return 1
  fi
}

# Run all tests
run_all_tests() {
  log "INFO" "Running all tests..."
  
  local total_tests=0
  local passed_tests=0
  local failed_tests=0
  local test_results=()
  
  # Run each test and collect results
  for test_func in test_gcp_project_access test_apis_enabled test_service_accounts test_secret_manager_secrets test_workload_identity_federation test_vertex_ai_access; do
    total_tests=$((total_tests + 1))
    
    if ${test_func}; then
      passed_tests=$((passed_tests + 1))
      test_results+=("${GREEN}✓${NC} ${test_func}")
    else
      failed_tests=$((failed_tests + 1))
      test_results+=("${RED}✗${NC} ${test_func}")
    fi
    
    # Add a separator between tests
    echo ""
  done
  
  # Print summary
  echo -e "\n${BOLD}Test Summary:${NC}"
  echo -e "Total tests: ${total_tests}"
  echo -e "Passed: ${GREEN}${passed_tests}${NC}"
  echo -e "Failed: ${RED}${failed_tests}${NC}"
  
  # Print detailed results
  echo -e "\n${BOLD}Test Results:${NC}"
  for result in "${test_results[@]}"; do
    echo -e "  ${result}"
  done
  
  # Return success if all tests passed
  if [ ${failed_tests} -eq 0 ]; then
    log "SUCCESS" "All tests passed!"
    return 0
  else
    log "ERROR" "${failed_tests} tests failed"
    return 1
  fi
}

# Main function
main() {
  log "INFO" "Starting GCP infrastructure verification..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Run all tests
  run_all_tests
  
  log "INFO" "GCP infrastructure verification completed"
}

# Execute main function
main
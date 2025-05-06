#!/bin/bash
# test_gcp_integration.sh - Test the integration between GitHub, Codespaces, and GCP

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

# Test Secret Manager access
test_secret_manager_access() {
  log "TEST" "Testing Secret Manager access..."
  
  if gcloud secrets list --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "PASS" "Secret Manager access test passed"
    return 0
  else
    log "FAIL" "Secret Manager access test failed"
    return 1
  fi
}

# Test Vertex AI access
test_vertex_ai_access() {
  log "TEST" "Testing Vertex AI access..."
  
  if gcloud ai models list --region="${REGION}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "PASS" "Vertex AI access test passed"
    return 0
  else
    log "FAIL" "Vertex AI access test failed"
    return 1
  fi
}

# Test Cloud Storage access
test_cloud_storage_access() {
  log "TEST" "Testing Cloud Storage access..."
  
  if gcloud storage ls --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "PASS" "Cloud Storage access test passed"
    return 0
  else
    log "FAIL" "Cloud Storage access test failed"
    return 1
  fi
}

# Test IAM access
test_iam_access() {
  log "TEST" "Testing IAM access..."
  
  if gcloud iam service-accounts list --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "PASS" "IAM access test passed"
    return 0
  else
    log "FAIL" "IAM access test failed"
    return 1
  fi
}

# Test Vertex AI service account key
test_vertex_key() {
  log "TEST" "Testing Vertex AI service account key..."
  
  # Get the key from Secret Manager
  local vertex_key=$(gcloud secrets versions access latest --secret="vertex-power-key" --project="${GCP_PROJECT_ID}" 2>/dev/null)
  
  if [[ -n "${vertex_key}" ]]; then
    # Create a temporary file for the key
    local temp_file=$(mktemp)
    echo "${vertex_key}" > "${temp_file}"
    
    # Authenticate with the key
    if gcloud auth activate-service-account --key-file="${temp_file}" &>/dev/null; then
      log "PASS" "Vertex AI service account key test passed"
      
      # Clean up
      rm -f "${temp_file}"
      
      return 0
    else
      log "FAIL" "Vertex AI service account key test failed: Could not authenticate with the key"
      
      # Clean up
      rm -f "${temp_file}"
      
      return 1
    fi
  else
    log "FAIL" "Vertex AI service account key test failed: Key not found in Secret Manager"
    return 1
  fi
}

# Test Gemini service account key
test_gemini_key() {
  log "TEST" "Testing Gemini service account key..."
  
  # Get the key from Secret Manager
  local gemini_key=$(gcloud secrets versions access latest --secret="gemini-power-key" --project="${GCP_PROJECT_ID}" 2>/dev/null)
  
  if [[ -n "${gemini_key}" ]]; then
    # Create a temporary file for the key
    local temp_file=$(mktemp)
    echo "${gemini_key}" > "${temp_file}"
    
    # Authenticate with the key
    if gcloud auth activate-service-account --key-file="${temp_file}" &>/dev/null; then
      log "PASS" "Gemini service account key test passed"
      
      # Clean up
      rm -f "${temp_file}"
      
      return 0
    else
      log "FAIL" "Gemini service account key test failed: Could not authenticate with the key"
      
      # Clean up
      rm -f "${temp_file}"
      
      return 1
    fi
  else
    log "FAIL" "Gemini service account key test failed: Key not found in Secret Manager"
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
  for test_func in test_gcp_project_access test_secret_manager_access test_vertex_ai_access test_cloud_storage_access test_iam_access test_vertex_key test_gemini_key; do
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
  log "INFO" "Starting GCP integration tests..."
  
  # Check requirements
  check_requirements
  
  # Authenticate with GCP
  authenticate_gcp
  
  # Run all tests
  run_all_tests
  
  log "INFO" "GCP integration tests completed"
}

# Execute main function
main
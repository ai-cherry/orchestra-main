#!/bin/bash
# test_gcp_integration.sh - Test integration between GitHub, Codespaces, and GCP
# This script verifies that the service account keys are working correctly and that the necessary permissions are in place

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

# Test gcloud authentication
test_gcloud_auth() {
  log "INFO" "Testing gcloud authentication..."
  
  if ! command_exists gcloud; then
    log "ERROR" "gcloud CLI is not installed"
    return 1
  fi
  
  if command_succeeds gcloud auth list --filter=status:ACTIVE --format="value(account)"; then
    local account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    log "SUCCESS" "Authenticated with gcloud as: ${account}"
    return 0
  else
    log "FAIL" "Not authenticated with gcloud"
    return 1
  fi
}

# Test GCP project access
test_project_access() {
  log "INFO" "Testing GCP project access..."
  
  if command_succeeds gcloud projects describe "${GCP_PROJECT_ID}"; then
    log "SUCCESS" "Access to GCP project: ${GCP_PROJECT_ID}"
    return 0
  else
    log "FAIL" "Cannot access GCP project: ${GCP_PROJECT_ID}"
    return 1
  fi
}

# Test Vertex AI access
test_vertex_ai_access() {
  log "INFO" "Testing Vertex AI access..."
  
  if command_succeeds gcloud ai models list --project="${GCP_PROJECT_ID}" --region="${REGION}" --limit=1; then
    log "SUCCESS" "Access to Vertex AI models"
    return 0
  else
    log "FAIL" "Cannot access Vertex AI models"
    return 1
  fi
}

# Test Gemini API access
test_gemini_api_access() {
  log "INFO" "Testing Gemini API access..."
  
  # Create a temporary Python script to test Gemini API access
  local temp_script=$(mktemp)
  cat > "${temp_script}" << EOF
import os
import sys
from google.cloud import aiplatform

try:
    # Initialize Vertex AI with the project and region
    aiplatform.init(project='${GCP_PROJECT_ID}', location='${REGION}')
    
    # Create a Gemini model
    model = aiplatform.GenerativeModel(model_name="gemini-pro")
    
    # Generate a simple response
    response = model.generate_content("Hello, Gemini!")
    
    # Print the response
    print(response.text)
    
    # Success
    sys.exit(0)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
EOF
  
  # Run the Python script
  if python3 "${temp_script}"; then
    log "SUCCESS" "Access to Gemini API"
    rm "${temp_script}"
    return 0
  else
    log "FAIL" "Cannot access Gemini API"
    rm "${temp_script}"
    return 1
  fi
}

# Test Secret Manager access
test_secret_manager_access() {
  log "INFO" "Testing Secret Manager access..."
  
  if command_succeeds gcloud secrets list --project="${GCP_PROJECT_ID}" --limit=1; then
    log "SUCCESS" "Access to Secret Manager"
    return 0
  else
    log "FAIL" "Cannot access Secret Manager"
    return 1
  fi
}

# Test Storage access
test_storage_access() {
  log "INFO" "Testing Storage access..."
  
  if command_succeeds gsutil ls -p "${GCP_PROJECT_ID}" gs:// 2>/dev/null; then
    log "SUCCESS" "Access to Storage"
    return 0
  else
    log "FAIL" "Cannot access Storage"
    return 1
  fi
}

# Test GitHub CLI access
test_github_cli_access() {
  log "INFO" "Testing GitHub CLI access..."
  
  if ! command_exists gh; then
    log "ERROR" "GitHub CLI is not installed"
    return 1
  fi
  
  if command_succeeds gh auth status; then
    log "SUCCESS" "Authenticated with GitHub CLI"
    return 0
  else
    log "FAIL" "Not authenticated with GitHub CLI"
    return 1
  fi
}

# Test GitHub repository access
test_github_repo_access() {
  log "INFO" "Testing GitHub repository access..."
  
  # Get the current repository from git config
  local remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
  
  if [ -z "${remote_url}" ]; then
    log "WARN" "Not in a git repository or no remote configured"
    return 1
  fi
  
  # Extract owner and repo from the remote URL
  local owner_repo=""
  if [[ "${remote_url}" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
    owner_repo="${BASH_REMATCH[1]}"
    owner_repo="${owner_repo%.git}"
  else
    log "WARN" "Could not extract owner/repo from remote URL: ${remote_url}"
    return 1
  fi
  
  if command_succeeds gh repo view "${owner_repo}"; then
    log "SUCCESS" "Access to GitHub repository: ${owner_repo}"
    return 0
  else
    log "FAIL" "Cannot access GitHub repository: ${owner_repo}"
    return 1
  fi
}

# Test GitHub Codespaces access
test_github_codespaces_access() {
  log "INFO" "Testing GitHub Codespaces access..."
  
  # Check if running in a Codespace
  if [ -n "${CODESPACES}" ] && [ "${CODESPACES}" = "true" ]; then
    log "SUCCESS" "Running in a GitHub Codespace"
    return 0
  else
    log "WARN" "Not running in a GitHub Codespace"
    return 1
  fi
}

# Run all tests and summarize results
run_all_tests() {
  local total_tests=0
  local passed_tests=0
  local failed_tests=0
  local test_results=()
  
  log "INFO" "Running all integration tests..."
  
  # Run each test and collect results
  for test_func in test_gcloud_auth test_project_access test_vertex_ai_access test_gemini_api_access test_secret_manager_access test_storage_access test_github_cli_access test_github_repo_access test_github_codespaces_access; do
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
    log "SUCCESS" "All integration tests passed!"
    return 0
  else
    log "FAIL" "${failed_tests} integration tests failed"
    return 1
  fi
}

# Main function
main() {
  log "INFO" "Starting GCP integration tests..."
  
  # Run all tests
  run_all_tests
  
  log "INFO" "GCP integration tests completed"
}

# Execute main function
main
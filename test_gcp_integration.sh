#!/bin/bash

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  GCP INTEGRATION TEST${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Function to display test results
test_result() {
  local result=$1
  local message=$2
  if [ $result -eq 0 ]; then
    echo -e "${GREEN}✅ PASS:${NC} $message"
  else
    echo -e "${RED}❌ FAIL:${NC} $message"
  fi
  return $result
}

# Record total tests and failures
TOTAL_TESTS=0
FAILED_TESTS=0

# Run a test and record results
run_test() {
  local command=$1
  local description=$2
  local hide_output=${3:-false}
  
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  
  echo -e "\n${BLUE}Test ${TOTAL_TESTS}:${NC} $description"
  echo -e "${YELLOW}Command:${NC} $command"
  
  # Run the command
  if [ "$hide_output" = true ]; then
    eval "$command" > /dev/null 2>&1
  else
    eval "$command"
  fi
  
  local result=$?
  test_result $result "$description"
  
  if [ $result -ne 0 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
  
  return $result
}

echo "Starting GCP integration test at $(date)"

# 1. Check gcloud installation and version
run_test "command -v gcloud" "Verify gcloud is installed" false
if [ $? -eq 0 ]; then
  echo -e "${BLUE}gcloud location:${NC} $(which gcloud)"
  echo -e "${BLUE}gcloud version:${NC} $(gcloud --version | head -1)"
fi

# 2. Check active authentication
run_test "gcloud auth list" "Check GCP authentication" false

# 3. Verify target project
run_test "gcloud config get-value project" "Verify GCP project configuration" false

# 4. Check application default credentials
run_test "[ -n \"\$GOOGLE_APPLICATION_CREDENTIALS\" ] && [ -f \"\$GOOGLE_APPLICATION_CREDENTIALS\" ]" "Verify application default credentials" false
if [ $? -eq 0 ]; then
  echo -e "${BLUE}Credentials file:${NC} $GOOGLE_APPLICATION_CREDENTIALS"
fi

# 5. Test basic connectivity - list projects
run_test "gcloud projects list --limit=1" "Test basic API connectivity (list projects)" false

# 6. Test basic resource listing - compute zones
run_test "gcloud compute zones list --limit=1" "Test compute resource API (list zones)" false

# 7. Test IAM permissions
run_test "gcloud iam service-accounts list --limit=1" "Test IAM permissions (list service accounts)" false

# 8. Test a more complex operation - describe project
run_test "gcloud projects describe cherry-ai-project" "Test describing project details" false

# 9. Verify restricted mode is disabled
run_test "[ \"\$VSCODE_DISABLE_WORKSPACE_TRUST\" = \"true\" ]" "Verify restricted mode is disabled" false

# 10. Test file permissions by writing to a temporary file
TEMP_FILE="/tmp/gcp_test_$$.txt"
run_test "echo 'Test file write access' > $TEMP_FILE && cat $TEMP_FILE && rm $TEMP_FILE" "Test file system write permissions" false

# Print test summary
echo -e "\n${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  TEST SUMMARY${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "Total tests: ${BOLD}${TOTAL_TESTS}${NC}"
echo -e "Tests passed: ${BOLD}${GREEN}$((TOTAL_TESTS - FAILED_TESTS))${NC}"
echo -e "Tests failed: ${BOLD}${RED}${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "\n${BOLD}${GREEN}All tests passed!${NC} Your GCP integration is working correctly."
else
  echo -e "\n${BOLD}${RED}Some tests failed.${NC} Please review the errors above and run ./fix_codespace_environment.sh to address issues."
fi

echo -e "\nTest completed at $(date)"

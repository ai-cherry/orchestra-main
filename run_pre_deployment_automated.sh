#!/bin/bash
# run_pre_deployment_automated.sh - Automated Pre-Deployment Verification
#
# This script automates the steps in the Manual Pre-Deployment Checklist, including:
# 1. Running readiness verification
# 2. Setting up PostgreSQL with pgvector
# 3. Verifying credentials
# 4. Running system diagnostics
# 5. Running connection and integration tests
# 6. Launching the UI for manual verification
#
# It identifies which steps are fully automated and which still require manual review.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}${BOLD}   Orchestra Automated Pre-Deployment Verification   ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Function to run a step and handle errors
run_step() {
  local step_name=$1
  local command=$2
  local manual_review=$3  # "yes" if manual review is required, "no" otherwise

  echo -e "\n${BLUE}${BOLD}Running step: ${step_name}${NC}"

  if [ "$manual_review" == "yes" ]; then
    echo -e "${YELLOW}⚠️  This step requires manual review of the output.${NC}"
  fi

  # Run the command
  echo -e "${YELLOW}Command: ${command}${NC}"
  echo -e "${YELLOW}Output:${NC}"

  if eval $command; then
    if [ "$manual_review" == "yes" ]; then
      echo -e "\n${YELLOW}✓ Step completed, but requires manual review of the output.${NC}"
      read -p "Press Enter after reviewing the output to continue..."
    else
      echo -e "\n${GREEN}✓ Step completed successfully.${NC}"
    fi
    return 0
  else
    echo -e "\n${RED}✗ Step failed.${NC}"
    if [ "$CONTINUE_ON_ERROR" == "yes" ]; then
      echo -e "${YELLOW}Continuing despite error due to CONTINUE_ON_ERROR=yes${NC}"
      return 1
    else
      echo -e "${RED}Exiting due to error. Fix the issue or set CONTINUE_ON_ERROR=yes to proceed anyway.${NC}"
      exit 1
    fi
  fi
}

# Show options
echo -e "This script will automate the pre-deployment checklist as much as possible."
echo -e "${YELLOW}Note: Some steps will still require manual review or verification.${NC}"
echo -e ""
echo -e "${BOLD}Options:${NC}"
read -p "Continue on error? (y/n, default: n): " continue_on_error
if [ "$continue_on_error" == "y" ] || [ "$continue_on_error" == "Y" ]; then
  CONTINUE_ON_ERROR="yes"
else
  CONTINUE_ON_ERROR="no"
fi

# Track overall status
status=0

# Step 0: Verify deployment readiness
if [ -f "./verify_deployment_readiness.sh" ]; then
  run_step "Deployment Readiness Check" "chmod +x ./verify_deployment_readiness.sh && ./verify_deployment_readiness.sh" "yes" || ((status++))
else
  echo -e "${RED}Error: verify_deployment_readiness.sh not found${NC}"
  ((status++))
fi

# Step 1: PostgreSQL setup with pgvector
echo -e "\n${BLUE}${BOLD}1. PostgreSQL Setup${NC}"
if [ -f "./scripts/setup_postgres_pgvector.py" ]; then
  run_step "PostgreSQL pgvector Setup" "python scripts/setup_postgres_pgvector.py --apply --schema llm" "yes" || ((status++))
else
  echo -e "${RED}Error: scripts/setup_postgres_pgvector.py not found${NC}"
  ((status++))
fi

# Step 2: Verify credentials
echo -e "\n${BLUE}${BOLD}2. Credentials Verification${NC}"
if [ -f "./setup_credentials.sh" ]; then
  run_step "Credentials Setup" "chmod +x ./setup_credentials.sh && ./setup_credentials.sh" "yes" || ((status++))
else
  echo -e "${RED}Error: setup_credentials.sh not found${NC}"
  ((status++))
fi

# Step 3: Run system diagnostics
echo -e "\n${BLUE}${BOLD}3. System Diagnostics${NC}"
if [ -f "./unified_diagnostics.py" ]; then
  run_step "Comprehensive Diagnostics" "python unified_diagnostics.py --all" "yes" || ((status++))
else
  echo -e "${RED}Error: unified_diagnostics.py not found${NC}"
  ((status++))
fi

# Step 4: Run connection tests
echo -e "\n${BLUE}${BOLD}4. Key Integration Tests${NC}"

# Step 4a: Firestore/Redis connection tests
if [ -f "./run_connection_tests.sh" ]; then
  run_step "Firestore/Redis Connection Tests" "chmod +x ./run_connection_tests.sh && ./run_connection_tests.sh" "yes" || ((status++))
else
  echo -e "${RED}Error: run_connection_tests.sh not found${NC}"
  ((status++))
fi

# Step 4b: PostgreSQL connectivity test
if [ -f "./test_postgres_connection.py" ]; then
  run_step "PostgreSQL Connectivity Test" "python test_postgres_connection.py" "yes" || ((status++))
else
  echo -e "${RED}Error: test_postgres_connection.py not found${NC}"
  ((status++))
fi

# Step 4c: LLM integration test
echo -e "\n${YELLOW}Checking for LLM integration test path...${NC}"
llm_test_path=""
if [ -d "./packages/llm/src" ]; then
  llm_test_path="packages/llm/src/test_phidata_integration.py"
else
  # Try other common locations
  for path in "./packages/llm/test_phidata_integration.py" "./test_phidata_integration.py"; do
    if [ -f "$path" ]; then
      llm_test_path=$path
      break
    fi
  done
fi

if [ -n "$llm_test_path" ]; then
  run_step "LLM Integration Test" "python -m ${llm_test_path%.py}" "yes" || ((status++))
else
  echo -e "${YELLOW}Warning: LLM integration test path not found. Skipping this test.${NC}"
  echo -e "${YELLOW}You should manually run: python -m packages.llm.src.test_phidata_integration${NC}"
fi

# Step 4d: Tool integration test
echo -e "\n${YELLOW}Checking for tool integration test path...${NC}"
tool_test_path=""
if [ -d "./packages/tools/src" ]; then
  tool_test_path="packages/tools/src/test_phidata_integration.py"
else
  # Try other common locations
  for path in "./packages/tools/test_phidata_integration.py" "./test_tools_integration.py"; do
    if [ -f "$path" ]; then
      tool_test_path=$path
      break
    fi
  done
fi

if [ -n "$tool_test_path" ]; then
  run_step "Tool Integration Test" "python -m ${tool_test_path%.py}" "yes" || ((status++))
else
  echo -e "${YELLOW}Warning: Tool integration test path not found. Skipping this test.${NC}"
  echo -e "${YELLOW}You should manually run: python -m packages.tools.src.test_phidata_integration${NC}"
fi

# Step 4e: Core integration test for /phidata/chat endpoint
echo -e "\n${YELLOW}Checking for core integration test paths...${NC}"
phidata_test_path=""
for path in "./tests/integration/phidata/test_phidata_agents_integration.py" "./tests/test_phidata_integration.py"; do
  if [ -f "$path" ]; then
    phidata_test_path=$path
    break
  fi
done

if [ -n "$phidata_test_path" ]; then
  run_step "Core Integration Test" "pytest $phidata_test_path -v" "yes" || ((status++))
else
  echo -e "${YELLOW}Warning: Core integration test path not found. Skipping this test.${NC}"
  echo -e "${YELLOW}You should manually run one of these commands:${NC}"
  echo -e "${YELLOW}  pytest tests/integration/phidata/test_phidata_agents_integration.py${NC}"
  echo -e "${YELLOW}  pytest tests/test_phidata_integration.py${NC}"
fi

# Step 5: UI verification (this step requires manual testing)
echo -e "\n${BLUE}${BOLD}5. UI Verification${NC}"
echo -e "${YELLOW}⚠️  This step requires manual verification and cannot be automated.${NC}"

# Get the UI URL from Terraform output if possible
ui_url=""
if command -v terraform &> /dev/null && [ -d "infra/orchestra-terraform" ]; then
  echo -e "${YELLOW}Attempting to get UI URL from Terraform output...${NC}"
  terraform_output=$(terraform -chdir="infra/orchestra-terraform" output -json service_urls 2>/dev/null || echo '{}')
  ui_url=$(echo $terraform_output | jq -r '.ui // empty' 2>/dev/null)

  if [ -n "$ui_url" ] && [ "$ui_url" != "null" ]; then
    echo -e "${GREEN}Found UI URL: $ui_url${NC}"
    echo -e "${YELLOW}Please visit the URL in your browser to verify the UI functionality.${NC}"

    # Try to open the URL in the default browser if on a supported platform
    echo -e "${YELLOW}Attempting to open the URL in your browser...${NC}"
    if command -v xdg-open &> /dev/null; then
      xdg-open "$ui_url" || echo -e "${YELLOW}Could not open URL automatically. Please open it manually.${NC}"
    elif command -v open &> /dev/null; then
      open "$ui_url" || echo -e "${YELLOW}Could not open URL automatically. Please open it manually.${NC}"
    else
      echo -e "${YELLOW}Could not detect a command to open URLs. Please open the URL manually.${NC}"
    fi
  else
    echo -e "${YELLOW}Could not get UI URL from Terraform output.${NC}"
  fi
else
  echo -e "${YELLOW}Terraform not found or infra/orchestra-terraform directory not found.${NC}"
  echo -e "${YELLOW}You will need to manually obtain the UI URL.${NC}"
fi

echo -e "\n${YELLOW}To verify the UI:${NC}"
echo -e "1. Access the UI using the URL obtained above or from deployment logs"
echo -e "2. Test sending messages and verify responses are received"
echo -e "3. Check that tool invocations work as expected"
echo -e "4. Test different agent types if applicable"
echo -e ""
read -p "Have you completed the manual UI verification? (y/n, default: n): " ui_verified
if [ "$ui_verified" == "y" ] || [ "$ui_verified" == "Y" ]; then
  echo -e "${GREEN}UI verification marked as completed.${NC}"
else
  echo -e "${YELLOW}UI verification not completed or skipped. You should perform this step manually.${NC}"
  ((status++))
fi

# Check for code duplication cleanup recommendations
echo -e "\n${BLUE}${BOLD}Code Duplication Cleanup Recommendations${NC}"
if [ -f "./docs/TECHNICAL_DEBT_REMEDIATION_PLAN.md" ]; then
  echo -e "${YELLOW}Found Technical Debt Remediation Plan which includes code duplication cleanup.${NC}"
  echo -e "${YELLOW}Please review the plan at ./docs/TECHNICAL_DEBT_REMEDIATION_PLAN.md${NC}"
  echo -e "${YELLOW}Specifically check section 7: 'Code Cleanup and Consolidation'${NC}"

  if [ -f "./docs/CODEBASE_HEALTH_ASSESSMENT.md" ]; then
    echo -e "${YELLOW}Also review ./docs/CODEBASE_HEALTH_ASSESSMENT.md for details on code duplication issues${NC}"
    echo -e "${YELLOW}Specifically check section 1: 'Parallel Implementation Patterns'${NC}"
  fi

  echo -e "${YELLOW}⚠️  Code duplication cleanup requires manual developer intervention and cannot be automated.${NC}"
else
  echo -e "${YELLOW}Technical Debt Remediation Plan not found. Cannot provide code duplication cleanup recommendations.${NC}"
  ((status++))
fi

# Summarize and provide next steps
echo -e "\n${BLUE}======================================================${NC}"
if [ $status -eq 0 ]; then
  echo -e "${GREEN}${BOLD}✅ All automated checks passed!${NC}"
  echo -e "${GREEN}${BOLD}Pre-deployment verification completed successfully.${NC}"
else
  echo -e "${YELLOW}${BOLD}⚠️ Pre-deployment verification completed with $status issue(s).${NC}"
  echo -e "${YELLOW}Review the output above to address the issues before proceeding.${NC}"
fi

echo -e "\n${BLUE}${BOLD}Summary of Steps Requiring Manual Verification:${NC}"
echo -e "${YELLOW}1. PostgreSQL pgvector setup - Verify output indicates successful setup${NC}"
echo -e "${YELLOW}2. Credentials verification - Check that all required credentials are properly set${NC}"
echo -e "${YELLOW}3. System diagnostics - Review output for any warnings or errors${NC}"
echo -e "${YELLOW}4. Integration tests - Ensure all tests pass and review any failures${NC}"
echo -e "${YELLOW}5. UI verification - Manually test the UI functionality${NC}"
echo -e "${YELLOW}6. Code duplication cleanup - Review technical debt remediation plan${NC}"

echo -e "\n${BLUE}${BOLD}Next Steps:${NC}"
echo -e "${YELLOW}1. Address any issues identified during the automated verification${NC}"
echo -e "${YELLOW}2. Complete any remaining manual verification steps${NC}"
echo -e "${YELLOW}3. Follow the code duplication cleanup recommendations${NC}"
echo -e "${YELLOW}4. Proceed with deployment using one of the available methods:${NC}"
echo -e "   - ./deploy_to_cloud_run.sh prod${NC}"
echo -e "   - cd infra && ./run_terraform.sh${NC}"
echo -e "   - Push to GitHub to trigger CI/CD pipeline${NC}"

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}Thank you for using the Automated Pre-Deployment Verification tool.${NC}"
echo -e "${BLUE}======================================================${NC}"

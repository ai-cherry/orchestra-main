#!/bin/bash
# verify-setup.sh - Validate the entire configuration

# Source the centralized environment configuration
source ~/setup-env.sh

# Text formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Status tracking
pass_count=0
fail_count=0
warning_count=0

echo "======================================================"
echo "  AI ORCHESTRA ENVIRONMENT VERIFICATION"
echo "======================================================"

# Function to check if VSCode extension is installed
# Function to check if VSCode extension is installed
check_vscode_extension() {
  local extension_id=$1
  local extension_name=$2
  
  # Check if we're in a Codespace or VS Code environment
  if [[ -n "$VSCODE_CLI" || -n "$CODESPACES" ]]; then
    echo -n "Checking for VSCode extension: $extension_name... "
    
    # This is a simple check that looks for extension files in the VS Code extensions directory
    # A more robust solution would use the VS Code CLI, but this works for basic verification
    local extension_found=false
    
    # Check in .vscode-server/extensions
    if [[ -d "$HOME/.vscode-server/extensions" ]]; then
      for ext_dir in "$HOME/.vscode-server/extensions"/*; do
        if [[ -d "$ext_dir" && "$ext_dir" == *"$extension_id"* ]]; then
          extension_found=true
          break
        fi
      done
    fi
    
    # If not found, check in .vscode/extensions
    if [[ "$extension_found" == "false" && -d "$HOME/.vscode/extensions" ]]; then
      for ext_dir in "$HOME/.vscode/extensions"/*; do
        if [[ -d "$ext_dir" && "$ext_dir" == *"$extension_id"* ]]; then
          extension_found=true
          break
        fi
      done
    fi
    
    if [[ "$extension_found" == "true" ]]; then
      echo -e "${GREEN}FOUND${NC}"
      ((pass_count++))
    else
      echo -e "${YELLOW}NOT FOUND${NC}"
      echo "  Consider installing the $extension_name extension for better GCP integration"
      ((warning_count++))
    fi
  fi
}

# Check for GCP-related VSCode extensions
check_vscode_extension "googlecloudtools.cloudcode" "Cloud Code"
check_vscode_extension "google-cloud-spanner-ecosystem.google-cloud-spanner" "Google Cloud Spanner"
# Check GCP authentication
echo -n "Checking GCP authentication... "
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  echo -e "${GREEN}PASSED${NC}"
  echo "  Active account: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
  ((pass_count++))
else
  echo -e "${RED}FAILED${NC}"
  echo "  No active GCP account found"
  ((fail_count++))
fi

# Check GCP project
echo -n "Checking GCP project... "
if [[ "$(gcloud config get-value project)" == "cherry-ai-project" ]]; then
  echo -e "${GREEN}PASSED${NC}"
  ((pass_count++))
else
  echo -e "${RED}FAILED${NC}"
  echo "  Project is set to: $(gcloud config get-value project)"
  ((fail_count++))
fi

# Check service account key
echo -n "Checking service account key... "
if [[ -f "$HOME/.gcp/service-account.json" ]]; then
  echo -e "${GREEN}PASSED${NC}"
  ((pass_count++))
else
  echo -e "${RED}FAILED${NC}"
  echo "  Service account key not found at $HOME/.gcp/service-account.json"
  ((fail_count++))
fi

# Check environment variables
echo -n "Checking environment variables... "
if [[ -n "$GOOGLE_APPLICATION_CREDENTIALS" && -n "$CLOUDSDK_CORE_PROJECT" && -n "$STANDARD_MODE" ]]; then
  echo -e "${GREEN}PASSED${NC}"
  ((pass_count++))
else
  echo -e "${RED}FAILED${NC}"
  echo "  Missing required environment variables"
  [[ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]] && echo "  - GOOGLE_APPLICATION_CREDENTIALS not set"
  [[ -z "$CLOUDSDK_CORE_PROJECT" ]] && echo "  - CLOUDSDK_CORE_PROJECT not set"
  [[ -z "$STANDARD_MODE" ]] && echo "  - STANDARD_MODE not set"
  ((fail_count++))
fi

# Check workspace trust settings
echo -n "Checking workspace trust settings... "
if [[ "$VSCODE_DISABLE_WORKSPACE_TRUST" == "true" ]]; then
  echo -e "${GREEN}PASSED${NC}"
  ((pass_count++))
else
  echo -e "${YELLOW}WARNING${NC}"
  echo "  VSCODE_DISABLE_WORKSPACE_TRUST is not set to 'true'"
  ((warning_count++))
fi

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
  echo -e "${GREEN}PASSED${NC}"
  echo "  Docker version: $(docker --version)"
  ((pass_count++))
else
  echo -e "${YELLOW}WARNING${NC}"
  echo "  Docker not found"
  ((warning_count++))
fi

# Check Terraform
echo -n "Checking Terraform... "
if command -v terraform &> /dev/null; then
  echo -e "${GREEN}PASSED${NC}"
  echo "  Terraform version: $(terraform --version | head -n 1)"
  ((pass_count++))
else
  echo -e "${YELLOW}WARNING${NC}"
  echo "  Terraform not found"
  ((warning_count++))
fi

# Check Poetry
echo -n "Checking Poetry... "
if command -v poetry &> /dev/null; then
  echo -e "${GREEN}PASSED${NC}"
  echo "  Poetry version: $(poetry --version)"
  ((pass_count++))
else
  echo -e "${YELLOW}WARNING${NC}"
  echo "  Poetry not found"
  ((warning_count++))
fi

# Test GCP API access
echo -n "Testing GCP API access... "
if gcloud projects describe cherry-ai-project --format="value(name)" &>/dev/null; then
  echo -e "${GREEN}PASSED${NC}"
  echo "  Successfully accessed project information"
  ((pass_count++))
else
  echo -e "${RED}FAILED${NC}"
  echo "  Could not access GCP project information"
  ((fail_count++))
fi

echo "======================================================"
echo "  VERIFICATION COMPLETE"
echo "======================================================"
echo "Summary: $pass_count checks passed, $fail_count checks failed, $warning_count warnings"

# Set exit code based on failures
if [[ $fail_count -gt 0 ]]; then
  echo "See above for details on failed checks"
  exit 1
fi

exit 0
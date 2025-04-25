#!/bin/bash
# verify_deployment_readiness.sh - Script to verify deployment readiness
#
# This script checks if the environment is properly set up for deployment
# and performs basic validation of configuration and credentials.

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
echo -e "${BLUE}${BOLD}   Orchestra Deployment Readiness Check               ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Function to check requirement
check_requirement() {
  local name=$1
  local check_command=$2
  local error_message=$3
  
  echo -n -e "${YELLOW}Checking $name...${NC} "
  
  if eval $check_command; then
    echo -e "${GREEN}✓ OK${NC}"
    return 0
  else
    echo -e "${RED}✗ FAILED${NC}"
    echo -e "  ${RED}$error_message${NC}"
    return 1
  fi
}

# Track overall status
status=0

# Check if .env file exists
check_requirement ".env file" "[ -f .env ]" "Missing .env file with configuration" || ((status++))

# Check if Dockerfile exists
check_requirement "Dockerfile" "[ -f Dockerfile ]" "Missing Dockerfile for containerization" || ((status++))

# Check environment variables
echo -e "\n${BLUE}${BOLD}Checking environment variables:${NC}"

# Check GCP Project ID
check_requirement "GCP_PROJECT_ID" "grep -q 'GCP_PROJECT_ID=' .env" "GCP_PROJECT_ID not set in .env file" || ((status++))

# Check GCP Auth
echo -e "\n${BLUE}${BOLD}Checking GCP authentication:${NC}"

# Check if GCP service account key exists
check_requirement "GCP Service Account Key" "[ -f /tmp/vertex-agent-key.json ]" "GCP service account key not found at /tmp/vertex-agent-key.json" || ((status++))

# Parse and validate the service account key if it exists
if [ -f /tmp/vertex-agent-key.json ]; then
  # Check if the service account key is valid JSON
  check_requirement "Valid SA Key JSON" "jq -e . /tmp/vertex-agent-key.json > /dev/null 2>&1" "Service account key is not valid JSON" || ((status++))
  
  # Check if the key has the necessary fields
  check_requirement "SA Key project" "jq -e '.project_id' /tmp/vertex-agent-key.json > /dev/null 2>&1" "Service account key missing project_id field" || ((status++))
  
  # Check if the key is for the expected project
  expected_project="agi-baby-cherry"
  actual_project=$(jq -r '.project_id' /tmp/vertex-agent-key.json 2>/dev/null || echo "unknown")
  check_requirement "SA Key project match" "[ \"$actual_project\" = \"$expected_project\" ]" "Service account key is for project '$actual_project', expected '$expected_project'" || ((status++))
fi

# Check API and Docker requirements
echo -e "\n${BLUE}${BOLD}Checking deployment tools:${NC}"

# Check if Docker is installed (for building)
docker_installed=$(command -v docker > /dev/null 2>&1 && echo "yes" || echo "no")
check_requirement "Docker installation" "[ \"$docker_installed\" = \"yes\" ]" "Docker is not installed" || ((status++))

# Check if gcloud is installed
gcloud_installed=$(command -v gcloud > /dev/null 2>&1 && echo "yes" || echo "no")
check_requirement "gcloud installation" "[ \"$gcloud_installed\" = \"yes\" ]" "Google Cloud SDK is not installed" || ((status++))

# If both are available, check more deeply
if [ "$docker_installed" = "yes" ]; then
  # Check if Docker daemon is running
  check_requirement "Docker daemon" "docker info > /dev/null 2>&1" "Docker daemon is not running" || ((status++))
fi

if [ "$gcloud_installed" = "yes" ]; then
  # Check if gcloud is authenticated
  check_requirement "gcloud auth" "gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q '@'" "Not authenticated with gcloud. Run 'gcloud auth login'" || ((status++))
  
  # Check if project is set
  project_set=$(gcloud config get-value project 2>/dev/null)
  check_requirement "gcloud project" "[ \"$project_set\" = \"agi-baby-cherry\" ]" "GCP project not set to 'agi-baby-cherry'. Run 'gcloud config set project agi-baby-cherry'" || ((status++))
fi

# Check CI/CD configuration
echo -e "\n${BLUE}${BOLD}Checking CI/CD configuration:${NC}"

# Check if GitHub workflows exist
check_requirement "GitHub workflows" "[ -d .github/workflows ]" "GitHub workflows directory not found" || ((status++))

# Check if main CD workflow exists
check_requirement "CI/CD workflow" "[ -f .github/workflows/orchestra-cicd.yml ]" "Main CI/CD workflow file not found" || ((status++))

# Check Redis configuration
echo -e "\n${BLUE}${BOLD}Checking Redis configuration:${NC}"

redis_host=$(grep "REDIS_HOST=" .env 2>/dev/null | cut -d= -f2)
if [ "$redis_host" = "localhost" ]; then
  echo -e "${YELLOW}⚠️  WARNING: Redis is configured to use localhost in .env${NC}"
  echo -e "${YELLOW}   For production deployment, Redis should point to a managed instance.${NC}"
fi

# Check API keys
echo -e "\n${BLUE}${BOLD}Checking API keys:${NC}"

# Check Portkey API Key
check_requirement "Portkey API Key" "grep -q 'PORTKEY_API_KEY=' .env" "PORTKEY_API_KEY not set in .env file" || ((status++))

# Check OpenRouter API Key
check_requirement "OpenRouter API Key" "grep -q 'OPENROUTER_API_KEY=' .env" "OPENROUTER_API_KEY not set in .env file" || ((status++))

# Summarize and provide next steps
echo -e "\n${BLUE}======================================================${NC}"
if [ $status -eq 0 ]; then
  echo -e "${GREEN}${BOLD}✅ All checks passed! Your environment is ready for deployment.${NC}"
  
  echo -e "\n${BLUE}${BOLD}Next steps for deployment:${NC}"
  echo -e "${YELLOW}1. Quick deployment to Cloud Run:${NC}"
  echo -e "   ./deploy_to_cloud_run.sh prod"
  echo -e "\n${YELLOW}2. Full infrastructure deployment with Terraform:${NC}"
  echo -e "   cd infra && ./run_terraform.sh"
  echo -e "\n${YELLOW}3. CI/CD deployment via GitHub Actions:${NC}"
  echo -e "   Commit and push changes to trigger deployment pipeline"
  echo -e "   Make sure GitHub repository secrets are properly configured"
else
  echo -e "${RED}${BOLD}❌ Found $status issue(s) that need to be resolved before deployment.${NC}"
  
  echo -e "\n${BLUE}${BOLD}Recommended actions:${NC}"
  echo -e "${YELLOW}1. Run the preparation script:${NC}"
  echo -e "   ./prepare_for_deployment.sh"
  echo -e "\n${YELLOW}2. Update GitHub secrets (if using CI/CD):${NC}"
  echo -e "   ./update_github_secrets.sh"
  echo -e "\n${YELLOW}3. Fix any remaining issues and run this verification again.${NC}"
fi
echo -e "${BLUE}======================================================${NC}"

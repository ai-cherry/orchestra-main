#!/bin/bash
# trigger_github_workflow.sh - Script to trigger a GitHub Actions workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER=${1:-"ai-cherry"}
REPO_NAME=${2:-"orchestra-main"}
WORKFLOW_ID=${3:-"key-deploy.yml"}
ENVIRONMENT=${4:-"dev"}

echo -e "${GREEN}Triggering GitHub Actions workflow...${NC}"
echo -e "${YELLOW}Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"
echo -e "${YELLOW}Workflow: ${WORKFLOW_ID}${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh) is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}Visit https://cli.github.com/ for installation instructions.${NC}"
    exit 1
fi

# Check if user is authenticated with GitHub CLI
if ! gh auth status &> /dev/null; then
    echo -e "${RED}You are not authenticated with GitHub CLI. Please run 'gh auth login' first.${NC}"
    exit 1
fi

# Trigger the workflow
echo -e "${GREEN}Triggering workflow...${NC}"
gh workflow run ${WORKFLOW_ID} -R ${REPO_OWNER}/${REPO_NAME} -f environment=${ENVIRONMENT}

echo -e "${GREEN}Workflow triggered successfully!${NC}"
echo -e "${YELLOW}You can check the workflow status at:${NC}"
echo -e "${YELLOW}https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_ID}${NC}"
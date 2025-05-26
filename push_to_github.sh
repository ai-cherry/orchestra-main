#!/bin/bash
# push_to_github.sh
# Script to push code to GitHub, triggering the GitHub Actions workflow for deployment

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

  case $level in
    "INFO")
      echo -e "${BLUE}[${timestamp}] [INFO] ${message}${NC}"
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
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check if git is installed
if ! command -v git &> /dev/null; then
  log "ERROR" "git is required but not installed. Please install it and try again."
  exit 1
fi

# Check if the current directory is a git repository
if [ ! -d .git ]; then
  log "ERROR" "The current directory is not a git repository. Please initialize a git repository and try again."
  exit 1
fi

# Check if the GitHub remote exists
if ! git remote | grep -q "origin"; then
  log "ERROR" "The 'origin' remote does not exist. Please add a remote named 'origin' and try again."
  log "INFO" "You can add a remote with: git remote add origin <repository-url>"
  exit 1
fi

# Get the current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Prompt for confirmation
log "WARN" "This script will push your code to the '${CURRENT_BRANCH}' branch on GitHub, triggering the deployment workflow."
log "WARN" "Make sure you have committed all your changes before proceeding."
read -p "Do you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  log "INFO" "Operation cancelled by user."
  exit 0
fi

# Add all files to git
log "INFO" "Adding all files to git..."
git add .

# Commit changes
log "INFO" "Committing changes..."
git commit -m "Deploy to Cloud Run via GitHub Actions"

# Push to GitHub
log "INFO" "Pushing to GitHub..."
git push origin ${CURRENT_BRANCH}

log "SUCCESS" "Code pushed to GitHub successfully!"
log "INFO" "The GitHub Actions workflow will now deploy the application to Cloud Run."
log "INFO" "You can check the status of the deployment in the 'Actions' tab of your GitHub repository."

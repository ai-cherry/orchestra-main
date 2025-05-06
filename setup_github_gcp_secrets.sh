#!/bin/bash

# Master script to set up all GitHub GCP secrets and authentication
# This script executes all the individual setup scripts in the correct sequence

set -e

# Color codes for better readability
RESET="\033[0m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"

# Log a message with timestamp
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${RESET}"
}

# Log an error message
error() {
  echo -e "${RED}[ERROR] $1${RESET}"
}

# Log a section header
section() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${CYAN}    $1${RESET}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
}

# Main execution
main() {
  section "GITHUB GCP SECRETS SETUP - MASTER SCRIPT"
  log "Starting complete GitHub GCP secrets setup process"
  log "This script will execute all the necessary steps to configure GCP authentication"
  log "for GitHub Actions workflows and Codespaces environments."
  
  # Create project admin service account and keys
  section "STEP 1: Creating Vertex AI and Secret Management Service Accounts"
  if [ -f "./create_service_accounts_and_update_secrets.sh" ]; then
    log "Running create_service_accounts_and_update_secrets.sh..."
    chmod +x ./create_service_accounts_and_update_secrets.sh
    ./create_service_accounts_and_update_secrets.sh
    log "Service accounts and GitHub organization secrets created successfully."
  else
    error "create_service_accounts_and_update_secrets.sh not found!"
    exit 1
  fi
  
  # Create Gemini service account and keys
  section "STEP 2: Creating Gemini API Service Account"
  if [ -f "./setup_gemini_access.sh" ]; then
    log "Running setup_gemini_access.sh..."
    chmod +x ./setup_gemini_access.sh
    ./setup_gemini_access.sh
    log "Gemini API service account and GitHub organization secrets created successfully."
  else
    error "setup_gemini_access.sh not found!"
    exit 1
  fi
  
  # Update GitHub Codespaces secrets
  section "STEP 3: Updating GitHub Codespaces Secrets"
  if [ -f "./update_codespaces_secrets.sh" ]; then
    log "Running update_codespaces_secrets.sh..."
    chmod +x ./update_codespaces_secrets.sh
    ./update_codespaces_secrets.sh
    log "GitHub Codespaces secrets updated successfully."
  else
    error "update_codespaces_secrets.sh not found!"
    exit 1
  fi
  
  section "SETUP COMPLETE"
  log "All GitHub GCP secrets have been set up successfully!"
  log "Please refer to GITHUB_GCP_SECRETS_SETUP.md for details on the changes made."
  log ""
  log "Note: The GitHub Actions workflows have been temporarily configured to use"
  log "service account keys instead of Workload Identity Federation for initial setup."
  log "Consider reverting to Workload Identity Federation after initial Terraform apply."
  log ""
  log "Run the following command to view the documentation:"
  log "cat GITHUB_GCP_SECRETS_SETUP.md"
}

# Execute the script
main

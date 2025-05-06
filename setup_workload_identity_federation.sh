#!/bin/bash
# setup_workload_identity_federation.sh - Main entry point for setting up Workload Identity Federation
# This script makes all WIF scripts executable and runs the setup process

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check requirements
check_requirements() {
  log "INFO" "Checking requirements..."
  
  # Check for GCP_MASTER_SERVICE_JSON
  if [[ -z "${GCP_MASTER_SERVICE_JSON}" ]]; then
    log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is required"
    log "INFO" "Please set the GCP_MASTER_SERVICE_JSON environment variable with your service account key"
    exit 1
  fi
  
  # Check for GITHUB_TOKEN
  if [[ -z "${GITHUB_TOKEN}" ]]; then
    log "ERROR" "GITHUB_TOKEN environment variable is required"
    log "INFO" "Please set the GITHUB_TOKEN environment variable with your GitHub personal access token"
    exit 1
  fi
  
  # Check for Portkey API key if using Portkey as LLM gateway
  if [[ -z "${PORTKEY_API_KEY}" && "${USE_PORTKEY_GATEWAY}" == "true" ]]; then
    log "WARN" "PORTKEY_API_KEY environment variable is not set but Portkey gateway is enabled"
    log "INFO" "Set PORTKEY_API_KEY for secure virtual key management with LLM providers"
  fi
  
  log "INFO" "All requirements satisfied"
}

# Make scripts executable
make_scripts_executable() {
  log "INFO" "Making WIF scripts executable..."
  
  chmod +x sync_github_gcp_secrets.sh
  chmod +x orchestra_wif_master.sh
  chmod +x migrate_workflow_to_wif.sh
  chmod +x setup_wif_codespaces.sh
  
  log "INFO" "Scripts are now executable"
}

# Run the WIF setup process
run_wif_setup() {
  log "INFO" "Starting Workload Identity Federation setup..."
  
  # Run the master setup script
  log "INFO" "Running orchestra_wif_master.sh..."
  ./orchestra_wif_master.sh
  
  # Migrate GitHub Actions workflows
  log "INFO" "Running migrate_workflow_to_wif.sh..."
  ./migrate_workflow_to_wif.sh
  
  # Configure Codespaces
  log "INFO" "Running setup_wif_codespaces.sh..."
  ./setup_wif_codespaces.sh
  
  log "INFO" "Workload Identity Federation setup complete!"
}

# Display help information
show_help() {
  echo -e "${BLUE}${BOLD}Workload Identity Federation Setup${NC}"
  echo ""
  echo -e "${YELLOW}Usage:${NC}"
  echo "  $0 [options]"
  echo ""
  echo -e "${YELLOW}Options:${NC}"
  echo "  --help, -h     Show this help message"
  echo "  --make-exec    Only make scripts executable"
  echo "  --run-setup    Run the WIF setup process"
  echo ""
  echo -e "${YELLOW}Environment Variables:${NC}"
  echo "  GCP_MASTER_SERVICE_JSON    Service account key for GCP authentication"
  echo "  GITHUB_TOKEN               GitHub personal access token"
  echo ""
  echo -e "${YELLOW}Example:${NC}"
  echo "  export GCP_MASTER_SERVICE_JSON='<your-service-account-key-json>'"
  echo "  export GITHUB_TOKEN='<your-github-pat>'"
  echo "  $0"
}

# Main function
main() {
  # Parse command line arguments
  if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
  elif [[ "$1" == "--make-exec" ]]; then
    make_scripts_executable
    exit 0
  elif [[ "$1" == "--run-setup" ]]; then
    check_requirements
    run_wif_setup
    exit 0
  fi
  
  # Default behavior: make scripts executable and run setup
  log "INFO" "Starting Workload Identity Federation setup for AI Orchestra..."
  
  # Check requirements
  check_requirements
  
  # Make scripts executable
  make_scripts_executable
  
  # Run the WIF setup process
  run_wif_setup
  
  log "INFO" "Workload Identity Federation setup complete!"
  log "INFO" "Please refer to WORKLOAD_IDENTITY_FEDERATION.md for more information"
}

# Execute main function
main "$@"

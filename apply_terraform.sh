#!/bin/bash
# apply_terraform.sh
# Script to apply Terraform configuration for the AI Orchestra project

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

# Check if a command exists
check_command() {
  if ! command -v $1 &> /dev/null; then
    log "ERROR" "$1 is required but not installed. Please install it and try again."
    exit 1
  fi
}

# Check prerequisites
check_prerequisites() {
  log "INFO" "Checking prerequisites..."
  
  # Check for required commands
  check_command "terraform"
  
  # Check if GCP_MASTER_SERVICE_JSON environment variable is set
  if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
    log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is not set. Please set it and try again."
    exit 1
  fi
  
  log "SUCCESS" "Prerequisites check passed"
}

# Initialize Terraform
initialize_terraform() {
  log "INFO" "Initializing Terraform..."
  
  # Create temporary service account key file from environment variable
  log "INFO" "Creating temporary service account key file from GCP_MASTER_SERVICE_JSON..."
  echo "${GCP_MASTER_SERVICE_JSON}" > /tmp/gcp-credentials.json
  chmod 600 /tmp/gcp-credentials.json
  
  # Set environment variable for authentication
  log "INFO" "Setting GOOGLE_APPLICATION_CREDENTIALS environment variable..."
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-credentials.json
  
  # Change to terraform directory
  cd terraform
  
  # Initialize Terraform
  log "INFO" "Running terraform init..."
  terraform init
  
  log "SUCCESS" "Terraform initialized successfully"
}

# Plan Terraform changes
plan_terraform() {
  log "INFO" "Planning Terraform changes..."
  
  # Run terraform plan
  terraform plan -out=tfplan
  
  log "SUCCESS" "Terraform plan created successfully"
}

# Apply Terraform changes
apply_terraform() {
  log "INFO" "Applying Terraform changes..."
  
  # Run terraform apply
  terraform apply -auto-approve tfplan
  
  log "SUCCESS" "Terraform changes applied successfully"
}

# Show Terraform outputs
show_outputs() {
  log "INFO" "Showing Terraform outputs..."
  
  # Run terraform output
  terraform output
  
  log "SUCCESS" "Terraform outputs displayed successfully"
}

# Cleanup
cleanup() {
  log "INFO" "Cleaning up..."
  
  # Remove temporary files
  rm -f /tmp/gcp-credentials.json
  rm -f terraform/tfplan
  
  log "SUCCESS" "Cleanup completed successfully"
}

# Main function
main() {
  log "INFO" "Starting Terraform deployment for AI Orchestra project..."
  
  # Check prerequisites
  check_prerequisites
  
  # Initialize Terraform
  initialize_terraform
  
  # Plan Terraform changes
  plan_terraform
  
  # Apply Terraform changes
  apply_terraform
  
  # Show Terraform outputs
  show_outputs
  
  # Cleanup
  cleanup
  
  log "SUCCESS" "Terraform deployment completed successfully!"
  log "INFO" "The following resources have been deployed:"
  log "INFO" "1. Service accounts for Vertex AI and Gemini"
  log "INFO" "2. IAM permissions for service accounts"
  log "INFO" "3. Storage buckets for model artifacts and data sync"
  log "INFO" "4. Secret Manager secrets for service account keys"
  log "INFO" "5. Workload Identity Federation for GitHub Actions"
  log "INFO" "6. Cloud Run service for the Orchestra API"
  
  log "INFO" "You can access your Cloud Run service at the URL shown in the outputs above."
}

# Execute main function
main
#!/bin/bash
# setup_infrastructure.sh - Master script to set up infrastructure for AI Orchestra
# This script makes all the infrastructure scripts executable and runs them in sequence

# Exit on error, but allow for error handling
set -o pipefail

# Configuration
: "${ENV:=dev}"                                # Environment (dev, staging, prod)
: "${LOG_FILE:=infrastructure_setup.log}"      # Log file
: "${GCP_PROJECT_ID:=cherry-ai-project}"       # GCP Project ID
: "${GITHUB_ORG:=ai-cherry}"                   # GitHub Organization
: "${GITHUB_REPO:=orchestra-main}"             # GitHub Repository
: "${REGION:=us-central1}"                     # GCP Region

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p logs

# Log function with timestamps and log to file
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  local log_message="[${timestamp}] [${level}] ${message}"
  
  case $level in
    "INFO")
      echo -e "${GREEN}${log_message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}${log_message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}${log_message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}${log_message}${NC}"
      ;;
    *)
      echo -e "${log_message}"
      ;;
  esac
  
  # Log to file without color codes
  echo "[${timestamp}] [${level}] ${message}" >> "logs/${LOG_FILE}"
}

# Error handling function
handle_error() {
  local exit_code=$?
  local line_number=$1
  
  if [ $exit_code -ne 0 ]; then
    log "ERROR" "Failed at line ${line_number} with exit code ${exit_code}"
    log "ERROR" "Check logs/infrastructure_setup.log for details"
    exit $exit_code
  fi
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Validate environment
validate_environment() {
  log "INFO" "Validating environment..."
  
  # Validate environment value
  if [[ ! "$ENV" =~ ^(dev|staging|prod)$ ]]; then
    log "ERROR" "Invalid environment: $ENV. Must be one of: dev, staging, prod"
    return 1
  fi
  
  # Check for required tools
  local required_tools=("gcloud" "gh" "terraform")
  local missing_tools=()
  
  for tool in "${required_tools[@]}"; do
    if ! command -v $tool &> /dev/null; then
      missing_tools+=("$tool")
    fi
  done
  
  if [ ${#missing_tools[@]} -gt 0 ]; then
    log "ERROR" "Missing required tools: ${missing_tools[*]}"
    log "INFO" "Please install the missing tools before continuing"
    return 1
  fi
  
  # Check for required environment variables
  if [ -z "${GCP_MASTER_SERVICE_JSON}" ]; then
    log "ERROR" "GCP_MASTER_SERVICE_JSON environment variable is not set"
    log "INFO" "Please set it to the content of your master service account key"
    return 1
  fi
  
  if [ -z "${GITHUB_TOKEN}" ]; then
    log "ERROR" "GITHUB_TOKEN environment variable is not set"
    log "INFO" "Please set it to your GitHub personal access token"
    return 1
  fi
  
  log "SUCCESS" "Environment validation passed"
  return 0
}

# Make scripts executable
make_scripts_executable() {
  log "INFO" "Making infrastructure scripts executable..."
  
  local scripts=(
    "scripts/create_powerful_service_keys.sh"
    "scripts/update_codespaces_secrets.sh"
    "scripts/test_gcp_integration.sh"
  )
  
  for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
      chmod +x "$script"
      log "INFO" "Made $script executable"
    else
      log "ERROR" "Script not found: $script"
      return 1
    fi
  done
  
  log "SUCCESS" "Scripts are now executable"
  return 0
}

# Run the create_powerful_service_keys.sh script
create_service_keys() {
  log "INFO" "Creating powerful service keys for environment: $ENV..."
  
  # Export required environment variables
  export GCP_PROJECT_ID
  export GITHUB_ORG
  export GITHUB_REPO
  export REGION
  export ENV
  
  # Run the script with timeout and retry
  local max_attempts=3
  local attempt=1
  local success=false
  
  while [ $attempt -le $max_attempts ] && [ "$success" = false ]; do
    log "INFO" "Attempt $attempt of $max_attempts"
    
    if timeout 300 ./scripts/create_powerful_service_keys.sh; then
      success=true
      log "SUCCESS" "Service keys created successfully"
    else
      local exit_code=$?
      if [ $exit_code -eq 124 ]; then
        log "WARN" "Timeout occurred while creating service keys"
      else
        log "WARN" "Failed to create service keys (exit code: $exit_code)"
      fi
      
      if [ $attempt -lt $max_attempts ]; then
        log "INFO" "Retrying in 10 seconds..."
        sleep 10
      fi
      
      attempt=$((attempt + 1))
    fi
  done
  
  if [ "$success" = false ]; then
    log "ERROR" "Failed to create service keys after $max_attempts attempts"
    return 1
  fi
  
  return 0
}

# Run the update_codespaces_secrets.sh script
update_codespaces_secrets() {
  log "INFO" "Updating Codespaces secrets for environment: $ENV..."
  
  # Check if required environment variables are set
  if [ -z "${GCP_VERTEX_POWER_KEY}" ]; then
    log "WARN" "GCP_VERTEX_POWER_KEY environment variable is not set"
    log "INFO" "This should have been set by the create_powerful_service_keys.sh script"
    log "INFO" "Attempting to retrieve from Secret Manager..."
    
    # Try to retrieve from Secret Manager
    if command -v gcloud &> /dev/null; then
      export GCP_VERTEX_POWER_KEY=$(gcloud secrets versions access latest --secret="vertex-power-key" --project="${GCP_PROJECT_ID}" 2>/dev/null)
      if [ -n "${GCP_VERTEX_POWER_KEY}" ]; then
        log "INFO" "Successfully retrieved GCP_VERTEX_POWER_KEY from Secret Manager"
      else
        log "ERROR" "Failed to retrieve GCP_VERTEX_POWER_KEY from Secret Manager"
        return 1
      fi
    else
      log "ERROR" "gcloud not available to retrieve secrets"
      return 1
    fi
  fi
  
  if [ -z "${GCP_GEMINI_POWER_KEY}" ]; then
    log "WARN" "GCP_GEMINI_POWER_KEY environment variable is not set"
    log "INFO" "This should have been set by the create_powerful_service_keys.sh script"
    log "INFO" "Attempting to retrieve from Secret Manager..."
    
    # Try to retrieve from Secret Manager
    if command -v gcloud &> /dev/null; then
      export GCP_GEMINI_POWER_KEY=$(gcloud secrets versions access latest --secret="gemini-power-key" --project="${GCP_PROJECT_ID}" 2>/dev/null)
      if [ -n "${GCP_GEMINI_POWER_KEY}" ]; then
        log "INFO" "Successfully retrieved GCP_GEMINI_POWER_KEY from Secret Manager"
      else
        log "ERROR" "Failed to retrieve GCP_GEMINI_POWER_KEY from Secret Manager"
        return 1
      fi
    else
      log "ERROR" "gcloud not available to retrieve secrets"
      return 1
    fi
  fi
  
  # Export required environment variables
  export GCP_PROJECT_ID
  export GITHUB_ORG
  export GITHUB_REPO
  export REGION
  export ENV
  
  # Run the script
  if ./scripts/update_codespaces_secrets.sh; then
    log "SUCCESS" "Codespaces secrets updated successfully"
    return 0
  else
    log "ERROR" "Failed to update Codespaces secrets"
    return 1
  fi
}

# Run the test_gcp_integration.sh script
test_gcp_integration() {
  log "INFO" "Testing GCP integration for environment: $ENV..."
  
  # Export required environment variables
  export GCP_PROJECT_ID
  export REGION
  export ENV
  
  # Run the script
  if ./scripts/test_gcp_integration.sh; then
    log "SUCCESS" "GCP integration tests completed successfully"
    return 0
  else
    local exit_code=$?
    log "WARN" "Some GCP integration tests failed (exit code: $exit_code)"
    log "INFO" "This may be expected if you haven't completed all setup steps"
    return 0  # Continue anyway
  fi
}

# Apply Terraform changes
apply_terraform() {
  log "INFO" "Applying Terraform changes for environment: $ENV..."
  
  # Check if terraform is installed
  if ! command -v terraform &> /dev/null; then
    log "ERROR" "terraform is not installed"
    log "INFO" "Please install terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
    return 1
  fi
  
  # Create backup of Terraform state
  if [ -f "terraform/terraform.tfstate" ]; then
    local backup_file="terraform/terraform.tfstate.backup.$(date +%Y%m%d%H%M%S)"
    log "INFO" "Creating backup of Terraform state: $backup_file"
    cp terraform/terraform.tfstate "$backup_file"
  fi
  
  # Initialize Terraform
  log "INFO" "Initializing Terraform..."
  (cd terraform && terraform init)
  
  # Plan Terraform changes
  log "INFO" "Planning Terraform changes..."
  (cd terraform && terraform plan -var="env=$ENV" -var="project_id=$GCP_PROJECT_ID" -var="region=$REGION" -out=tfplan)
  
  # Apply Terraform changes
  log "INFO" "Applying Terraform changes..."
  (cd terraform && terraform apply -auto-approve tfplan)
  
  if [ $? -eq 0 ]; then
    log "SUCCESS" "Terraform changes applied successfully"
    return 0
  else
    log "ERROR" "Failed to apply Terraform changes"
    log "INFO" "Check terraform/terraform.tfstate for details"
    
    # Offer to restore from backup
    if [ -f "$backup_file" ]; then
      read -p "Do you want to restore Terraform state from backup? (y/n): " RESTORE_BACKUP
      if [[ "$RESTORE_BACKUP" =~ ^[Yy]$ ]]; then
        cp "$backup_file" terraform/terraform.tfstate
        log "INFO" "Restored Terraform state from backup"
      fi
    fi
    
    return 1
  fi
}

# Main function
main() {
  log "INFO" "Starting infrastructure setup for AI Orchestra (Environment: $ENV)..."
  
  # Create logs directory
  mkdir -p logs
  
  # Validate environment
  if ! validate_environment; then
    log "ERROR" "Environment validation failed"
    exit 1
  fi
  
  # Make scripts executable
  if ! make_scripts_executable; then
    log "ERROR" "Failed to make scripts executable"
    exit 1
  fi
  
  # Ask if the user wants to run the scripts
  read -p "Do you want to run the infrastructure setup scripts for environment '$ENV'? (y/n): " RUN_SCRIPTS
  if [[ "$RUN_SCRIPTS" =~ ^[Yy]$ ]]; then
    # Create service keys
    if ! create_service_keys; then
      log "ERROR" "Failed to create service keys"
      exit 1
    fi
    
    # Update Codespaces secrets
    if ! update_codespaces_secrets; then
      log "ERROR" "Failed to update Codespaces secrets"
      exit 1
    fi
    
    # Test GCP integration
    test_gcp_integration
    
    # Ask if the user wants to apply Terraform changes
    read -p "Do you want to apply Terraform changes for environment '$ENV'? (y/n): " APPLY_TERRAFORM
    if [[ "$APPLY_TERRAFORM" =~ ^[Yy]$ ]]; then
      if ! apply_terraform; then
        log "ERROR" "Failed to apply Terraform changes"
        exit 1
      fi
    else
      log "INFO" "Skipping Terraform changes"
    fi
    
    log "SUCCESS" "Infrastructure setup completed successfully for environment: $ENV!"
    log "INFO" "Log file: logs/$LOG_FILE"
  else
    log "INFO" "Skipping infrastructure setup"
    log "INFO" "You can run the scripts individually:"
    log "INFO" "  - ./scripts/create_powerful_service_keys.sh"
    log "INFO" "  - ./scripts/update_codespaces_secrets.sh"
    log "INFO" "  - ./scripts/test_gcp_integration.sh"
  fi
}

# Execute main function
main
#!/bin/bash
# Validate environment before migration
# This script checks if all prerequisites are in place for the migration

set -e

# Text formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Helper functions
log_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
  echo -e "${RED}✗ $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}! $1${NC}"
}

log_section() {
  echo -e "\n${GREEN}===== $1 =====${NC}"
}

# Check for service account key file
log_section "Checking Service Account Key"
if [ -f "vertex-agent-service-account.json" ]; then
  log_success "Service account key file found"
  # Verify file permissions
  PERMS=$(stat -c "%a" vertex-agent-service-account.json)
  if [ "$PERMS" != "600" ]; then
    log_warning "File permissions should be 600 for security (current: $PERMS)"
    echo "Fixing permissions..."
    chmod 600 vertex-agent-service-account.json
    log_success "Permissions fixed"
  else
    log_success "File permissions are correct (600)"
  fi
  
  # Verify key contents
  if grep -q '"project_id": "agi-baby-cherry"' vertex-agent-service-account.json; then
    log_success "Key contains correct project ID"
  else
    log_error "Key does not contain expected project ID!"
  fi
  
  if grep -q '"client_email": "vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"' vertex-agent-service-account.json; then
    log_success "Key contains correct service account email"
  else
    log_error "Key does not contain expected service account email!"
  fi
else
  log_error "Service account key file not found!"
  exit 1
fi

# Check Terraform configuration file
log_section "Checking Terraform Configuration"
if [ -f "hybrid_workstation_config.tf" ]; then
  log_success "Terraform configuration file found"
  
  # Verify contents
  if grep -q '"n2d-standard-32"' hybrid_workstation_config.tf; then
    log_success "Configuration includes correct machine type"
  else
    log_warning "Configuration may not specify the correct machine type"
  fi
  
  if grep -q '"nvidia-tesla-t4"' hybrid_workstation_config.tf; then
    log_success "Configuration includes GPU accelerator"
  else
    log_warning "Configuration may not specify GPU accelerator"
  fi
  
  if grep -q 'persistent_directories' hybrid_workstation_config.tf; then
    log_success "Configuration includes persistent storage"
  else
    log_warning "Configuration may not specify persistent storage"
  fi
else
  log_warning "Main Terraform configuration not found in root directory"
  log_warning "The migration script will create this file, but it may conflict with existing files"
  
  if [ -f "infra/cloud_workstation_config.tf" ]; then
    log_warning "Alternative configuration found in infra/cloud_workstation_config.tf"
    log_warning "This may cause conflicts - consider backing up before proceeding"
  fi
fi

# Check Redis to AlloyDB sync worker
log_section "Checking Redis to AlloyDB Sync Worker"
if [ -f "agent/core/redis_alloydb_sync.py" ]; then
  log_success "Redis to AlloyDB sync worker found"
  
  # Check debounce interval
  DEBOUNCE=$(grep "debounce_interval: float =" agent/core/redis_alloydb_sync.py | awk '{print $NF}')
  if [ "$DEBOUNCE" == "0.5," ]; then
    log_success "Debounce interval is correctly set to 0.5 seconds"
  else
    log_warning "Debounce interval may not be set to 0.5 seconds (found: $DEBOUNCE)"
  fi
else
  log_error "Redis to AlloyDB sync worker not found!"
fi

# Provide summary
log_section "Validation Summary"
echo "The validation checks have completed. Review any warnings or errors above."
echo "If there are no critical errors, you can proceed with the migration by running:"
echo "./execute_migration.sh"

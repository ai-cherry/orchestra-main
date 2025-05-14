#!/bin/bash
#
# Fix Terraform Duplicate Backend Configuration
#
# This script modifies the Terraform backend configuration to resolve
# the duplicate backend error during migration
#
# Author: Roo

set -e

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logging function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  
  case $level in
    INFO)
      echo -e "${GREEN}[INFO]${NC} ${message}"
      ;;
    WARNING)
      echo -e "${YELLOW}[WARNING]${NC} ${message}"
      ;;
    ERROR)
      echo -e "${RED}[ERROR]${NC} ${message}"
      ;;
    STEP)
      echo -e "${BLUE}[STEP]${NC} ${BOLD}${message}${NC}"
      ;;
    *)
      echo -e "${message}"
      ;;
  esac
}

# Define Terraform directory
TF_DIR="${1:-/workspaces/orchestra-main/terraform/migration}"
if [ ! -d "$TF_DIR" ]; then
  log "ERROR" "Terraform directory not found: $TF_DIR"
  exit 1
fi

# Check if backend files exist
BACKEND_FILE="$TF_DIR/backend.tf"
LOCAL_BACKEND_FILE="$TF_DIR/backend.local.tf"

if [ ! -f "$BACKEND_FILE" ] && [ ! -f "$LOCAL_BACKEND_FILE" ]; then
  log "ERROR" "Neither backend.tf nor backend.local.tf found in $TF_DIR"
  exit 1
fi

# Path for backup files
BACKUP_DIR="$TF_DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
log "INFO" "Creating backup directory: $BACKUP_DIR"

# Backup existing files
if [ -f "$BACKEND_FILE" ]; then
  cp "$BACKEND_FILE" "$BACKUP_DIR/backend.tf.bak"
  log "INFO" "Backed up $BACKEND_FILE to $BACKUP_DIR/backend.tf.bak"
fi

if [ -f "$LOCAL_BACKEND_FILE" ]; then
  cp "$LOCAL_BACKEND_FILE" "$BACKUP_DIR/backend.local.tf.bak"
  log "INFO" "Backed up $LOCAL_BACKEND_FILE to $BACKUP_DIR/backend.local.tf.bak"
fi

# Decide which backend to keep
log "STEP" "Resolving duplicate backend configuration"

log "INFO" "1. Keep only local backend (recommended for testing)"
log "INFO" "2. Keep only GCS backend (recommended for production)"
read -p "Select option (default: 1): " OPTION

if [ "$OPTION" = "2" ]; then
  # Keep GCS backend, remove local backend
  log "INFO" "Keeping GCS backend in $BACKEND_FILE"
  if [ -f "$LOCAL_BACKEND_FILE" ]; then
    mv "$LOCAL_BACKEND_FILE" "$LOCAL_BACKEND_FILE.disabled"
    log "INFO" "Renamed $LOCAL_BACKEND_FILE to $LOCAL_BACKEND_FILE.disabled"
  fi
else
  # Keep local backend, rename GCS backend
  log "INFO" "Keeping local backend in $LOCAL_BACKEND_FILE"
  
  # Create local backend if it doesn't exist
  if [ ! -f "$LOCAL_BACKEND_FILE" ]; then
    log "INFO" "Creating local backend configuration"
    cat > "$LOCAL_BACKEND_FILE" << EOF
# Local backend configuration for development
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
EOF
  fi
  
  # Disable GCS backend
  if [ -f "$BACKEND_FILE" ]; then
    mv "$BACKEND_FILE" "$BACKEND_FILE.disabled"
    log "INFO" "Renamed $BACKEND_FILE to $BACKEND_FILE.disabled"
  fi
fi

# Display result
log "STEP" "Backend configuration resolved"
log "INFO" "Terraform backend configuration has been fixed. You can now run:"
log "INFO" "cd $TF_DIR && terraform init -reconfigure"

# Offer to run Terraform init
read -p "Initialize Terraform now? (y/n): " RUN_INIT
if [[ "$RUN_INIT" =~ ^[Yy] ]]; then
  log "INFO" "Running terraform init -reconfigure"
  cd "$TF_DIR" && terraform init -reconfigure
  
  log "INFO" "Testing with terraform plan"
  terraform plan -out=tfplan || {
    log "WARNING" "Terraform plan encountered issues"
  }
else
  log "INFO" "Skipping Terraform initialization"
fi

log "INFO" "Script completed successfully"
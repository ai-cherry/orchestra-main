#!/bin/bash
# sanitized_manage_keys.sh
#
# SANITIZED VERSION: This script replaces sensitive information with placeholders
# for security purposes. Replace placeholders with your actual values before use.

set -e

# Configuration - REPLACE WITH YOUR ACTUAL VALUES
SERVICE_ACCOUNT="YOUR_SERVICE_ACCOUNT"  # e.g., "service-account@your-project-id.iam.gserviceaccount.com"
PROJECT_ID="YOUR_PROJECT_ID"            # e.g., "your-project-id"
KEY_FILE="service-account-key.json"     # Path to your service account key file
KEY_TEMPLATE="sanitized-service-account-key-template.json"  # Path to your key template file

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
  exit 1
}

log_warning() {
  echo -e "${YELLOW}⚠️ $1${NC}"
}

log_info() {
  echo -e "${BLUE}ℹ️ $1${NC}"
}

show_help() {
  echo -e "${BLUE}Service Account Key Management Script${NC}"
  echo -e "Usage: $0 [OPTION]"
  echo -e "Options:"
  echo -e "  create        Create a new service account key"
  echo -e "  authenticate  Authenticate with existing key"
  echo -e "  rotate        Rotate keys (create new, authenticate, delete old)"
  echo -e "  secure        Set secure permissions on existing key file"
  echo -e "  template      Create key file from template"
  echo -e "  help          Show this help message"
}

create_key() {
  log_info "Creating new service account key for $SERVICE_ACCOUNT"
  
  if [ -f "$KEY_FILE" ]; then
    log_warning "Key file $KEY_FILE already exists."
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_info "Key creation cancelled."
      exit 0
    fi
  fi
  
  # Create new key
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT" || {
    log_error "Failed to create new service account key"
  }
  
  # Set secure permissions
  chmod 600 "$KEY_FILE"
  
  log_success "New key created and secured at $KEY_FILE"
  
  # Print key ID for future reference
  KEY_ID=$(cat "$KEY_FILE" | jq -r '.private_key_id')
  echo -e "${YELLOW}Save this key ID for future rotation: $KEY_ID${NC}"
}

authenticate() {
  log_info "Authenticating with service account key"
  
  if [ ! -f "$KEY_FILE" ]; then
    log_error "Key file $KEY_FILE not found."
  fi
  
  # Verify permissions
  PERMISSIONS=$(stat -c "%a" "$KEY_FILE")
  if [ "$PERMISSIONS" != "600" ]; then
    log_warning "Key file has insecure permissions: $PERMISSIONS"
    log_info "Setting secure permissions (600)..."
    chmod 600 "$KEY_FILE"
  fi
  
  # Authenticate
  gcloud auth activate-service-account "$SERVICE_ACCOUNT" \
    --key-file="$KEY_FILE" || {
    log_error "Failed to authenticate with service account"
  }
  
  # Set project
  gcloud config set project "$PROJECT_ID" || {
    log_warning "Failed to set project to $PROJECT_ID"
  }
  
  log_success "Successfully authenticated as $SERVICE_ACCOUNT"
}

rotate_keys() {
  log_info "Rotating service account keys"
  
  # Prompt for old key ID
  echo -e "${YELLOW}Enter the ID of the old key to revoke:${NC}"
  read OLD_KEY_ID
  
  if [ -z "$OLD_KEY_ID" ]; then
    log_error "No key ID provided"
  fi
  
  # Backup old key if it exists
  if [ -f "$KEY_FILE" ]; then
    BACKUP_FILE="${KEY_FILE}.bak"
    log_info "Backing up existing key to $BACKUP_FILE"
    cp "$KEY_FILE" "$BACKUP_FILE"
  fi
  
  # Create new key
  log_info "Creating new service account key..."
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT" || {
    log_error "Failed to create new service account key"
  }
  
  # Set secure permissions
  chmod 600 "$KEY_FILE"
  
  # Authenticate with new key
  log_info "Authenticating with new key..."
  gcloud auth activate-service-account "$SERVICE_ACCOUNT" \
    --key-file="$KEY_FILE" || {
    log_error "Failed to authenticate with new service account key"
  }
  
  # Delete old key
  log_info "Revoking old key $OLD_KEY_ID..."
  gcloud iam service-accounts keys delete "$OLD_KEY_ID" \
    --iam-account="$SERVICE_ACCOUNT" || {
    log_warning "Failed to revoke old key. It may already be deleted or you may not have permission."
  }
  
  # Get new key ID
  NEW_KEY_ID=$(cat "$KEY_FILE" | jq -r '.private_key_id')
  
  log_success "Key rotation complete!"
  echo -e "${YELLOW}New key ID: $NEW_KEY_ID${NC}"
  echo -e "${YELLOW}Save this key ID for future rotation${NC}"
}

secure_key() {
  log_info "Securing key file permissions"
  
  if [ ! -f "$KEY_FILE" ]; then
    log_error "Key file $KEY_FILE not found."
  fi
  
  # Set secure permissions
  chmod 600 "$KEY_FILE"
  
  # Verify permissions
  PERMISSIONS=$(stat -c "%a" "$KEY_FILE")
  if [ "$PERMISSIONS" == "600" ]; then
    log_success "Key file permissions set to $PERMISSIONS (secure)"
  else
    log_error "Failed to set secure permissions"
  fi
}

create_from_template() {
  log_info "Creating key file from template"
  
  if [ ! -f "$KEY_TEMPLATE" ]; then
    log_error "Template file $KEY_TEMPLATE not found."
  fi
  
  if [ -f "$KEY_FILE" ]; then
    log_warning "Key file $KEY_FILE already exists."
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_info "Key creation cancelled."
      exit 0
    fi
  fi
  
  # Prompt for private key
  echo -e "${YELLOW}Enter your private key (paste, then press Ctrl+D when finished):${NC}"
  PRIVATE_KEY=$(cat)
  
  if [ -z "$PRIVATE_KEY" ]; then
    log_warning "No private key provided. Using placeholder."
    PRIVATE_KEY="[YOUR_ACTUAL_PRIVATE_KEY_HERE]"
  fi
  
  # Create key file from template
  cp "$KEY_TEMPLATE" "$KEY_FILE"
  
  # Replace placeholder with actual key
  sed -i "s|\[YOUR_ACTUAL_PRIVATE_KEY_HERE\]|$PRIVATE_KEY|g" "$KEY_FILE"
  
  # Set secure permissions
  chmod 600 "$KEY_FILE"
  
  log_success "Key file created from template and secured"
}

# Main execution
case "$1" in
  create)
    create_key
    ;;
  authenticate)
    authenticate
    ;;
  rotate)
    rotate_keys
    ;;
  secure)
    secure_key
    ;;
  template)
    create_from_template
    ;;
  help)
    show_help
    ;;
  *)
    log_info "No option specified"
    show_help
    ;;
esac

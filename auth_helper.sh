#!/bin/bash
# auth_helper.sh - Consolidated GCP authentication helper for AI Orchestra
# 
# This script provides a simple, unified approach to GCP authentication
# without browser prompts by using service account keys.
#
# Usage:
#   source auth_helper.sh              # Load functions without authentication
#   source auth_helper.sh --auth       # Load functions and authenticate
#   source auth_helper.sh --help       # Show usage information
#
# Functions:
#   auth_setup            - Set up service account key
#   auth_check            - Check if authentication is configured
#   auth_activate         - Activate authentication
#   auth_get_token        - Get authentication token
#   auth_docker_mount     - Get Docker mount parameters for auth

set -e

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Key file location
AUTH_KEY_FILE="$HOME/.gcp/service-account.json"

# Log function for standardized output
log() {
  local level=$1
  local message=$2
  local color=$NC
  
  case $level in
    "INFO")
      color=$BLUE
      ;;
    "WARN")
      color=$YELLOW
      ;;
    "ERROR")
      color=$RED
      ;;
    "SUCCESS")
      color=$GREEN
      ;;
    *)
      color=$NC
      ;;
  esac
  
  echo -e "${color}[$level] $message${NC}"
}

# Display help information
auth_help() {
  echo "GCP Authentication Helper for AI Orchestra"
  echo ""
  echo "Usage:"
  echo "  source auth_helper.sh              # Load functions without authentication"
  echo "  source auth_helper.sh --auth       # Load functions and authenticate"
  echo "  source auth_helper.sh --help       # Show this help message"
  echo ""
  echo "Environment Variables:"
  echo "  GCP_MASTER_SERVICE_JSON            # Service account JSON (alternative to file)"
  echo ""
  echo "Functions:"
  echo "  auth_setup                         # Set up service account key"
  echo "  auth_check                         # Check if authentication is configured"
  echo "  auth_activate                      # Activate authentication"
  echo "  auth_get_token                     # Get authentication token"
  echo "  auth_docker_mount                  # Get Docker mount parameters for auth"
}

# Check if authentication is configured
auth_check() {
  if [[ -f "$AUTH_KEY_FILE" ]]; then
    log "SUCCESS" "Service account key found at $AUTH_KEY_FILE"
    return 0
  elif [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
    log "SUCCESS" "Service account JSON found in environment variable"
    return 0
  else
    log "WARN" "No service account credentials found"
    return 1
  fi
}

# Set up service account key
auth_setup() {
  # Create directory for service account key
  mkdir -p "$(dirname "$AUTH_KEY_FILE")"
  
  # Check if key file already exists
  if [[ -f "$AUTH_KEY_FILE" ]]; then
    log "INFO" "Service account key already exists at $AUTH_KEY_FILE"
    
    # Verify the key file is valid JSON
    if jq . "$AUTH_KEY_FILE" > /dev/null 2>&1; then
      log "SUCCESS" "Service account key appears to be valid JSON"
    else
      log "ERROR" "Service account key file exists but is not valid JSON"
      return 1
    fi
    
    return 0
  fi
  
  # Check if we have environment variable
  if [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
    log "INFO" "Creating service account key file from environment variable"
    echo "$GCP_MASTER_SERVICE_JSON" > "$AUTH_KEY_FILE"
    
    # Verify the key file is valid JSON
    if jq . "$AUTH_KEY_FILE" > /dev/null 2>&1; then
      log "SUCCESS" "Service account key created successfully"
      chmod 600 "$AUTH_KEY_FILE"  # Secure permissions
      return 0
    else
      log "ERROR" "Failed to create valid service account key"
      rm -f "$AUTH_KEY_FILE"  # Clean up invalid file
      return 1
    fi
  fi
  
  # If we get here, we need to prompt the user
  log "INFO" "To set up non-interactive authentication, you need a service account key"
  log "INFO" "Please run ./setup_service_account.sh for guided setup"
  return 1
}

# Activate authentication with GCP
auth_activate() {
  if [[ -f "$AUTH_KEY_FILE" ]]; then
    log "INFO" "Authenticating with service account key"
    if gcloud auth activate-service-account --quiet --key-file="$AUTH_KEY_FILE" > /dev/null 2>&1; then
      export GOOGLE_APPLICATION_CREDENTIALS="$AUTH_KEY_FILE"
      log "SUCCESS" "Successfully authenticated with GCP"
      
      # Get the authenticated account
      ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "unknown")
      log "INFO" "Authenticated as: $ACCOUNT"
      
      return 0
    else
      log "ERROR" "Failed to authenticate with service account key"
      return 1
    fi
  elif [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
    log "INFO" "Authenticating with service account from environment variable"
    
    # Create temporary file
    local TEMP_FILE
    TEMP_FILE=$(mktemp)
    echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_FILE"
    
    if gcloud auth activate-service-account --quiet --key-file="$TEMP_FILE" > /dev/null 2>&1; then
      # Create the permanent file for future use
      mkdir -p "$(dirname "$AUTH_KEY_FILE")"
      cp "$TEMP_FILE" "$AUTH_KEY_FILE"
      chmod 600 "$AUTH_KEY_FILE"  # Secure permissions
      export GOOGLE_APPLICATION_CREDENTIALS="$AUTH_KEY_FILE"
      rm -f "$TEMP_FILE"  # Clean up temp file
      
      log "SUCCESS" "Successfully authenticated with GCP"
      
      # Get the authenticated account
      ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "unknown")
      log "INFO" "Authenticated as: $ACCOUNT"
      
      return 0
    else
      log "ERROR" "Failed to authenticate with service account from environment variable"
      rm -f "$TEMP_FILE"  # Clean up temp file
      return 1
    fi
  else
    log "WARN" "No service account credentials found, using default auth method"
    log "INFO" "To avoid interactive prompts, set up a service account key at $AUTH_KEY_FILE"
    return 1
  fi
}

# Get authentication token for API calls
auth_get_token() {
  if auth_check; then
    auth_activate > /dev/null
    TOKEN=$(gcloud auth print-identity-token 2>/dev/null)
    if [[ -n "$TOKEN" ]]; then
      echo "$TOKEN"
      return 0
    else
      log "ERROR" "Failed to get authentication token"
      return 1
    fi
  else
    log "ERROR" "Authentication not configured"
    return 1
  fi
}

# Get Docker mount parameters for authentication
auth_docker_mount() {
  local mount_params=""
  
  if [[ -f "$AUTH_KEY_FILE" ]]; then
    # Determine the correct mount path based on container setup
    local CONTAINER_PATH="/app/.gcp"
    
    # Check if a custom path was provided
    if [[ -n "$1" ]]; then
      CONTAINER_PATH="$1"
    fi
    
    # Create the mount directory in the container
    mkdir -p "$(dirname "$AUTH_KEY_FILE")"
    
    # Return the mount parameter
    echo "-v $HOME/.gcp:$CONTAINER_PATH:ro -e GOOGLE_APPLICATION_CREDENTIALS=$CONTAINER_PATH/service-account.json"
  fi
}

# Main script functionality when sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  # Script is being sourced
  if [[ "$1" == "--help" ]]; then
    auth_help
  elif [[ "$1" == "--auth" ]]; then
    auth_activate
  fi
else
  # Script is being executed directly
  log "INFO" "This script should be sourced, not executed"
  log "INFO" "Use: source $(basename "$0")"
  exit 1
fi

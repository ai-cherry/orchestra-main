#!/bin/bash
#
# Setup Service Account for AI Orchestra GCP Migration
#
# This script downloads the service account key from GitHub secrets
# or creates a dummy key file for testing
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

# Default values
KEY_DIR="gcp_migration/keys"
mkdir -p "$KEY_DIR"
SA_KEY_PATH="$KEY_DIR/org-policy-manager-sa.json"
TEST_KEY_PATH="$KEY_DIR/dummy-test-key.json"
LOG_FILE="gcp_migration/migration_logs/setup_sa_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

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
  
  echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# Function to create a dummy service account key for testing
create_dummy_key() {
  log "STEP" "Creating dummy service account key for testing"
  
  cat > "$TEST_KEY_PATH" << EOF
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "dummy_key_id_for_testing",
  "private_key": "-----BEGIN PRIVATE KEY-----\ndummy_key_for_testing\n-----END PRIVATE KEY-----\n",
  "client_email": "org-policy-manager-sa@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "104285551098275703787",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/org-policy-manager-sa%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  
  log "INFO" "Dummy service account key created at $TEST_KEY_PATH"
  log "WARNING" "This is NOT a real key and will not work for authentication"
  log "INFO" "Use this path only for testing the script flow without authentication"
  
  echo "$TEST_KEY_PATH"
}

# Function to get service account key from environment or setup
get_service_account_key() {
  log "STEP" "Getting service account key"
  
  # Check if key already exists
  if [ -f "$SA_KEY_PATH" ]; then
    log "INFO" "Service account key already exists at $SA_KEY_PATH"
    echo "$SA_KEY_PATH"
    return 0
  fi
  
  # Check if key exists in environment
  if [ -n "$GCP_ORGANIZATION_POLICY_JSON" ]; then
    log "INFO" "Found GCP_ORGANIZATION_POLICY_JSON in environment"
    echo "$GCP_ORGANIZATION_POLICY_JSON" > "$SA_KEY_PATH"
    log "INFO" "Service account key saved to $SA_KEY_PATH"
    echo "$SA_KEY_PATH"
    return 0
  fi
  
  # Ask user for key path or to paste content
  log "INFO" "Service account key not found in environment."
  log "INFO" "Options:"
  log "INFO" "1. Enter path to existing service account key file"
  log "INFO" "2. Paste service account key JSON content"
  log "INFO" "3. Create dummy key for testing script flow (will not work for actual auth)"
  log "INFO" "4. Skip key setup (will need to provide key later)"
  
  read -p "Select option (1-4): " OPTION
  
  case $OPTION in
    1)
      log "INFO" "Enter the path to the service account key file:"
      read -p "Path: " KEY_FILE_PATH
      
      if [ -f "$KEY_FILE_PATH" ]; then
        cp "$KEY_FILE_PATH" "$SA_KEY_PATH"
        log "INFO" "Service account key copied to $SA_KEY_PATH"
        echo "$SA_KEY_PATH"
        return 0
      else
        log "ERROR" "File not found: $KEY_FILE_PATH"
        return 1
      fi
      ;;
    2)
      log "INFO" "Paste the service account JSON below and press Ctrl+D when done:"
      SA_JSON=$(cat)
      echo "$SA_JSON" > "$SA_KEY_PATH"
      log "INFO" "Service account key saved to $SA_KEY_PATH"
      echo "$SA_KEY_PATH"
      return 0
      ;;
    3)
      create_dummy_key
      return 0
      ;;
    4)
      log "INFO" "Skipping key setup"
      return 1
      ;;
    *)
      log "ERROR" "Invalid option"
      return 1
      ;;
  esac
}

# Function to verify service account key
verify_service_account_key() {
  local key_path="$1"
  
  log "STEP" "Verifying service account key"
  
  # Check if key exists
  if [ ! -f "$key_path" ]; then
    log "ERROR" "Service account key not found at $key_path"
    return 1
  fi
  
  # Check key format
  if ! jq -e . "$key_path" > /dev/null 2>&1; then
    log "ERROR" "Service account key is not valid JSON"
    return 1
  fi
  
  # Check key content
  local client_email
  client_email=$(jq -r '.client_email' "$key_path" 2>/dev/null)
  
  if [ -z "$client_email" ] || [ "$client_email" == "null" ]; then
    log "ERROR" "Service account key missing client_email field"
    return 1
  fi
  
  log "INFO" "Service account key validated for: $client_email"
  
  # Try to authenticate
  log "INFO" "Testing authentication with gcloud..."
  if GOOGLE_APPLICATION_CREDENTIALS="$key_path" gcloud auth application-default print-access-token &>/dev/null; then
    log "INFO" "Authentication successful!"
    return 0
  else
    log "WARNING" "Authentication failed or skipped for testing"
    return 1
  fi
}

# Function to set up environment variables
setup_environment() {
  local key_path="$1"
  
  log "STEP" "Setting up environment variables"
  
  # Check if key exists
  if [ ! -f "$key_path" ]; then
    log "ERROR" "Service account key not found at $key_path"
    return 1
  fi
  
  # Set environment variables
  export GOOGLE_APPLICATION_CREDENTIALS="$key_path"
  export GCP_ORGANIZATION_POLICY_JSON=$(cat "$key_path")
  
  log "INFO" "Environment variables set:"
  log "INFO" "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
  log "INFO" "GCP_ORGANIZATION_POLICY_JSON is set with the key content"
  
  # Generate export commands for the user
  cat > setup_env.sh << EOF
#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="$key_path"
export GCP_ORGANIZATION_POLICY_JSON=\$(cat "$key_path")
EOF
  
  chmod +x setup_env.sh
  log "INFO" "Environment setup script created at: setup_env.sh"
  log "INFO" "Run 'source setup_env.sh' to set environment variables in your shell"
  
  return 0
}

# Main function
main() {
  log "INFO" "Starting service account setup for AI Orchestra GCP migration"
  
  # Get service account key
  local key_path
  if ! key_path=$(get_service_account_key); then
    log "WARNING" "Service account key setup skipped or failed"
    return 1
  fi
  
  # Verify service account key
  if ! verify_service_account_key "$key_path"; then
    log "WARNING" "Service account key verification failed"
    log "INFO" "You may proceed with a dummy key for testing script flow only"
  fi
  
  # Setup environment variables
  if ! setup_environment "$key_path"; then
    log "WARNING" "Environment setup failed"
    return 1
  fi
  
  log "INFO" "Service account setup completed successfully"
  log "INFO" "You can now run the migration scripts with proper authentication"
  log "INFO" "Next step: ./gcp_migration/migrate_to_gcp.sh"
  
  return 0
}

# Execute main function
main "$@"
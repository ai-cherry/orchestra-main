#!/bin/bash
#
# Create Service Account Key for Organization Policy Manager
#
# This script creates a service account key for the organization policy manager
# service account to use in the migration process
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
PROJECT_ID="cherry-ai-project"
SERVICE_ACCOUNT="org-policy-manager-sa@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_DIR="gcp_migration/keys"
mkdir -p "$KEY_DIR"
KEY_FILE="$KEY_DIR/org-policy-manager-key.json"

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

# Function to check if service account exists
check_service_account() {
  log "STEP" "Checking if service account exists"
  
  if gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
    log "INFO" "Service account $SERVICE_ACCOUNT exists"
    return 0
  else
    log "WARNING" "Service account $SERVICE_ACCOUNT not found"
    return 1
  fi
}

# Function to create service account if it doesn't exist
create_service_account() {
  log "STEP" "Creating service account"
  
  log "INFO" "Creating service account: $SERVICE_ACCOUNT"
  gcloud iam service-accounts create "org-policy-manager-sa" \
    --project="$PROJECT_ID" \
    --display-name="Organization Policy Manager Service Account" \
    --description="Service account for managing organization policies during migration"
    
  log "INFO" "Service account created successfully"
}

# Function to grant necessary permissions to service account
grant_permissions() {
  log "STEP" "Granting permissions to service account"
  
  # Grant Organization Policy Admin role
  log "INFO" "Granting Organization Policy Admin role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/orgpolicy.policyAdmin"
    
  # Grant Vertex AI Admin role
  log "INFO" "Granting Vertex AI Admin role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.admin"
    
  # Grant Cloud Run Admin role
  log "INFO" "Granting Cloud Run Admin role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.admin"
    
  # Grant Project IAM Admin role
  log "INFO" "Granting Project IAM Admin role"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/resourcemanager.projectIamAdmin"
    
  log "INFO" "Permissions granted successfully"
}

# Function to create service account key
create_service_account_key() {
  log "STEP" "Creating service account key"
  
  if [ -f "$KEY_FILE" ]; then
    log "WARNING" "Key file already exists at $KEY_FILE"
    read -p "Overwrite? (y/n): " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy] ]]; then
      log "INFO" "Using existing key file"
      return 0
    fi
  fi
  
  log "INFO" "Creating new service account key"
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT" \
    --project="$PROJECT_ID"
    
  log "INFO" "Service account key created at: $KEY_FILE"
}

# Function to set up environment variables
setup_environment() {
  log "STEP" "Setting up environment variables"
  
  export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
  export GCP_ORGANIZATION_POLICY_JSON=$(cat "$KEY_FILE")
  
  log "INFO" "Environment variables set:"
  log "INFO" "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
  log "INFO" "GCP_ORGANIZATION_POLICY_JSON is set with the key content"

  # Create an environment script for future use
  cat > setup_policy_manager_env.sh << EOF
#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
export GCP_ORGANIZATION_POLICY_JSON=\$(cat "$KEY_FILE")
EOF

  chmod +x setup_policy_manager_env.sh
  
  log "INFO" "Created environment script: setup_policy_manager_env.sh"
  log "INFO" "Run 'source setup_policy_manager_env.sh' to set up these variables in future sessions"
}

# Function to test authentication
test_authentication() {
  log "STEP" "Testing authentication"
  
  log "INFO" "Testing authentication with gcloud"
  if gcloud auth activate-service-account --key-file="$KEY_FILE"; then
    log "INFO" "Authentication successful"
    
    # Test listing organization policies
    log "INFO" "Testing organization policy listing"
    gcloud org-policies list --project="$PROJECT_ID"
    
    return 0
  else
    log "ERROR" "Authentication failed"
    return 1
  fi
}

# Main function
main() {
  log "INFO" "Starting service account key creation for organization policy manager"
  
  # Check if service account exists
  if ! check_service_account; then
    create_service_account
  fi
  
  # Grant permissions
  grant_permissions
  
  # Create service account key
  create_service_account_key
  
  # Setup environment variables
  setup_environment
  
  # Test authentication
  if test_authentication; then
    log "INFO" "Service account key creation and setup completed successfully"
    log "INFO" "You can now use the organization policy manager service account for GCP migration"
  else
    log "ERROR" "Service account authentication failed"
    log "INFO" "Please check the service account permissions and try again"
    exit 1
  fi
}

# Execute main function
main "$@"
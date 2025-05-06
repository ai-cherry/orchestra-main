#!/bin/bash
# setup_wif_codespaces.sh - Configure GitHub Codespaces to use Workload Identity Federation
# This script sets up authentication for Codespaces using GitHub's OIDC token

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration - Set defaults but allow override through environment variables
: "${GCP_PROJECT_ID:=cherry-ai-project}"
: "${GITHUB_ORG:=ai-cherry}"
: "${GITHUB_REPO:=orchestra-main}"
: "${SERVICE_ACCOUNT:=codespaces-dev@${GCP_PROJECT_ID}.iam.gserviceaccount.com}"

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
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not found"
    log "INFO" "Installing gcloud CLI..."
    curl -sSL https://sdk.cloud.google.com | bash
    exec -l $SHELL
    gcloud init
  fi
  
  # Check for GitHub token
  if [[ -z "${GITHUB_TOKEN}" ]]; then
    log "ERROR" "GITHUB_TOKEN environment variable is required"
    log "INFO" "This should be automatically set in Codespaces"
    exit 1
  fi
  
  log "INFO" "All requirements satisfied"
}

# Configure gcloud for WIF
configure_gcloud_wif() {
  log "INFO" "Configuring gcloud for Workload Identity Federation..."
  
  # Create credential configuration directory
  mkdir -p ~/.config/gcloud/workload_identity
  
  # Create GitHub token file
  mkdir -p ~/.github
  echo "${GITHUB_TOKEN}" > ~/.github/token
  chmod 600 ~/.github/token
  
  # Create credential configuration file
  cat > ~/.config/gcloud/workload_identity/config.json << EOF
{
  "type": "external_account",
  "audience": "//iam.googleapis.com/projects/${GCP_PROJECT_ID}/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider",
  "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
  "token_url": "https://sts.googleapis.com/v1/token",
  "credential_source": {
    "file": "${HOME}/.github/token",
    "format": {
      "type": "text"
    }
  },
  "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${SERVICE_ACCOUNT}:generateAccessToken"
}
EOF
  
  # Configure gcloud to use the WIF configuration
  gcloud auth login --cred-file=~/.config/gcloud/workload_identity/config.json
  
  # Set default project
  gcloud config set project "${GCP_PROJECT_ID}"
  
  log "INFO" "gcloud configured to use Workload Identity Federation"
}

# Add helper functions to bashrc
add_helper_functions() {
  log "INFO" "Adding helper functions to bashrc..."
  
  # Create helper script to refresh GitHub token
  cat > ~/refresh_github_token.sh << 'EOF'
#!/bin/bash
# This script refreshes the GitHub token for WIF authentication

# Get GitHub token from environment
if [[ -n "${GITHUB_TOKEN}" ]]; then
  echo "${GITHUB_TOKEN}" > ~/.github/token
  chmod 600 ~/.github/token
  echo "GitHub token refreshed"
else
  echo "Error: GITHUB_TOKEN environment variable not set"
  exit 1
fi
EOF
  chmod +x ~/refresh_github_token.sh
  
  # Add to bashrc if not already present
  if ! grep -q "refresh-wif-token" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# WIF authentication helpers
alias refresh-wif-token='~/refresh_github_token.sh'
alias check-wif-auth='gcloud auth list'
EOF
  fi
  
  log "INFO" "Helper functions added to bashrc"
}

# Configure Docker credential helper
configure_docker() {
  log "INFO" "Configuring Docker credential helper..."
  
  # Install Docker credential helper
  gcloud components install docker-credential-gcr
  
  # Configure Docker to use gcloud credential helper
  mkdir -p ~/.docker
  cat > ~/.docker/config.json << EOF
{
  "credHelpers": {
    "gcr.io": "gcloud",
    "us.gcr.io": "gcloud",
    "eu.gcr.io": "gcloud",
    "asia.gcr.io": "gcloud",
    "staging-k8s.gcr.io": "gcloud",
    "marketplace.gcr.io": "gcloud"
  }
}
EOF
  
  log "INFO" "Docker credential helper configured"
}

# Configure VS Code extensions
configure_vscode() {
  log "INFO" "Configuring VS Code extensions..."
  
  # Check if running in Codespaces
  if [[ -n "${CODESPACES}" ]]; then
    # Create VS Code settings directory if it doesn't exist
    mkdir -p ~/.vscode-remote/data/Machine
    
    # Configure Cloud Code extension settings
    cat > ~/.vscode-remote/data/Machine/settings.json << EOF
{
  "cloudcode.project": "${GCP_PROJECT_ID}",
  "cloudcode.region": "us-west4",
  "cloudcode.gke.cluster": "",
  "cloudcode.cloud-run.project": "${GCP_PROJECT_ID}",
  "cloudcode.cloud-run.region": "us-west4"
}
EOF
    
    log "INFO" "VS Code extensions configured"
  else
    log "WARN" "Not running in Codespaces, skipping VS Code configuration"
  fi
}

# Test authentication
test_authentication() {
  log "INFO" "Testing authentication..."
  
  # Test gcloud authentication
  if gcloud auth list | grep -q "ACTIVE"; then
    log "INFO" "gcloud authentication successful"
  else
    log "ERROR" "gcloud authentication failed"
    return 1
  fi
  
  # Test access to GCP resources
  if gcloud projects describe "${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Successfully accessed GCP project"
  else
    log "ERROR" "Failed to access GCP project"
    return 1
  fi
  
  # Test access to Secret Manager
  if gcloud secrets list --project="${GCP_PROJECT_ID}" &>/dev/null; then
    log "INFO" "Successfully accessed Secret Manager"
  else
    log "WARN" "Failed to access Secret Manager (may be due to permissions)"
  fi
  
  log "INFO" "Authentication tests completed"
  return 0
}

# Main function
main() {
  log "INFO" "Starting Workload Identity Federation setup for Codespaces..."
  
  # Check requirements
  check_requirements
  
  # Configure gcloud for WIF
  configure_gcloud_wif
  
  # Add helper functions to bashrc
  add_helper_functions
  
  # Configure Docker credential helper
  configure_docker
  
  # Configure VS Code extensions
  configure_vscode
  
  # Test authentication
  if test_authentication; then
    log "INFO" "Workload Identity Federation setup complete!"
    log "INFO" "You can now use gcloud, Docker, and other GCP tools with WIF authentication"
  else
    log "ERROR" "Authentication test failed. Please check the logs for details"
    exit 1
  fi
}

# Execute main function
main
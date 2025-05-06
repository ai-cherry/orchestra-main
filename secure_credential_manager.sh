#!/bin/bash
# secure_credential_manager.sh
#
# This script provides a command-line interface for the credential manager.
# It allows users to:
# - Secure exposed credentials
# - Get credential information
# - Set up environment variables for credentials

set -e

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT=$(pwd)
PYTHON_CMD="python3"

# Function to print section header
print_header() {
  echo -e "\n${BLUE}${BOLD}$1${NC}"
  echo -e "${BLUE}${BOLD}$(printf '=%.0s' $(seq 1 ${#1}))${NC}"
}

# Function to print success message
print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error message
print_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Function to print warning message
print_warning() {
  echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to print info message
print_info() {
  echo -e "${BLUE}ℹ️ $1${NC}"
}

# Function to check if Python is available
check_python() {
  if ! command -v $PYTHON_CMD &> /dev/null; then
    print_error "Python is not installed or not in PATH"
    exit 1
  fi
  
  print_success "Python is available: $($PYTHON_CMD --version)"
}

# Function to secure exposed credentials
secure_credentials() {
  print_header "Securing Exposed Credentials"
  
  # Create the core/security directory if it doesn't exist
  mkdir -p "$PROJECT_ROOT/core/security"
  
  # Check if the credential manager exists
  if [ ! -f "$PROJECT_ROOT/core/security/credential_manager.py" ]; then
    print_error "Credential manager not found at $PROJECT_ROOT/core/security/credential_manager.py"
    exit 1
  fi
  
  # Run the credential manager to secure credentials
  print_info "Running credential manager to secure credentials..."
  $PYTHON_CMD "$PROJECT_ROOT/core/security/credential_manager.py"
  
  # Check if service account key files still exist
  if [ -f "$PROJECT_ROOT/service-account-key.json" ]; then
    print_warning "Service account key file still exists at $PROJECT_ROOT/service-account-key.json"
    print_info "Removing file..."
    rm -f "$PROJECT_ROOT/service-account-key.json"
  fi
  
  if [ -f "$PROJECT_ROOT/.credentials/service-account-key.json" ]; then
    print_warning "Service account key file still exists at $PROJECT_ROOT/.credentials/service-account-key.json"
    print_info "Removing file..."
    rm -f "$PROJECT_ROOT/.credentials/service-account-key.json"
  fi
  
  print_success "Credentials secured successfully"
}

# Function to create a sanitized service account key template
create_sanitized_template() {
  print_header "Creating Sanitized Service Account Key Template"
  
  cat > "$PROJECT_ROOT/sanitized-service-account-key-template.json" << EOF
{
  "type": "service_account",
  "project_id": "PROJECT_ID",
  "private_key_id": "PRIVATE_KEY_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nPRIVATE_KEY_CONTENTS_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com",
  "client_id": "CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/SERVICE_ACCOUNT_NAME%40PROJECT_ID.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  
  print_success "Created sanitized template at $PROJECT_ROOT/sanitized-service-account-key-template.json"
}

# Function to set up environment variables
setup_env_vars() {
  print_header "Setting Up Environment Variables"
  
  # Check if .env file exists
  if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_info "Creating .env file..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env" 2>/dev/null || touch "$PROJECT_ROOT/.env"
  fi
  
  # Get project ID from credential manager
  print_info "Getting project ID from credential manager..."
  PROJECT_ID=$($PYTHON_CMD -c "from core.security.credential_manager import CredentialManager; cm = CredentialManager(); print(cm.get_project_id() or '')")
  
  if [ -n "$PROJECT_ID" ]; then
    print_info "Setting ORCHESTRA_PROJECT_ID=$PROJECT_ID in .env file..."
    grep -q "^ORCHESTRA_PROJECT_ID=" "$PROJECT_ROOT/.env" && \
      sed -i "s/^ORCHESTRA_PROJECT_ID=.*/ORCHESTRA_PROJECT_ID=$PROJECT_ID/" "$PROJECT_ROOT/.env" || \
      echo "ORCHESTRA_PROJECT_ID=$PROJECT_ID" >> "$PROJECT_ROOT/.env"
    
    print_success "Environment variables set up successfully"
  else
    print_warning "Could not get project ID from credential manager"
  fi
}

# Function to display help
show_help() {
  echo "Usage: $0 [command]"
  echo ""
  echo "Commands:"
  echo "  secure              Secure exposed credentials"
  echo "  template            Create a sanitized service account key template"
  echo "  env                 Set up environment variables"
  echo "  help                Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 secure           # Secure exposed credentials"
  echo "  $0 template         # Create a sanitized service account key template"
  echo "  $0 env              # Set up environment variables"
}

# Main function
main() {
  # Check if Python is available
  check_python
  
  # Parse command line arguments
  if [ $# -eq 0 ]; then
    show_help
    exit 0
  fi
  
  case "$1" in
    secure)
      secure_credentials
      ;;
    template)
      create_sanitized_template
      ;;
    env)
      setup_env_vars
      ;;
    help)
      show_help
      ;;
    *)
      print_error "Unknown command: $1"
      show_help
      exit 1
      ;;
  esac
}

# Run the main function
main "$@"
#!/bin/bash
# auth_examples.sh - Examples of using the non-interactive authentication tools
# This script demonstrates how to use the authentication helpers in various contexts

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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
    "HEADER")
      color=$BOLD
      ;;
  esac
  
  echo -e "${color}[$level] $message${NC}"
}

# Section divider
section() {
  echo ""
  log "HEADER" "=== $1 ==="
  echo ""
}

# Check dependencies
check_dependencies() {
  section "Checking Dependencies"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is required but not installed"
    log "INFO" "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
  log "SUCCESS" "gcloud is installed"
  
  # Check for python
  if ! command -v python3 &> /dev/null; then
    log "WARN" "python3 is recommended but not installed"
  else
    log "SUCCESS" "python3 is installed"
  fi
  
  # Check for jq
  if ! command -v jq &> /dev/null; then
    log "WARN" "jq is recommended but not installed (install with: apt-get install jq)"
  else
    log "SUCCESS" "jq is installed"
  fi
  
  # Check for docker
  if ! command -v docker &> /dev/null; then
    log "WARN" "docker is recommended but not installed"
  else
    log "SUCCESS" "docker is installed"
  fi
}

# Example 1: Basic shell script authentication
example_basic_shell() {
  section "Example 1: Basic Shell Authentication"
  
  log "INFO" "Attempting to authenticate with GCP..."
  
  if [[ -f "$HOME/.gcp/service-account.json" ]]; then
    log "INFO" "Using service account key from $HOME/.gcp/service-account.json"
    gcloud auth activate-service-account --quiet --key-file="$HOME/.gcp/service-account.json"
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcp/service-account.json"
    log "SUCCESS" "Authentication successful"
    log "INFO" "Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
  elif [[ -n "$GCP_MASTER_SERVICE_JSON" ]]; then
    log "INFO" "Using service account key from environment variable"
    TEMP_FILE=$(mktemp)
    echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_FILE"
    gcloud auth activate-service-account --quiet --key-file="$TEMP_FILE"
    mkdir -p "$HOME/.gcp"
    cp "$TEMP_FILE" "$HOME/.gcp/service-account.json"
    chmod 600 "$HOME/.gcp/service-account.json"
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcp/service-account.json"
    rm -f "$TEMP_FILE"
    log "SUCCESS" "Authentication successful"
    log "INFO" "Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
  else
    log "WARN" "No service account credentials found"
    log "INFO" "To avoid interactive prompts, set up a service account key at $HOME/.gcp/service-account.json"
    log "INFO" "Using browser-based authentication (not recommended for automation)"
    log "INFO" "Run ./setup_service_account.sh to set up non-interactive authentication"
  fi
}

# Example 2: Using auth_helper.sh
example_auth_helper() {
  section "Example 2: Using auth_helper.sh"
  
  log "INFO" "Sourcing auth_helper.sh..."
  if [[ -f "auth_helper.sh" ]]; then
    # Source the helper functions
    source auth_helper.sh
    
    # Check if authentication is configured
    if auth_check; then
      log "SUCCESS" "Authentication is configured"
      
      # Activate authentication
      if auth_activate; then
        log "SUCCESS" "Authentication successful"
        
        # Run some authenticated commands
        log "INFO" "Checking authenticated account..."
        ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
        log "INFO" "Authenticated as: $ACCOUNT"
        
        # Get auth token for API calls
        TOKEN=$(auth_get_token)
        if [[ -n "$TOKEN" ]]; then
          log "SUCCESS" "Got authentication token: ${TOKEN:0:10}..."
        else
          log "ERROR" "Failed to get authentication token"
        fi
        
        # Get Docker mount parameters
        DOCKER_MOUNT=$(auth_docker_mount)
        if [[ -n "$DOCKER_MOUNT" ]]; then
          log "INFO" "Docker mount parameters: $DOCKER_MOUNT"
        else
          log "WARN" "No Docker mount parameters available"
        fi
      else
        log "ERROR" "Authentication failed"
      fi
    else
      log "WARN" "Authentication is not configured"
      
      # Try to set up authentication
      if auth_setup; then
        log "SUCCESS" "Authentication is now configured"
        auth_activate
      else
        log "ERROR" "Failed to set up authentication"
      fi
    fi
  else
    log "ERROR" "auth_helper.sh not found in current directory"
  fi
}

# Example 3: Using Python module
example_python_module() {
  section "Example 3: Using Python Authentication Module"
  
  if command -v python3 &> /dev/null; then
    log "INFO" "Testing Python authentication module..."
    
    if [[ -f "gcp_auth.py" ]]; then
      log "INFO" "Running authentication check with Python module..."
      if python3 -c "import gcp_auth; print('Authentication is configured: ' + str(gcp_auth.check_auth_configured()))"; then
        log "SUCCESS" "Python module imported successfully"
        
        log "INFO" "Attempting authentication with Python module..."
        if python3 -c "import gcp_auth; print('Authentication successful: ' + str(gcp_auth.authenticate()))"; then
          log "SUCCESS" "Python authentication successful"
          
          # Example of getting a token
          log "INFO" "Getting authentication token..."
          TOKEN=$(python3 -c "import gcp_auth; token = gcp_auth.get_auth_token(); print(token if token else '')")
          if [[ -n "$TOKEN" ]]; then
            log "SUCCESS" "Got authentication token: ${TOKEN:0:10}..."
          else
            log "WARN" "No authentication token available"
          fi
        else
          log "ERROR" "Python authentication failed"
        fi
      else
        log "ERROR" "Failed to import Python module"
      fi
    else
      log "ERROR" "gcp_auth.py not found in current directory"
    fi
  else
    log "WARN" "Python 3 not available, skipping Python examples"
  fi
}

# Example 4: Deploying with authenticated Docker
example_docker_auth() {
  section "Example 4: Docker Authentication Integration"
  
  if command -v docker &> /dev/null; then
    log "INFO" "Testing Docker authentication integration..."
    
    # Source the auth helper if available
    if [[ -f "auth_helper.sh" ]]; then
      source auth_helper.sh
      
      # Get Docker mount parameters
      DOCKER_MOUNT=$(auth_docker_mount)
      
      if [[ -n "$DOCKER_MOUNT" ]]; then
        log "INFO" "Using Docker mount parameters: $DOCKER_MOUNT"
        
        # Example Docker command with auth
        log "INFO" "Example Docker command:"
        echo -e "${YELLOW}docker run -it --rm $DOCKER_MOUNT python:3.9-slim bash -c 'echo \$GOOGLE_APPLICATION_CREDENTIALS && ls -la \$(dirname \$GOOGLE_APPLICATION_CREDENTIALS)'${NC}"
        
        log "INFO" "This would mount your credentials into the container"
      else
        log "WARN" "No Docker mount parameters available"
        log "INFO" "Please set up authentication with ./setup_service_account.sh"
      fi
    else
      log "ERROR" "auth_helper.sh not found in current directory"
    fi
  else
    log "WARN" "Docker not available, skipping Docker examples"
  fi
}

# Example 5: Integrating with deploy.sh
example_deploy_integration() {
  section "Example 5: Integration with deploy.sh"
  
  if [[ -f "deploy.sh" ]]; then
    log "INFO" "The deploy.sh script already has integrated authentication"
    log "INFO" "It will use service account credentials if available"
    log "INFO" "Example usage:"
    echo -e "${YELLOW}./deploy.sh --project my-project-id --region us-central1 --service my-service${NC}"
    
    log "INFO" "It uses this authentication logic:"
    # shellcheck disable=SC2155
    export HIGHLIGHT=$(grep -n "Try to authenticate with service account" deploy.sh | cut -d: -f1)
    if [[ -n "$HIGHLIGHT" ]]; then
      HIGHLIGHT=$((HIGHLIGHT - 1))
      END=$((HIGHLIGHT + 15))
      log "INFO" "Excerpt from deploy.sh (lines $HIGHLIGHT-$END):"
      sed -n "${HIGHLIGHT},${END}p" deploy.sh | sed 's/^/  /'
    else
      log "ERROR" "Could not find authentication logic in deploy.sh"
    fi
  else
    log "WARN" "deploy.sh not found in current directory"
  fi
}

# Main function to run all examples
main() {
  echo "===================================================="
  echo "  AI ORCHESTRA AUTHENTICATION EXAMPLES"
  echo "===================================================="
  echo ""
  
  check_dependencies
  example_basic_shell
  example_auth_helper
  example_python_module
  example_docker_auth
  example_deploy_integration
  
  echo ""
  echo "===================================================="
  echo "  AUTHENTICATION EXAMPLES COMPLETE"
  echo "===================================================="
  echo ""
  log "INFO" "To set up non-interactive authentication, run:"
  echo -e "${GREEN}./setup_service_account.sh${NC}"
}

# Run main function
main

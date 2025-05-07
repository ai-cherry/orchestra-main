#!/bin/bash
# entrypoint.sh - Entrypoint script for AI Orchestra Docker container
# Handles startup tasks like environment setup and authentication

set -e

# Function to log messages
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if running in GCP environment
check_gcp_environment() {
  # Check for GCP metadata server
  if curl --silent --fail "http://metadata.google.internal/computeMetadata/v1/instance/id" -H "Metadata-Flavor: Google" > /dev/null 2>&1; then
    log "Running in GCP environment"
    return 0
  else
    log "Not running in GCP environment"
    return 1
  fi
}

# Set up GCP authentication if needed
setup_gcp_auth() {
  # If GOOGLE_APPLICATION_CREDENTIALS is set and the file exists, use it
  if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS}" && -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
    log "Using service account key from GOOGLE_APPLICATION_CREDENTIALS"
    gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
    return 0
  fi

  # If running in GCP, use the default service account
  if check_gcp_environment; then
    log "Using GCP metadata server for authentication"
    # No explicit auth needed in Cloud Run, it uses the attached service account
    return 0
  fi

  # If no authentication method is available, warn but continue
  log "WARNING: No GCP authentication method available"
  return 1
}

# Set up environment variables
setup_environment() {
  # Set default environment variables if not already set
  export ENVIRONMENT=${ENVIRONMENT:-"dev"}
  export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
  
  # Set project ID from environment or try to get it from GCP
  if [[ -z "${PROJECT_ID}" ]]; then
    if check_gcp_environment; then
      PROJECT_ID=$(curl --silent "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")
      export PROJECT_ID
    else
      export PROJECT_ID="cherry-ai-project"
    fi
  fi
  
  log "Environment: ${ENVIRONMENT}"
  log "Project ID: ${PROJECT_ID}"
  log "Log level: ${LOG_LEVEL}"
}

# Main function
main() {
  log "Starting AI Orchestra application"
  
  # Set up environment
  setup_environment
  
  # Set up GCP authentication
  setup_gcp_auth
  
  # Execute the command passed to the entrypoint
  log "Executing command: ${*}"
  exec "${@}"
}

# Run main function with all arguments
main "$@"
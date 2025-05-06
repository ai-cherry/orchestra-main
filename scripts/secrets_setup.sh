#!/bin/bash
# secrets_setup.sh - Enhanced version with Gemini integration

set -eo pipefail

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--project) PROJECT="$2"; shift ;;
    -f|--file) SECRET_FILE="$2"; shift ;;
    -s|--secret) SECRET_NAME="$2"; shift ;;
    -a|--service-account) SA="$2"; shift ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

# Gemini-generated validation checks
validate_environment() {
  if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found"
    exit 1
  fi
  
  if [[ ! -f "$SECRET_FILE" ]]; then
    echo "Error: Secret file not found (path omitted for security)"
    exit 1
  fi

  # Check file permissions to ensure it's not world-readable
  if [[ $(stat -c "%a" "$SECRET_FILE" 2>/dev/null || stat -f "%p" "$SECRET_FILE" 2>/dev/null) =~ [67][0-7][0-7] ]]; then
    echo "Error: Secret file has insecure permissions (accessible to others)"
    exit 1
  fi
}

# Main execution flow
main() {
  validate_environment
  
  # Enable Secret Manager API
  gcloud services enable secretmanager.googleapis.com --project="$PROJECT"
  
  # Create/update secret
  if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT" >/dev/null 2>&1; then
    echo "Updating existing secret (name omitted for security)"
    echo -n "v$(date +%s)" | gcloud secrets versions add "$SECRET_NAME" \
      --data-file="$SECRET_FILE" \
      --project="$PROJECT" 2>/dev/null
    if [ $? -ne 0 ]; then
      echo "Error: Failed to update secret (details omitted for security)"
      exit 1
    fi
  else
    echo "Creating new secret (name omitted for security)"
    gcloud secrets create "$SECRET_NAME" \
      --replication-policy=automatic \
      --data-file="$SECRET_FILE" \
      --project="$PROJECT" 2>/dev/null
    if [ $? -ne 0 ]; then
      echo "Error: Failed to create secret (details omitted for security)"
      exit 1
    fi
  fi

  # Set IAM permissions
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT"
    
  echo "Secret setup complete (details omitted for security)"
}

main "$@"

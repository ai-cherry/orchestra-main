#!/bin/bash
# migrate_workflow_to_wif.sh - Migrate GitHub Actions workflows to use Workload Identity Federation
# This script updates GitHub Actions workflow files to use WIF authentication instead of service account keys

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
: "${WORKFLOWS_DIR:=.github/workflows}"
: "${BACKUP_DIR:=.github/workflows/backups}"

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

# Check if a workflow file uses service account keys
uses_service_account_keys() {
  local file=$1
  grep -q "credentials_json" "$file"
}

# Check if a workflow file already uses WIF
uses_wif() {
  local file=$1
  grep -q "workload_identity_provider" "$file" && ! grep -q "# workload_identity_provider" "$file"
}

# Create backup of a workflow file
backup_workflow() {
  local file=$1
  local backup_file="${BACKUP_DIR}/$(basename "$file").bak.$(date +%Y%m%d%H%M%S)"
  
  # Create backup directory if it doesn't exist
  mkdir -p "${BACKUP_DIR}"
  
  # Create backup
  cp "$file" "$backup_file"
  log "INFO" "Created backup: $backup_file"
}

# Migrate a workflow file to use WIF
migrate_workflow() {
  local file=$1
  local tmp_file=$(mktemp)
  
  log "INFO" "Migrating workflow: $file"
  
  # Create backup
  backup_workflow "$file"
  
  # Process the file
  awk '
  {
    # Print the current line
    print $0;
    
    # If we find the google-github-actions/auth action
    if ($0 ~ /google-github-actions\/auth/) {
      # Read the next line (with)
      getline;
      print $0;
      
      # Check if the next line contains credentials_json
      getline;
      if ($0 ~ /credentials_json/) {
        # Replace credentials_json with workload_identity_provider
        sub(/credentials_json/, "workload_identity_provider");
        sub(/\$\{\{ secrets\.GCP_.*_JSON \}\}/, "${{ secrets.WIF_PROVIDER_ID }}");
        print $0;
        
        # Add service_account line
        print "          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}";
      } else {
        # If not credentials_json, just print the line
        print $0;
      }
    }
  }
  ' "$file" > "$tmp_file"
  
  # Check if the file was modified
  if diff -q "$file" "$tmp_file" > /dev/null; then
    log "WARN" "No changes were made to $file"
    rm "$tmp_file"
    return 1
  else
    # Replace the original file
    mv "$tmp_file" "$file"
    log "INFO" "Successfully migrated $file to use WIF"
    return 0
  fi
}

# Main function
main() {
  log "INFO" "Starting GitHub Actions workflow migration to WIF..."
  
  # Check if workflows directory exists
  if [ ! -d "$WORKFLOWS_DIR" ]; then
    log "ERROR" "Workflows directory not found: $WORKFLOWS_DIR"
    exit 1
  fi
  
  # Find all workflow files
  WORKFLOW_FILES=$(find "$WORKFLOWS_DIR" -name "*.yml" -o -name "*.yaml" | grep -v "backups")
  
  if [ -z "$WORKFLOW_FILES" ]; then
    log "WARN" "No workflow files found in $WORKFLOWS_DIR"
    exit 0
  fi
  
  log "INFO" "Found $(echo "$WORKFLOW_FILES" | wc -l) workflow files"
  
  # Process each workflow file
  MIGRATED=0
  ALREADY_USING_WIF=0
  NO_AUTH=0
  
  for file in $WORKFLOW_FILES; do
    log "INFO" "Processing $file"
    
    if uses_wif "$file"; then
      log "INFO" "$file already uses WIF, skipping"
      ALREADY_USING_WIF=$((ALREADY_USING_WIF + 1))
    elif uses_service_account_keys "$file"; then
      if migrate_workflow "$file"; then
        MIGRATED=$((MIGRATED + 1))
      fi
    else
      log "INFO" "$file does not use GCP authentication, skipping"
      NO_AUTH=$((NO_AUTH + 1))
    fi
  done
  
  log "INFO" "Migration complete!"
  log "INFO" "Summary:"
  log "INFO" "  - Migrated: $MIGRATED"
  log "INFO" "  - Already using WIF: $ALREADY_USING_WIF"
  log "INFO" "  - No GCP authentication: $NO_AUTH"
  log "INFO" "  - Total workflows: $(echo "$WORKFLOW_FILES" | wc -l)"
  
  if [ $MIGRATED -gt 0 ]; then
    log "INFO" "Next steps:"
    log "INFO" "1. Review the migrated workflows"
    log "INFO" "2. Commit and push the changes"
    log "INFO" "3. Test the workflows to ensure they work with WIF"
  fi
}

# Execute main function
main
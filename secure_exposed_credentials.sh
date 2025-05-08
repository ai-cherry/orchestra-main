#!/bin/bash
# secure_exposed_credentials.sh - Simplified version for single-developer project
# Focuses on essential credential protection without excessive measures

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log function with simplified output
log() {
  local level=$1
  local message=$2
  
  case $level in
    "INFO")
      echo -e "${GREEN}[INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[ERROR] ${message}${NC}"
      ;;
  esac
}

# Find and secure service account key files - essential protection
find_and_secure_key_files() {
  log "INFO" "Finding and securing service account key files..."
  
  # Find JSON files that might contain service account keys
  local key_files=$(find . -type f -name "*key*.json" -o -name "*credential*.json" | grep -v "node_modules")
  
  for file in ${key_files}; do
    # Check if the file contains "private_key"
    if grep -q "private_key" "${file}"; then
      log "WARN" "Found service account key file: ${file}"
      
      # Add to gitignore directly instead of modifying the file
      echo "${file}" >> .gitignore
      log "INFO" "Added ${file} to .gitignore"
    fi
  done
}

# Add common credential files to .gitignore
add_to_gitignore() {
  log "INFO" "Adding sensitive files to .gitignore..."
  
  # Check if .gitignore exists
  if [ ! -f ".gitignore" ]; then
    touch .gitignore
  fi
  
  # Add service account key files to .gitignore
  echo "" >> .gitignore
  echo "# Service account key files" >> .gitignore
  echo "*-key.json" >> .gitignore
  echo "*credential*.json" >> .gitignore
  
  log "INFO" "Added sensitive files to .gitignore"
}

# Main function - simplified for essential protection
main() {
  log "INFO" "Starting simplified credential security process..."
  
  # Find and secure service account key files
  find_and_secure_key_files
  
  # Add files to .gitignore
  add_to_gitignore
  
  log "INFO" "Credential security process completed"
  log "INFO" "Remember to avoid committing sensitive files"
}

# Execute main function
main
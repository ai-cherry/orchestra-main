#!/bin/bash
# secure_exposed_credentials.sh - Secure any exposed credentials in the repository

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Find and secure service account key files
find_and_secure_key_files() {
  log "INFO" "Finding and securing service account key files..."
  
  # Find all JSON files that might contain service account keys
  local key_files=$(find . -type f -name "*.json" | grep -v "node_modules" | grep -v "package-lock.json" | grep -v "package.json")
  
  for file in ${key_files}; do
    # Check if the file contains "private_key" which is a good indicator of a service account key
    if grep -q "private_key" "${file}"; then
      log "WARN" "Found potential service account key file: ${file}"
      
      # Backup the file
      cp "${file}" "${file}.bak"
      
      # Replace the private key with a placeholder
      sed -i 's/-----BEGIN PRIVATE KEY-----.*-----END PRIVATE KEY-----/-----BEGIN PRIVATE KEY-----REDACTED-----END PRIVATE KEY-----/g' "${file}"
      
      # Replace the private_key_id with a placeholder
      sed -i 's/"private_key_id": "[^"]*"/"private_key_id": "REDACTED"/g' "${file}"
      
      log "SUCCESS" "Secured service account key file: ${file}"
    fi
  done
  
  log "INFO" "Service account key files secured"
}

# Find and secure credentials in shell scripts
find_and_secure_credentials_in_scripts() {
  log "INFO" "Finding and securing credentials in shell scripts..."
  
  # Find all shell scripts
  local script_files=$(find . -type f -name "*.sh" | grep -v "node_modules")
  
  for file in ${script_files}; do
    # Check if the file contains potential credentials
    if grep -q -E "(password|token|key|secret|credential)" "${file}"; then
      log "WARN" "Found potential credentials in script: ${file}"
      
      # Backup the file
      cp "${file}" "${file}.bak"
      
      # Replace potential credentials with placeholders
      sed -i 's/\(password\|token\|key\|secret\|credential\)="[^"]*"/\1="REDACTED"/g' "${file}"
      sed -i "s/\(password\|token\|key\|secret\|credential\)='[^']*'/\1='REDACTED'/g" "${file}"
      
      log "SUCCESS" "Secured credentials in script: ${file}"
    fi
  done
  
  log "INFO" "Credentials in shell scripts secured"
}

# Find and secure credentials in YAML files
find_and_secure_credentials_in_yaml() {
  log "INFO" "Finding and securing credentials in YAML files..."
  
  # Find all YAML files
  local yaml_files=$(find . -type f -name "*.yml" -o -name "*.yaml" | grep -v "node_modules")
  
  for file in ${yaml_files}; do
    # Check if the file contains potential credentials
    if grep -q -E "(password|token|key|secret|credential)" "${file}"; then
      log "WARN" "Found potential credentials in YAML file: ${file}"
      
      # Backup the file
      cp "${file}" "${file}.bak"
      
      # Replace potential credentials with placeholders
      sed -i 's/\(password\|token\|key\|secret\|credential\): "[^"]*"/\1: "REDACTED"/g' "${file}"
      sed -i "s/\(password\|token\|key\|secret\|credential\): '[^']*'/\1: 'REDACTED'/g" "${file}"
      
      log "SUCCESS" "Secured credentials in YAML file: ${file}"
    fi
  done
  
  log "INFO" "Credentials in YAML files secured"
}

# Find and secure credentials in Python files
find_and_secure_credentials_in_python() {
  log "INFO" "Finding and securing credentials in Python files..."
  
  # Find all Python files
  local python_files=$(find . -type f -name "*.py" | grep -v "node_modules")
  
  for file in ${python_files}; do
    # Check if the file contains potential credentials
    if grep -q -E "(password|token|key|secret|credential)" "${file}"; then
      log "WARN" "Found potential credentials in Python file: ${file}"
      
      # Backup the file
      cp "${file}" "${file}.bak"
      
      # Replace potential credentials with placeholders
      sed -i 's/\(password\|token\|key\|secret\|credential\) = "[^"]*"/\1 = "REDACTED"/g' "${file}"
      sed -i "s/\(password\|token\|key\|secret\|credential\) = '[^']*'/\1 = 'REDACTED'/g" "${file}"
      
      log "SUCCESS" "Secured credentials in Python file: ${file}"
    fi
  done
  
  log "INFO" "Credentials in Python files secured"
}

# Add files to .gitignore
add_to_gitignore() {
  log "INFO" "Adding sensitive files to .gitignore..."
  
  # Check if .gitignore exists
  if [ ! -f ".gitignore" ]; then
    log "WARN" ".gitignore file not found, creating one"
    touch .gitignore
  fi
  
  # Add service account key files to .gitignore
  echo "" >> .gitignore
  echo "# Service account key files" >> .gitignore
  echo "*.json.bak" >> .gitignore
  echo "*-key.json" >> .gitignore
  echo "secret-management-key.json" >> .gitignore
  echo "project-admin-key.json" >> .gitignore
  
  log "SUCCESS" "Added sensitive files to .gitignore"
}

# Main function
main() {
  log "INFO" "Starting credential security process..."
  
  # Find and secure service account key files
  find_and_secure_key_files
  
  # Find and secure credentials in shell scripts
  find_and_secure_credentials_in_scripts
  
  # Find and secure credentials in YAML files
  find_and_secure_credentials_in_yaml
  
  # Find and secure credentials in Python files
  find_and_secure_credentials_in_python
  
  # Add files to .gitignore
  add_to_gitignore
  
  log "SUCCESS" "Credential security process completed successfully!"
  log "INFO" "Backup files have been created with the .bak extension"
  log "INFO" "Please review the changes and commit them if they look good"
}

# Execute main function
main
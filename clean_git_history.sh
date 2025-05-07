#!/bin/bash
# clean_git_history.sh - Clean the git history to remove any sensitive credentials

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
    "STEP")
      echo -e "\n${BLUE}[${timestamp}] [STEP] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Check requirements
check_requirements() {
  log "STEP" "Checking requirements..."
  
  # Check for git
  if ! command -v git &> /dev/null; then
    log "ERROR" "git is required but not found"
    exit 1
  fi
  
  # Check if we're in a git repository
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    log "ERROR" "Not in a git repository"
    exit 1
  fi
  
  log "SUCCESS" "All requirements satisfied"
}

# Confirm with the user
confirm() {
  log "WARN" "This script will rewrite the git history to remove sensitive credentials."
  log "WARN" "This is a destructive operation and cannot be undone."
  log "WARN" "If you have already pushed the repository, you will need to force push after this operation."
  log "WARN" "Make sure you have a backup of the repository before proceeding."
  
  read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
  echo
  
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "INFO" "Operation cancelled"
    exit 0
  fi
}

# Find sensitive files
find_sensitive_files() {
  log "STEP" "Finding sensitive files..."
  
  # Find all files that might contain sensitive credentials
  local sensitive_files=$(git grep -l -E "(password|token|key|secret|credential)" -- "*.json" "*.sh" "*.yml" "*.yaml" "*.py" | grep -v "node_modules" | grep -v "package-lock.json" | grep -v "package.json")
  
  if [ -z "${sensitive_files}" ]; then
    log "INFO" "No sensitive files found"
    return
  fi
  
  log "WARN" "Found the following sensitive files:"
  echo "${sensitive_files}"
  
  # Create a .gitignore entry for these files
  echo "" >> .gitignore
  echo "# Sensitive files" >> .gitignore
  for file in ${sensitive_files}; do
    echo "${file}" >> .gitignore
  done
  
  log "SUCCESS" "Added sensitive files to .gitignore"
}

# Clean the git history
clean_git_history() {
  log "STEP" "Cleaning the git history..."
  
  # Create a temporary directory for the clean repository
  local temp_dir=$(mktemp -d)
  
  # Clone the repository without the history
  git clone --depth 1 . "${temp_dir}"
  
  # Remove the .git directory
  rm -rf .git
  
  # Copy the clean repository
  cp -r "${temp_dir}/.git" .
  
  # Clean up
  rm -rf "${temp_dir}"
  
  # Initialize the repository
  git init
  
  # Add all files
  git add .
  
  # Commit the changes
  git commit -m "Initial commit (cleaned history)"
  
  log "SUCCESS" "Git history cleaned successfully"
}

# Alternative: Use BFG Repo-Cleaner
use_bfg() {
  log "STEP" "Using BFG Repo-Cleaner to clean the git history..."
  
  # Check if BFG is available
  if ! command -v bfg &> /dev/null; then
    log "WARN" "BFG Repo-Cleaner not found, downloading..."
    
    # Download BFG
    curl -L -o bfg.jar https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
    
    # Check if Java is available
    if ! command -v java &> /dev/null; then
      log "ERROR" "Java is required to run BFG Repo-Cleaner but not found"
      log "INFO" "Please install Java or use the alternative method"
      return 1
    fi
    
    # Create a text file with the sensitive patterns
    echo "password" > sensitive-patterns.txt
    echo "token" >> sensitive-patterns.txt
    echo "key" >> sensitive-patterns.txt
    echo "secret" >> sensitive-patterns.txt
    echo "credential" >> sensitive-patterns.txt
    
    # Run BFG
    java -jar bfg.jar --replace-text sensitive-patterns.txt .
    
    # Clean up
    rm -f bfg.jar sensitive-patterns.txt
  else
    # Create a text file with the sensitive patterns
    echo "password" > sensitive-patterns.txt
    echo "token" >> sensitive-patterns.txt
    echo "key" >> sensitive-patterns.txt
    echo "secret" >> sensitive-patterns.txt
    echo "credential" >> sensitive-patterns.txt
    
    # Run BFG
    bfg --replace-text sensitive-patterns.txt .
    
    # Clean up
    rm -f sensitive-patterns.txt
  fi
  
  # Run git garbage collection
  git gc --aggressive --prune=now
  
  log "SUCCESS" "Git history cleaned successfully using BFG Repo-Cleaner"
}

# Main function
main() {
  log "INFO" "Starting git history cleaning process..."
  
  # Check requirements
  check_requirements
  
  # Confirm with the user
  confirm
  
  # Find sensitive files
  find_sensitive_files
  
  # Ask the user which method to use
  log "INFO" "There are two methods to clean the git history:"
  log "INFO" "1. Clean the git history by creating a new repository (recommended)"
  log "INFO" "2. Use BFG Repo-Cleaner to clean the git history (requires Java)"
  
  read -p "Which method do you want to use? (1/2) " -n 1 -r
  echo
  
  if [[ $REPLY =~ ^[1]$ ]]; then
    clean_git_history
  elif [[ $REPLY =~ ^[2]$ ]]; then
    use_bfg
  else
    log "ERROR" "Invalid choice"
    exit 1
  fi
  
  log "SUCCESS" "Git history cleaning process completed successfully!"
  log "INFO" "You may need to force push the changes with 'git push --force'"
}

# Execute main function
main
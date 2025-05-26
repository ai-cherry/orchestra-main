#!/bin/bash
# Workspace Cleanup Script
# This script helps clean up your Orchestra workspace and return to a cleaner state
# Last updated: May 2025

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Orchestra Workspace Cleanup${NC}"

# Function to clean up temporary files
cleanup_temp_files() {
  echo -e "${YELLOW}Cleaning up temporary files...${NC}"
  find . -name "*.tmp" -type f -delete
  find . -name "*.bak" -type f -delete
  find . -name "*.swp" -type f -delete
  find . -name "*~" -type f -delete
  find . -name ".DS_Store" -type f -delete
  echo -e "${GREEN}Temporary files cleaned up.${NC}"
}

# Function to clean up cache directories
cleanup_cache_dirs() {
  echo -e "${YELLOW}Cleaning up cache directories...${NC}"
  find . -name "__pycache__" -type d -exec rm -rf {} +
  find . -name ".pytest_cache" -type d -exec rm -rf {} +
  find . -name ".ruff_cache" -type d -exec rm -rf {} +
  find . -name ".mypy_cache" -type d -exec rm -rf {} +
  echo -e "${GREEN}Cache directories cleaned up.${NC}"
}

# Function to clean up node_modules
cleanup_node_modules() {
  echo -e "${YELLOW}Cleaning up node modules...${NC}"
  find . -name "node_modules" -type d -exec rm -rf {} +
  echo -e "${GREEN}Node modules cleaned up.${NC}"
}

# Function to clean up build artifacts
cleanup_build_artifacts() {
  echo -e "${YELLOW}Cleaning up build artifacts...${NC}"
  find . -name "build" -type d -exec rm -rf {} +
  find . -name "dist" -type d -exec rm -rf {} +
  find . -name "*.egg-info" -type d -exec rm -rf {} +
  echo -e "${GREEN}Build artifacts cleaned up.${NC}"
}

# Function to reset permissions
reset_permissions() {
  echo -e "${YELLOW}Resetting file permissions...${NC}"
  find . -type f -not -path "*/\.*" -exec chmod 644 {} \;
  find . -type d -not -path "*/\.*" -exec chmod 755 {} \;
  find . -name "*.sh" -type f -exec chmod +x {} \;
  find . -name "*.py" -type f -exec chmod 644 {} \;
  echo -e "${GREEN}File permissions reset.${NC}"
}

# Function to clean up git conflicts
cleanup_git_conflicts() {
  echo -e "${YELLOW}Checking for git conflict markers...${NC}"
  CONFLICT_FILES=$(grep -l "<<<<<<< HEAD" $(find . -type f -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/.venv/*" | grep -v "node_modules"))

  if [ -z "$CONFLICT_FILES" ]; then
    echo -e "${GREEN}No git conflict markers found.${NC}"
  else
    echo -e "${RED}Files with conflict markers found:${NC}"
    echo "$CONFLICT_FILES"
    echo
    read -p "Would you like to edit these files to resolve conflicts? (y/n): " RESOLVE
    if [ "$RESOLVE" = "y" ]; then
      for FILE in $CONFLICT_FILES; do
        $EDITOR "$FILE"
      done
    fi
  fi
}

# Function to check for and fix Poetry lock
check_poetry_lock() {
  echo -e "${YELLOW}Checking Poetry setup...${NC}"
  if [ -f "pyproject.toml" ] && [ -f "poetry.lock" ]; then
    echo -e "Found Poetry configuration files."
    read -p "Would you like to regenerate the Poetry lock file? (y/n): " REGEN_LOCK
    if [ "$REGEN_LOCK" = "y" ]; then
      echo -e "${YELLOW}Regenerating Poetry lock file...${NC}"
      rm -f poetry.lock
      poetry lock
      echo -e "${GREEN}Poetry lock file regenerated.${NC}"
    fi
  else
    echo -e "${YELLOW}No Poetry configuration found.${NC}"
  fi
}

# Function to clean up database files
cleanup_db_files() {
  echo -e "${YELLOW}Checking for database files...${NC}"
  DB_FILES=$(find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3")
  if [ -z "$DB_FILES" ]; then
    echo -e "${GREEN}No database files found.${NC}"
  else
    echo -e "${YELLOW}Found database files:${NC}"
    echo "$DB_FILES"
    read -p "Would you like to delete these database files? (y/n): " DELETE_DB
    if [ "$DELETE_DB" = "y" ]; then
      for FILE in $DB_FILES; do
        rm -f "$FILE"
        echo -e "${GREEN}Deleted: $FILE${NC}"
      done
    fi
  fi
}

# Function to remove unused Docker images
cleanup_docker_images() {
  echo -e "${YELLOW}Removing unused Docker images and containers...${NC}"
  docker container prune -f
  docker image prune -f
  docker network prune -f
  docker volume prune -f
  echo -e "${GREEN}Unused Docker resources removed.${NC}"
}

# Function to remove unused Terraform state files
cleanup_terraform_state_files() {
  echo -e "${YELLOW}Removing local Terraform state files...${NC}"
  find . -name "*.tfstate*" -exec rm -f {} \;
  find . -name ".terraform.lock.hcl" -exec rm -f {} \;
  find . -name ".terraform" -type d -exec rm -rf {} \;
  echo -e "${GREEN}Local Terraform state files removed.${NC}"
}

# Function to clean up GCP service account keys
cleanup_gcp_keys() {
  echo -e "${YELLOW}Checking for GCP service account keys...${NC}"
  KEY_FILES=$(find /tmp -name "*-key.json" 2>/dev/null)
  KEY_FILES+=" "$(find . -name "*-key.json" -o -name "*sa*.json" | grep -v node_modules)

  if [ -z "$KEY_FILES" ]; then
    echo -e "${GREEN}No GCP service account key files found.${NC}"
  else
    echo -e "${RED}Found potential service account key files:${NC}"
    echo "$KEY_FILES"
    read -p "Would you like to securely delete these key files? (y/n): " DELETE_KEYS
    if [ "$DELETE_KEYS" = "y" ];then
      for FILE in $KEY_FILES; do
        if [ -f "$FILE" ]; then
          shred -uz "$FILE"
          echo -e "${GREEN}Securely deleted: $FILE${NC}"
        fi
      done
    fi
  fi

  # Also check for environment variables with credentials
  if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}GOOGLE_APPLICATION_CREDENTIALS environment variable is set to:${NC}"
    echo -e "${YELLOW}$GOOGLE_APPLICATION_CREDENTIALS${NC}"
    read -p "Would you like to unset this environment variable? (y/n): " UNSET_VAR
    if [ "$UNSET_VAR" = "y" ]; then
      unset GOOGLE_APPLICATION_CREDENTIALS
      echo -e "${GREEN}GOOGLE_APPLICATION_CREDENTIALS unset.${NC}"
    fi
  fi
}

# Function to revoke gcloud authentication
cleanup_gcloud_auth() {
  echo -e "${YELLOW}Checking gcloud authentication...${NC}"
  if command -v gcloud &> /dev/null; then
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
    if [ -n "$ACTIVE_ACCOUNT" ]; then
      echo -e "${YELLOW}Currently authenticated as: $ACTIVE_ACCOUNT${NC}"
      read -p "Would you like to revoke this authentication? (y/n): " REVOKE_AUTH
      if [ "$REVOKE_AUTH" = "y" ]; then
        gcloud auth revoke "$ACTIVE_ACCOUNT"
        echo -e "${GREEN}Authentication revoked for: $ACTIVE_ACCOUNT${NC}"
      fi
    else
      echo -e "${GREEN}No active gcloud authentication found.${NC}"
    fi
  else
    echo -e "${YELLOW}gcloud CLI not found. Skipping auth cleanup.${NC}"
  fi
}

# Function to clean Workload Identity Federation configurations
cleanup_workload_identity() {
  echo -e "${YELLOW}Checking for Workload Identity Federation configurations...${NC}"
  if command -v gcloud &> /dev/null; then
    WIF_CONFIG=$(gcloud iam workload-identity-pools list --format="value(name)" 2>/dev/null)
    if [ -n "$WIF_CONFIG" ]; then
      echo -e "${YELLOW}Found Workload Identity Federation configurations:${NC}"
      echo "$WIF_CONFIG"
      echo -e "${YELLOW}Note: These configurations are managed in GCP and won't be deleted here.${NC}"
      echo -e "${YELLOW}Use 'orchestra_wif_master.sh' to manage these configurations.${NC}"
    else
      echo -e "${GREEN}No Workload Identity Federation configurations found.${NC}"
    fi
  else
    echo -e "${YELLOW}gcloud CLI not found. Skipping Workload Identity Federation cleanup.${NC}"
  fi
}

# Function to clean GitHub CLI authentication
cleanup_github_auth() {
  echo -e "${YELLOW}Checking GitHub CLI authentication...${NC}"
  if command -v gh &> /dev/null; then
    if gh auth status &>/dev/null; then
      GH_USER=$(gh api user -q '.login' 2>/dev/null)
      echo -e "${YELLOW}Currently authenticated as GitHub user: $GH_USER${NC}"
      read -p "Would you like to log out? (y/n): " LOGOUT
      if [ "$LOGOUT" = "y" ]; then
        gh auth logout
        echo -e "${GREEN}Logged out of GitHub CLI.${NC}"
      fi
    else
      echo -e "${GREEN}Not authenticated with GitHub CLI.${NC}"
    fi
  else
    echo -e "${YELLOW}GitHub CLI not found. Skipping GitHub auth cleanup.${NC}"
  fi
}

# Function to validate final cleanup plan
validate_final_cleanup_plan() {
  echo -e "${YELLOW}Validating final cleanup plan...${NC}"
  if [ -f final_cleanup_plan.md ]; then
    echo -e "${GREEN}Final cleanup plan found. Please review: final_cleanup_plan.md${NC}"
  else
    echo -e "${YELLOW}No final cleanup plan found. Skipping validation.${NC}"
  fi
}

# Main execution
echo -e "${BLUE}This script will help clean up your workspace.${NC}"
echo -e "${YELLOW}WARNING: This will delete files. Make sure you have backups if needed.${NC}"
echo

# Menu
echo -e "${BLUE}Please select cleanup options:${NC}"
echo "1) Clean up temporary files"
echo "2) Clean up cache directories"
echo "3) Clean up node_modules"
echo "4) Clean up build artifacts"
echo "5) Reset file permissions"
echo "6) Check for git conflicts"
echo "7) Fix Poetry lock issues"
echo "8) Clean up database files"
echo "9) Remove unused Docker resources"
echo "10) Remove unused Terraform state files"
echo "11) Clean up GCP service account keys"
echo "12) Revoke gcloud authentication"
echo "13) Check Workload Identity Federation configurations"
echo "14) Clean up GitHub CLI authentication"
echo "15) Validate final cleanup plan"
echo "16) Run all cleanup operations"
echo "0) Exit"
echo

read -p "Enter your choice(s) (e.g., 1 3 7): " CHOICES

for CHOICE in $CHOICES; do
  case $CHOICE in
    1) cleanup_temp_files ;;
    2) cleanup_cache_dirs ;;
    3) cleanup_node_modules ;;
    4) cleanup_build_artifacts ;;
    5) reset_permissions ;;
    6) cleanup_git_conflicts ;;
    7) check_poetry_lock ;;
    8) cleanup_db_files ;;
    9) cleanup_docker_images ;;
    10) cleanup_terraform_state_files ;;
    11) cleanup_gcp_keys ;;
    12) cleanup_gcloud_auth ;;
    13) cleanup_workload_identity ;;
    14) cleanup_github_auth ;;
    15) validate_final_cleanup_plan ;;
    16)
      cleanup_temp_files
      cleanup_cache_dirs
      cleanup_node_modules
      cleanup_build_artifacts
      reset_permissions
      cleanup_git_conflicts
      check_poetry_lock
      cleanup_db_files
      cleanup_docker_images
      cleanup_terraform_state_files
      cleanup_gcp_keys
      # Skip auth revocation in full cleanup mode to prevent accidental logout
      cleanup_workload_identity
      validate_final_cleanup_plan
      ;;
    0) exit 0 ;;
    *) echo -e "${RED}Invalid option: $CHOICE${NC}" ;;
  esac
done

echo -e "${GREEN}Cleanup operations completed!${NC}"
echo
echo -e "${BLUE}=== Recommended Next Steps ===${NC}"
echo -e "1. Run ${YELLOW}./execute_cleanup.sh${NC} if you need to perform the structured cleanup from the cleanup plan"
echo -e "2. Consider running ${YELLOW}./orchestra_wif_master.sh${NC} to migrate to Workload Identity Federation"
echo -e "3. Use ${YELLOW}terraform -chdir=terraform destroy${NC} to clean up cloud resources if needed"

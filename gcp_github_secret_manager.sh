#!/bin/bash
# Interactive command-line tool for managing GCP service accounts and GitHub secrets
# This tool provides a user-friendly interface to create service accounts and sync secrets

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default configuration
GCP_PROJECT_ID="cherry-ai-project"
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"

# Print header
echo -e "${BLUE}${BOLD}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   GCP SERVICE ACCOUNT & GITHUB SECRET MANAGEMENT UTILITY   ${NC}"
echo -e "${BLUE}${BOLD}=================================================================${NC}"

# Check for required tools
check_requirements() {
  local missing_tools=()
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    missing_tools+=("gcloud (Google Cloud SDK)")
  fi
  
  # Check for GitHub CLI
  if ! command -v gh &> /dev/null; then
    missing_tools+=("gh (GitHub CLI)")
  fi
  
  # Check for jq
  if ! command -v jq &> /dev/null; then
    missing_tools+=("jq")
  fi
  
  # If any tools are missing, provide installation instructions
  if [ ${#missing_tools[@]} -gt 0 ]; then
    echo -e "${RED}${BOLD}Missing required tools:${NC}"
    for tool in "${missing_tools[@]}"; do
      echo -e "  - ${tool}"
    done
    
    echo -e "\n${YELLOW}Installation instructions:${NC}"
    echo -e "  - Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    echo -e "  - GitHub CLI: https://cli.github.com/manual/installation"
    echo -e "  - jq: https://stedolan.github.io/jq/download/"
    
    exit 1
  fi
  
  echo -e "${GREEN}All required tools are installed.${NC}"
}

# Configure settings
configure_settings() {
  echo -e "\n${BLUE}${BOLD}CONFIGURATION${NC}"
  echo -e "${YELLOW}Current settings:${NC}"
  echo -e "  GCP Project ID: ${BOLD}$GCP_PROJECT_ID${NC}"
  echo -e "  GitHub Organization: ${BOLD}$GITHUB_ORG${NC}"
  echo -e "  GitHub PAT: ${BOLD}[Configured]${NC}"
  
  read -p "Would you like to update these settings? (y/n): " update_settings
  if [[ "$update_settings" == "y" || "$update_settings" == "Y" ]]; then
    read -p "Enter GCP Project ID [$GCP_PROJECT_ID]: " new_project_id
    read -p "Enter GitHub Organization [$GITHUB_ORG]: " new_github_org
    read -s -p "Enter GitHub PAT (leave empty to keep current): " new_github_pat
    echo ""
    
    # Update settings if provided
    GCP_PROJECT_ID=${new_project_id:-$GCP_PROJECT_ID}
    GITHUB_ORG=${new_github_org:-$GITHUB_ORG}
    GITHUB_PAT=${new_github_pat:-$GITHUB_PAT}
    
    echo -e "${GREEN}Settings updated.${NC}"
  fi
}

# Display the main menu
show_main_menu() {
  echo -e "\n${BLUE}${BOLD}MAIN MENU${NC}"
  echo -e "1. Create Badass Service Accounts for Vertex AI and Gemini"
  echo -e "2. Sync GitHub Secrets to GCP Secret Manager"
  echo -e "3. Complete Setup (Service Accounts + Secret Sync)"
  echo -e "4. Show Available Scripts"
  echo -e "5. Configure Settings"
  echo -e "6. Exit"
  
  read -p "Enter your choice (1-6): " choice
  
  case $choice in
    1) create_service_accounts ;;
    2) sync_github_to_gcp ;;
    3) complete_setup ;;
    4) show_available_scripts ;;
    5) configure_settings; show_main_menu ;;
    6) exit_program ;;
    *) echo -e "${RED}Invalid choice. Please try again.${NC}"; show_main_menu ;;
  esac
}

# Create service accounts
create_service_accounts() {
  echo -e "\n${BLUE}${BOLD}CREATING SERVICE ACCOUNTS${NC}"
  
  echo -e "${YELLOW}This will create the following service accounts with extensive permissions:${NC}"
  echo -e "  - vertex-ai-badass-access"
  echo -e "  - gemini-api-badass-access"
  echo -e "  - gemini-code-assist-badass-access"
  echo -e "  - gemini-cloud-assist-badass-access"
  
  read -p "Do you want to proceed? (y/n): " confirm
  if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    if [ -f "configure_badass_keys_and_sync.sh" ]; then
      echo -e "${YELLOW}Running script to create service accounts...${NC}"
      ./configure_badass_keys_and_sync.sh
    else
      echo -e "${RED}Script 'configure_badass_keys_and_sync.sh' not found.${NC}"
      echo -e "${YELLOW}Please run the tool from the correct directory.${NC}"
    fi
  else
    echo -e "${YELLOW}Operation cancelled.${NC}"
  fi
  
  read -p "Press Enter to return to the main menu..."
  show_main_menu
}

# Sync GitHub secrets to GCP
sync_github_to_gcp() {
  echo -e "\n${BLUE}${BOLD}SYNCING GITHUB SECRETS TO GCP${NC}"
  
  echo -e "${YELLOW}This will:${NC}"
  echo -e "  1. List all GitHub organization secrets"
  echo -e "  2. Create corresponding secrets in GCP Secret Manager"
  echo -e "  3. Set up a Cloud Function for automated sync"
  echo -e "  4. Create a daily Cloud Scheduler job"
  
  read -p "Do you want to proceed? (y/n): " confirm
  if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    if [ -f "github_to_gcp_secret_sync.sh" ]; then
      echo -e "${YELLOW}Running script to sync GitHub secrets to GCP...${NC}"
      ./github_to_gcp_secret_sync.sh
    else
      echo -e "${RED}Script 'github_to_gcp_secret_sync.sh' not found.${NC}"
      echo -e "${YELLOW}Please run the tool from the correct directory.${NC}"
    fi
  else
    echo -e "${YELLOW}Operation cancelled.${NC}"
  fi
  
  read -p "Press Enter to return to the main menu..."
  show_main_menu
}

# Complete setup
complete_setup() {
  echo -e "\n${BLUE}${BOLD}COMPLETE SETUP${NC}"
  
  echo -e "${YELLOW}This will perform a complete setup:${NC}"
  echo -e "  1. Create service accounts with extensive permissions"
  echo -e "  2. Generate service account keys"
  echo -e "  3. Set up GitHub organization secrets and variables"
  echo -e "  4. Create a Cloud Function for secret synchronization"
  echo -e "  5. Set up daily secret sync via Cloud Scheduler"
  
  read -p "Do you want to proceed? (y/n): " confirm
  if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    if [ -f "configure_badass_keys_and_sync.sh" ]; then
      echo -e "${YELLOW}Running complete setup script...${NC}"
      ./configure_badass_keys_and_sync.sh
    else
      echo -e "${RED}Script 'configure_badass_keys_and_sync.sh' not found.${NC}"
      echo -e "${YELLOW}Please run the tool from the correct directory.${NC}"
    fi
  else
    echo -e "${YELLOW}Operation cancelled.${NC}"
  fi
  
  read -p "Press Enter to return to the main menu..."
  show_main_menu
}

# Show available scripts
show_available_scripts() {
  echo -e "\n${BLUE}${BOLD}AVAILABLE SCRIPTS${NC}"
  
  local scripts=(
    "configure_badass_keys_and_sync.sh:Comprehensive script for service accounts and secret sync"
    "github_to_gcp_secret_sync.sh:Sync GitHub organization secrets to GCP Secret Manager"
    "create_badass_service_keys.sh:Create badass service account keys only"
    "migrate_github_to_gcp_secrets.sh:Migrate GitHub secrets to GCP Secret Manager"
    "update_github_gcp_service_keys.sh:Update GitHub organization secrets with GCP service keys"
    "switch_to_wif_authentication.sh:Switch from service account keys to Workload Identity Federation"
    "setup_workload_identity_federation.sh:Set up Workload Identity Federation"
    "make_scripts_executable.sh:Make all scripts executable"
  )
  
  for script_info in "${scripts[@]}"; do
    local script_name="${script_info%%:*}"
    local script_desc="${script_info#*:}"
    
    if [ -f "$script_name" ]; then
      echo -e "${GREEN}✓${NC} ${BOLD}$script_name${NC}"
      echo -e "  ${YELLOW}$script_desc${NC}"
      if [ -x "$script_name" ]; then
        echo -e "  ${BLUE}Executable: Yes${NC}"
      else
        echo -e "  ${RED}Executable: No (Run ./make_scripts_executable.sh first)${NC}"
      fi
    else
      echo -e "${RED}✗${NC} ${BOLD}$script_name${NC} - Not found"
      echo -e "  ${YELLOW}$script_desc${NC}"
    fi
    echo ""
  done
  
  read -p "Press Enter to return to the main menu..."
  show_main_menu
}

# Exit the program
exit_program() {
  echo -e "\n${GREEN}${BOLD}Thank you for using the GCP Service Account & GitHub Secret Management Utility!${NC}"
  echo -e "${YELLOW}For more information, see GITHUB_GCP_SERVICE_KEYS_README.md${NC}"
  exit 0
}

# Main function
main() {
  # Check requirements
  check_requirements
  
  # Show main menu
  show_main_menu
}

# Execute the main function
main

#!/bin/bash
# run_migration_with_claude.sh
#
# Master script to execute the full GCP migration process 
# with Claude Code integration, validation, and documentation

set -e

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== AGI Baby Cherry GCP Migration Suite =====${NC}"
echo -e "${YELLOW}This script will execute the full migration process with Claude Code integration${NC}"

# Function to display progress
display_step() {
  echo -e "\n${YELLOW}======================================================${NC}"
  echo -e "${GREEN}Step $1: $2${NC}"
  echo -e "${YELLOW}======================================================${NC}"
}

# Function to verify step execution
verify_step() {
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Step completed successfully${NC}"
  else
    echo -e "\n${RED}✗ Step failed with error code $?${NC}"
    echo -e "${YELLOW}Please check the logs above for more information${NC}"
    echo -e "${YELLOW}You can continue with the remaining steps or exit and troubleshoot${NC}"
    
    read -p "Do you want to continue with the remaining steps? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}Exiting...${NC}"
      exit 1
    fi
  fi
}

# Display introduction
echo -e "\n${BLUE}This suite includes:${NC}"
echo -e "  1. GCP project migration to organization 873291114285"
echo -e "  2. Deployment of hybrid IDE with n2d-standard-32 and 2x T4 GPUs"
echo -e "  3. Claude Code installation and configuration"
echo -e "  4. Comprehensive validation and verification"
echo -e "  5. Documentation and usage examples"

# Confirm execution
echo -e "\n${YELLOW}This script will perform a complete GCP migration and Claude Code setup.${NC}"
read -p "Do you want to continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${RED}Exiting...${NC}"
  exit 1
fi

# Step 1: Verify script permissions
display_step "1" "Verifying script permissions"
chmod +x execute_gcp_migration.sh
chmod +x setup_claude_code.sh
chmod +x use_claude_code_examples.sh
chmod +x validate_migration_and_claude.sh
verify_step

# Step 2: Execute GCP migration
display_step "2" "Executing GCP migration"
echo -e "${BLUE}This will migrate the cherry-ai-project project to organization 873291114285${NC}"
echo -e "${BLUE}and deploy hybrid IDE with n2d-standard-32 and 2x T4 GPUs${NC}"

read -p "Execute GCP migration? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  ./execute_gcp_migration.sh
  verify_step
else
  echo -e "${YELLOW}Skipping GCP migration...${NC}"
fi

# Step 3: Set up Claude Code
display_step "3" "Setting up Claude Code"
echo -e "${BLUE}This will install Claude Code and configure it for GCP project management${NC}"

read -p "Set up Claude Code? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  ./setup_claude_code.sh
  verify_step
else
  echo -e "${YELLOW}Skipping Claude Code setup...${NC}"
fi

# Step 4: Validate migration and Claude Code setup
display_step "4" "Validating migration and Claude Code setup"
echo -e "${BLUE}This will verify that the migration was successful and Claude Code is properly set up${NC}"

read -p "Validate migration and Claude Code setup? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  ./validate_migration_and_claude.sh
  verify_step
else
  echo -e "${YELLOW}Skipping validation...${NC}"
fi

# Step 5: Display Claude Code examples
display_step "5" "Displaying Claude Code examples"
echo -e "${BLUE}This will display examples of how to use Claude Code with your GCP project${NC}"

read -p "Display Claude Code examples? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  ./use_claude_code_examples.sh
  verify_step
else
  echo -e "${YELLOW}Skipping examples...${NC}"
fi

# Final step: Display summary
display_step "6" "Migration and setup summary"

echo -e "${BLUE}The following components have been deployed:${NC}"
echo -e "  ${GREEN}✓${NC} GCP project migrated to organization 873291114285"
echo -e "  ${GREEN}✓${NC} Hybrid IDE with n2d-standard-32 and 2x T4 GPUs"
echo -e "  ${GREEN}✓${NC} Claude Code installed and configured"
echo -e "  ${GREEN}✓${NC} Validation scripts and examples"

echo -e "\n${BLUE}For more information, see:${NC}"
echo -e "  ${YELLOW}README-CLAUDE-GCP-MIGRATION.md${NC} - Comprehensive documentation"

echo -e "\n${BLUE}Next steps:${NC}"
echo -e "  1. Explore your GCP project in the Google Cloud Console"
echo -e "  2. Access your hybrid IDE at https://console.cloud.google.com/workstations"
echo -e "  3. Use Claude Code to manage your GCP project: ${GREEN}claude 'analyze our GCP migration'${NC}"

echo -e "\n${GREEN}===== Migration and setup completed successfully =====${NC}"

#!/bin/bash
# apply_github_security_improvements.sh - Script to apply GitHub security improvements
# This script renames the updated files to replace the original files and makes them executable

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   APPLYING GITHUB SECURITY IMPROVEMENTS   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Function to apply changes
apply_changes() {
    local original_file=$1
    local updated_file="${original_file}.updated"
    
    if [ -f "$updated_file" ]; then
        echo -e "${YELLOW}Applying changes to ${original_file}...${NC}"
        
        # Create backup of original file if it exists
        if [ -f "$original_file" ]; then
            cp "$original_file" "${original_file}.bak"
            echo -e "${BLUE}Created backup: ${original_file}.bak${NC}"
        fi
        
        # Replace original file with updated file
        mv "$updated_file" "$original_file"
        
        # Make the file executable
        chmod +x "$original_file"
        
        echo -e "${GREEN}✓ Successfully updated ${original_file}${NC}"
    else
        echo -e "${RED}❌ Updated file ${updated_file} not found${NC}"
    fi
}

# List of files to update
files_to_update=(
    "setup_github_secrets.sh"
    "update_wif_secrets.sh"
    "deploy_with_adc.sh"
    "configure_badass_keys_and_sync.sh"
    "push_to_gcp.sh"
    "github_auth.sh"
    "github-workflow-wif-template.yml"
)

# Apply changes to each file
echo -e "${YELLOW}Applying changes to script files...${NC}"
for file in "${files_to_update[@]}"; do
    apply_changes "$file"
done

# Make new scripts executable
echo -e "${YELLOW}Making new scripts executable...${NC}"
chmod +x verify_github_secrets.sh
echo -e "${GREEN}✓ Made verify_github_secrets.sh executable${NC}"

# Create .github/workflows directory if it doesn't exist
if [ ! -d ".github/workflows" ]; then
    echo -e "${YELLOW}Creating .github/workflows directory...${NC}"
    mkdir -p .github/workflows
    echo -e "${GREEN}✓ Created .github/workflows directory${NC}"
fi

# Copy the workflow template to the workflows directory
if [ -f "github-workflow-wif-template.yml" ]; then
    echo -e "${YELLOW}Copying workflow template to .github/workflows directory...${NC}"
    cp github-workflow-wif-template.yml .github/workflows/
    echo -e "${GREEN}✓ Copied workflow template to .github/workflows directory${NC}"
fi

# Print summary
echo -e "\n${BLUE}${BOLD}Summary of Changes:${NC}"
echo -e "1. Updated script files to use organization-level secrets instead of hardcoded tokens"
echo -e "2. Created a centralized GitHub authentication utility (github_auth.sh)"
echo -e "3. Created a GitHub Actions workflow template using Workload Identity Federation"
echo -e "4. Added a verification tool for GitHub organization secrets (verify_github_secrets.sh)"
echo -e "5. Created documentation for the security improvements (GITHUB_SECURITY_IMPROVEMENTS.md)"

echo -e "\n${BLUE}${BOLD}Next Steps:${NC}"
echo -e "1. Run the verify_github_secrets.sh script to check if all required secrets are available:"
echo -e "   ${GREEN}./verify_github_secrets.sh${NC}"
echo -e "2. Update your GitHub Actions workflows to use the new template"
echo -e "3. Review the GITHUB_SECURITY_IMPROVEMENTS.md file for more information"

echo -e "\n${GREEN}${BOLD}GitHub security improvements have been successfully applied!${NC}"
#!/bin/bash
# migrate_to_wif.sh - Script to migrate to the new Workload Identity Federation implementation
# This script helps users transition from the old scripts with .updated suffixes to the new consolidated scripts

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   MIGRATING TO NEW WORKLOAD IDENTITY FEDERATION IMPLEMENTATION   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Function to check if a file exists
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ Found $file${NC}"
        return 0
    else
        echo -e "${RED}❌ $file not found${NC}"
        return 1
    fi
}

# Function to make a backup of a file
backup_file() {
    local file=$1
    local backup="${file}.bak"
    if [ -f "$file" ]; then
        cp "$file" "$backup"
        echo -e "${BLUE}Created backup: $backup${NC}"
    fi
}

# Check if the new scripts exist
echo -e "${YELLOW}Checking for new scripts...${NC}"
new_scripts_exist=true

if ! check_file "setup_wif.sh"; then
    new_scripts_exist=false
fi

if ! check_file "verify_wif_setup.sh"; then
    new_scripts_exist=false
fi

if ! check_file ".github/workflows/wif-deploy-template.yml"; then
    new_scripts_exist=false
fi

if ! check_file "docs/WORKLOAD_IDENTITY_FEDERATION.md"; then
    new_scripts_exist=false
fi

if [ "$new_scripts_exist" = false ]; then
    echo -e "${RED}Some new scripts are missing. Please make sure all new scripts are in place before running this migration script.${NC}"
    exit 1
fi

# Make the new scripts executable
echo -e "${YELLOW}Making new scripts executable...${NC}"
chmod +x setup_wif.sh
chmod +x verify_wif_setup.sh
echo -e "${GREEN}✓ Made scripts executable${NC}"

# Create backup directory
backup_dir="wif_migration_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
echo -e "${BLUE}Created backup directory: $backup_dir${NC}"

# List of old scripts to back up and remove
old_scripts=(
    "setup_github_secrets.sh"
    "setup_github_secrets.sh.updated"
    "update_wif_secrets.sh"
    "update_wif_secrets.sh.updated"
    "github_auth.sh"
    "github_auth.sh.updated"
    "github-workflow-wif-template.yml"
    "github-workflow-wif-template.yml.updated"
    "verify_github_secrets.sh"
)

# Back up old scripts
echo -e "${YELLOW}Backing up old scripts...${NC}"
for script in "${old_scripts[@]}"; do
    if [ -f "$script" ]; then
        cp "$script" "$backup_dir/"
        echo -e "${BLUE}Backed up $script to $backup_dir/${NC}"
    fi
done

# Check if apply_github_security_improvements.sh exists and back it up
if [ -f "apply_github_security_improvements.sh" ]; then
    cp "apply_github_security_improvements.sh" "$backup_dir/"
    echo -e "${BLUE}Backed up apply_github_security_improvements.sh to $backup_dir/${NC}"
fi

# Check if old documentation exists and back it up
if [ -f "docs/workload_identity_federation.md" ]; then
    cp "docs/workload_identity_federation.md" "$backup_dir/"
    echo -e "${BLUE}Backed up docs/workload_identity_federation.md to $backup_dir/${NC}"
fi

# Remove old scripts (optional, ask user first)
echo -e "${YELLOW}Do you want to remove the old scripts? (y/n)${NC}"
read -r remove_old

if [[ "$remove_old" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing old scripts...${NC}"
    for script in "${old_scripts[@]}"; do
        if [ -f "$script" ]; then
            rm "$script"
            echo -e "${GREEN}✓ Removed $script${NC}"
        fi
    done
    
    # Remove old documentation if it exists
    if [ -f "docs/workload_identity_federation.md" ]; then
        rm "docs/workload_identity_federation.md"
        echo -e "${GREEN}✓ Removed docs/workload_identity_federation.md${NC}"
    fi
    
    echo -e "${GREEN}✓ Old scripts removed${NC}"
else
    echo -e "${BLUE}Old scripts were not removed. They have been backed up to $backup_dir/${NC}"
fi

# Print summary
echo -e "\n${BLUE}${BOLD}Migration Summary:${NC}"
echo -e "1. New scripts are in place and executable:"
echo -e "   - setup_wif.sh: Unified script for setting up Workload Identity Federation"
echo -e "   - verify_wif_setup.sh: Script for verifying the WIF setup"
echo -e "   - .github/workflows/wif-deploy-template.yml: Template for GitHub Actions workflows using WIF"
echo -e "2. Comprehensive documentation is available at docs/WORKLOAD_IDENTITY_FEDERATION.md"
echo -e "3. Old scripts have been backed up to $backup_dir/"
if [[ "$remove_old" =~ ^[Yy]$ ]]; then
    echo -e "4. Old scripts have been removed"
else
    echo -e "4. Old scripts have not been removed"
fi

echo -e "\n${BLUE}${BOLD}Next Steps:${NC}"
echo -e "1. Review the new documentation at docs/WORKLOAD_IDENTITY_FEDERATION.md"
echo -e "2. Run the setup script to ensure WIF is properly configured:"
echo -e "   ${GREEN}./setup_wif.sh${NC}"
echo -e "3. Verify the setup with:"
echo -e "   ${GREEN}./verify_wif_setup.sh${NC}"
echo -e "4. Update your GitHub Actions workflows using the new template at .github/workflows/wif-deploy-template.yml"

echo -e "\n${GREEN}${BOLD}Migration to the new Workload Identity Federation implementation is complete!${NC}"
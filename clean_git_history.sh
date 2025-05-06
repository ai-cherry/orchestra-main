#!/bin/bash
# clean_git_history.sh - Remove sensitive files from git history

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}Cleaning Git history of sensitive files...${NC}"

# Create a backup branch
echo -e "${YELLOW}Creating backup branch...${NC}"
git branch -m main main_backup

# Create a new branch
echo -e "${YELLOW}Creating new clean branch...${NC}"
git checkout --orphan clean_main

# Add all files except sensitive ones
echo -e "${YELLOW}Adding all files except sensitive ones...${NC}"
git add .
git reset -- service-account-key.json .credentials/service-account-key.json 2>/dev/null || true

# Commit the changes
echo -e "${YELLOW}Committing changes...${NC}"
git config --local commit.gpgsign false
git commit -m "Initial commit with clean history"

# Force push to main
echo -e "${YELLOW}Force pushing to main...${NC}"
git push -f origin clean_main:main

# Checkout the new main branch
echo -e "${YELLOW}Checking out the new main branch...${NC}"
git checkout -b main origin/main

echo -e "${GREEN}Git history cleaned successfully!${NC}"
echo -e "${YELLOW}Note: The backup branch 'main_backup' contains the original history.${NC}"
echo -e "${YELLOW}You can delete it with 'git branch -D main_backup' if everything is working correctly.${NC}"
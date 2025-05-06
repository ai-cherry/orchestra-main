#!/bin/bash
# Script to install the enhanced pre-commit hook with Gemini-generated checks

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure we're in the project root (where .git exists)
if [ ! -d ".git" ]; then
  echo -e "${RED}Error: Not in project root directory (no .git directory found)${NC}"
  echo "Please run this script from the root of the repository."
  exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the hook template
if [ -f "scripts/pre-commit-hook-template" ]; then
  cp scripts/pre-commit-hook-template .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
  echo -e "${GREEN}Enhanced pre-commit hook successfully installed!${NC}"
  echo -e "${YELLOW}The hook will prevent committing:${NC}"
  echo "  - *.key (API keys and other sensitive key files)"
  echo "  - *gsa-key.json (Google Service Account key files)"
  echo "  - Text patterns matching API keys and credentials"
else
  echo -e "${RED}Error: Could not find scripts/pre-commit-hook-template${NC}"
  exit 1
fi

echo -e "\n${GREEN}Done!${NC} Your repository is now protected against accidental secret commits with enhanced AI-generated pattern detection."

#!/bin/bash
# apply_simplified_security.sh - Apply simplified security for single-developer use
# This script applies all the simplified security components to streamline development
# and removes unnecessary complex security files

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

section "Simplified Security for Single-Developer Projects"

echo "This script will apply simplified security components optimized for single-developer use."
echo "Unnecessary original files will be moved to an archived_security directory."
echo ""
echo -e "${YELLOW}Do you want to proceed? (y/n)${NC}"
read -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Operation cancelled.${NC}"
    exit 0
fi

section "Creating Archive Directory"

# Create archived_security directory if it doesn't exist
if [ ! -d "archived_security" ]; then
    mkdir -p archived_security
    echo -e "${GREEN}Created archived_security directory.${NC}"
fi

section "Making Scripts Executable"

# Make all the simplified scripts executable
echo "Making simplified scripts executable..."
chmod +x github_auth.sh.simplified
chmod +x verify_github_secrets.sh.simplified
chmod +x setup_wif.sh.simplified
echo -e "${GREEN}All simplified scripts are now executable.${NC}"

section "Replacing Original Files"

# Replace original files with simplified versions
echo "Replacing original files with simplified versions..."

# GitHub Authentication
if [ -f "github_auth.sh" ]; then
    echo "Moving original github_auth.sh to archive..."
    mv github_auth.sh archived_security/
fi
cp github_auth.sh.simplified github_auth.sh
chmod +x github_auth.sh
echo -e "${GREEN}Replaced: github_auth.sh with simplified version${NC}"

# GitHub Secrets Verification
if [ -f "verify_github_secrets.sh" ]; then
    echo "Moving original verify_github_secrets.sh to archive..."
    mv verify_github_secrets.sh archived_security/
fi
cp verify_github_secrets.sh.simplified verify_github_secrets.sh
chmod +x verify_github_secrets.sh
echo -e "${GREEN}Replaced: verify_github_secrets.sh with simplified version${NC}"

# WIF Setup
if [ -f "setup_wif.sh" ]; then
    echo "Moving original setup_wif.sh to archive..."
    mv setup_wif.sh archived_security/
fi
cp setup_wif.sh.simplified setup_wif.sh
chmod +x setup_wif.sh
echo -e "${GREEN}Replaced: setup_wif.sh with simplified version${NC}"

# GitHub Workflow Template
if [ -f ".github/workflows/wif-deploy-template.yml" ]; then
    echo "Moving original wif-deploy-template.yml to archive..."
    mv .github/workflows/wif-deploy-template.yml archived_security/
fi
echo -e "${GREEN}Kept simplified GitHub workflow template at .github/workflows/simplified-deploy-template.yml${NC}"

section "Archiving Unnecessary Files"

# Archive other unnecessary files
echo "Archiving unnecessary security files..."

FILES_TO_ARCHIVE=(
    "setup_github_secrets.sh.updated"
    "update_wif_secrets.sh.updated"
    "github-workflow-wif-template.yml.updated"
    "verify_wif_setup.sh"
    "migrate_to_wif.sh"
    "apply_github_security_improvements.sh"
    "GITHUB_SECURITY_IMPROVEMENTS.md"
    "WIF_IMPLEMENTATION_PLAN_README.md"
)

for file in "${FILES_TO_ARCHIVE[@]}"; do
    if [ -f "$file" ]; then
        echo "Moving $file to archive..."
        mv "$file" archived_security/
        echo -e "${GREEN}Archived: $file${NC}"
    fi
done

section "Setting Up Web Implementation"

# Update CSRF protection for web implementation
echo "Setting up development mode for CSRF protection..."

# Create a CSRF loader file to switch between production and development mode
cat > wif_implementation/csrf_loader.py << 'EOF'
"""
CSRF Protection Loader.

This module loads the appropriate CSRF protection implementation based on environment variables.
"""

import os
import logging

# Configure logging
logger = logging.getLogger("wif_implementation.csrf_loader")

# Check for development mode
DEV_MODE = os.environ.get("WIF_DEV_MODE", "false").lower() == "true"
BYPASS_CSRF = os.environ.get("WIF_BYPASS_CSRF", "false").lower() == "true"

if DEV_MODE:
    logger.info("Loading development CSRF protection")
    try:
        from .csrf_protection_dev import csrf_protection as csrf_protection
        from .csrf_protection_dev import csrf_protect_dev as csrf_protect
    except ImportError:
        logger.warning("Development CSRF protection not found, falling back to production version")
        from .csrf_protection import csrf_protection, csrf_protect
else:
    logger.info("Loading production CSRF protection")
    from .csrf_protection import csrf_protection, csrf_protect

__all__ = ["csrf_protection", "csrf_protect"]
EOF

echo -e "${GREEN}Created CSRF loader module to support both production and development modes${NC}"

section "Setting Up Development Environment"

# Create a script to easily toggle development mode
echo "Creating development mode toggle script..."
cat > toggle_dev_mode.sh << 'EOF'
#!/bin/bash
# toggle_dev_mode.sh - Toggle development mode for WIF implementation
# This script toggles between development and production modes

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Check current mode
if [ -f .dev_mode ]; then
    DEV_MODE=$(cat .dev_mode)
else
    DEV_MODE="false"
fi

if [ "$DEV_MODE" == "true" ]; then
    echo -e "${YELLOW}Currently in DEVELOPMENT mode with CSRF bypassed.${NC}"
    echo -e "${YELLOW}Do you want to switch to PRODUCTION mode? (y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "false" > .dev_mode
        echo -e "${GREEN}Switched to PRODUCTION mode.${NC}"
        echo -e "${BLUE}Run the following commands to apply the change:${NC}"
        echo "export WIF_DEV_MODE=false"
        echo "export WIF_BYPASS_CSRF=false"
    else
        echo -e "${YELLOW}Remaining in DEVELOPMENT mode.${NC}"
    fi
else
    echo -e "${YELLOW}Currently in PRODUCTION mode.${NC}"
    echo -e "${YELLOW}Do you want to switch to DEVELOPMENT mode with CSRF bypassed? (y/n)${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "true" > .dev_mode
        echo -e "${GREEN}Switched to DEVELOPMENT mode with CSRF bypassed.${NC}"
        echo -e "${BLUE}Run the following commands to apply the change:${NC}"
        echo "export WIF_DEV_MODE=true"
        echo "export WIF_BYPASS_CSRF=true"
    else
        echo -e "${YELLOW}Remaining in PRODUCTION mode.${NC}"
    fi
fi

# Add environment variables to shell startup file if requested
echo -e "${YELLOW}Do you want to add these environment variables to your shell startup file? (y/n)${NC}"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SHELL_RC=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi

    if [ -n "$SHELL_RC" ]; then
        if [ "$DEV_MODE" == "true" ]; then
            echo '# WIF Development Mode' >> "$SHELL_RC"
            echo 'export WIF_DEV_MODE=true' >> "$SHELL_RC"
            echo 'export WIF_BYPASS_CSRF=true' >> "$SHELL_RC"
        else
            echo '# WIF Production Mode' >> "$SHELL_RC"
            echo 'export WIF_DEV_MODE=false' >> "$SHELL_RC"
            echo 'export WIF_BYPASS_CSRF=false' >> "$SHELL_RC"
        fi
        echo -e "${GREEN}Added environment variables to $SHELL_RC${NC}"
        echo -e "${BLUE}Please restart your shell or run 'source $SHELL_RC' to apply the changes.${NC}"
    else
        echo -e "${YELLOW}Could not find .bashrc or .zshrc. Please add the environment variables manually.${NC}"
    fi
fi
EOF

chmod +x toggle_dev_mode.sh
echo -e "${GREEN}Created toggle_dev_mode.sh script.${NC}"

section "Updating Python Imports"

# Find all Python files that import directly from csrf_protection
echo "Updating Python files to use the CSRF loader instead of direct imports..."
PYTHON_FILES=$(grep -r --include="*.py" "from wif_implementation.csrf_protection import" . | cut -d: -f1 | sort | uniq)

if [ -n "$PYTHON_FILES" ]; then
    for file in $PYTHON_FILES; do
        echo "Updating imports in $file..."
        # Replace direct imports with loader imports
        sed -i 's/from wif_implementation.csrf_protection import csrf_protection, csrf_protect/from wif_implementation.csrf_loader import csrf_protection, csrf_protect/g' "$file"
        echo -e "${GREEN}Updated $file to use the CSRF loader.${NC}"
    done
else
    echo -e "${YELLOW}No Python files found importing directly from csrf_protection.${NC}"
fi

# Make sure wif_implementation_web.py gets updated
if [ -f "wif_implementation_web.py" ]; then
    echo "Checking wif_implementation_web.py for CSRF imports..."
    if grep -q "from wif_implementation.csrf_protection import" wif_implementation_web.py; then
        echo "Updating wif_implementation_web.py to use the CSRF loader..."
        sed -i 's/from wif_implementation.csrf_protection import csrf_protection, csrf_protect/from wif_implementation.csrf_loader import csrf_protection, csrf_protect/g' wif_implementation_web.py
        echo -e "${GREEN}Updated wif_implementation_web.py to use the CSRF loader.${NC}"
    else
        echo -e "${YELLOW}wif_implementation_web.py already uses the CSRF loader or does not use CSRF protection.${NC}"
    fi
fi

section "Simplified Security Documentation"

echo "A comprehensive documentation file has been created at SIMPLIFIED_SECURITY_README.md."
echo "This file explains the simplified security approach, how to use the new tools,"
echo "and when to choose between more secure options and simplified alternatives."

section "Completed!"

echo -e "${GREEN}All simplified security components have been applied!${NC}"
echo -e "${GREEN}Original files have been moved to 'archived_security' directory.${NC}"
echo ""
echo "You can now use the following simplified commands:"
echo "  ./github_auth.sh             - Simplified GitHub authentication"
echo "  ./verify_github_secrets.sh   - Simplified GitHub secrets verification"
echo "  ./setup_wif.sh               - Simplified GCP authentication setup"
echo "  ./toggle_dev_mode.sh         - Toggle between development and production modes"
echo ""
echo "For your GitHub Actions workflows, use the template at:"
echo "  .github/workflows/simplified-deploy-template.yml"
echo ""
echo "For more detailed information, please refer to:"
echo "  SIMPLIFIED_SECURITY_README.md"
echo ""
echo -e "${BLUE}Happy coding!${NC}"

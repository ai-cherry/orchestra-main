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

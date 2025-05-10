#!/bin/bash
# mode_indicator.sh - Add development/production mode indicator to your shell prompt
# This script adds a visual indicator to your shell prompt and manages persistent mode settings

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Create the .mode_config directory if it doesn't exist
mkdir -p ~/.mode_config

# Function to set mode in all relevant places
set_mode() {
    local mode=$1
    local bypass_csrf=$2
    
    # Save the mode settings persistently
    echo "$mode" > ~/.mode_config/current_mode
    echo "$bypass_csrf" > ~/.mode_config/bypass_csrf
    
    # Update .dev_mode file for the toggle script to read
    if [ "$mode" == "DEV" ]; then
        echo "true" > .dev_mode
    else
        echo "false" > .dev_mode
    fi
    
    # Set the environment variables for the current session
    if [ "$mode" == "DEV" ]; then
        export WIF_DEV_MODE=true
        if [ "$bypass_csrf" == "true" ]; then
            export WIF_BYPASS_CSRF=true
        else
            export WIF_BYPASS_CSRF=false
        fi
    else
        export WIF_DEV_MODE=false
        export WIF_BYPASS_CSRF=false
    fi
    
    # Add or update the environment variables in shell config
    update_shell_config
}

# Function to update shell configuration
update_shell_config() {
    # Detect shell
    local SHELL_RC=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        echo -e "${YELLOW}Could not find .bashrc or .zshrc. Please manually configure your shell.${NC}"
        return
    fi
    
    # Remove any existing mode settings
    sed -i '/# WIF Mode Settings/,/# End WIF Mode Settings/d' "$SHELL_RC"
    
    # Add new mode settings
    cat >> "$SHELL_RC" << EOF
# WIF Mode Settings
export MODE_INDICATOR_INSTALLED=true

# Load mode from persistent storage
if [ -f ~/.mode_config/current_mode ]; then
    WIF_MODE=\$(cat ~/.mode_config/current_mode)
else
    WIF_MODE="PROD"
fi

if [ -f ~/.mode_config/bypass_csrf ]; then
    WIF_BYPASS=\$(cat ~/.mode_config/bypass_csrf)
else
    WIF_BYPASS="false"
fi

# Set environment variables based on mode
if [ "\$WIF_MODE" == "DEV" ]; then
    export WIF_DEV_MODE=true
    export WIF_BYPASS_CSRF=\$WIF_BYPASS
    MODE_INDICATOR="${BOLD}${GREEN}[DEV]${NC}"
    if [ "\$WIF_BYPASS" == "true" ]; then
        MODE_INDICATOR="${BOLD}${YELLOW}[DEV-BYPASS]${NC}"
    fi
else
    export WIF_DEV_MODE=false
    export WIF_BYPASS_CSRF=false
    MODE_INDICATOR="${BOLD}${BLUE}[PROD]${NC}"
fi

# Add indicator to prompt
if [ -n "\$BASH_VERSION" ]; then
    # For Bash
    PS1_ORIGINAL=\${PS1_ORIGINAL:-\$PS1}
    export PS1="\${MODE_INDICATOR} \${PS1_ORIGINAL}"
elif [ -n "\$ZSH_VERSION" ]; then
    # For Zsh
    PS1_ORIGINAL=\${PS1_ORIGINAL:-\$PS1}
    export PS1="\${MODE_INDICATOR} \${PS1_ORIGINAL}"
fi

# Helper functions
dev_mode() {
    echo "true" > ~/.mode_config/current_mode
    echo "false" > ~/.mode_config/bypass_csrf
    echo "Switched to DEV mode. Please restart your shell or source your shell configuration."
    echo "Run 'source ~/.bashrc' or 'source ~/.zshrc' to apply changes immediately."
}

dev_bypass_mode() {
    echo "true" > ~/.mode_config/current_mode
    echo "true" > ~/.mode_config/bypass_csrf
    echo "Switched to DEV mode with CSRF bypass. Please restart your shell or source your shell configuration."
    echo "Run 'source ~/.bashrc' or 'source ~/.zshrc' to apply changes immediately."
}

prod_mode() {
    echo "PROD" > ~/.mode_config/current_mode
    echo "false" > ~/.mode_config/bypass_csrf
    echo "Switched to PROD mode. Please restart your shell or source your shell configuration."
    echo "Run 'source ~/.bashrc' or 'source ~/.zshrc' to apply changes immediately."
}

show_mode() {
    if [ "\$WIF_MODE" == "DEV" ]; then
        if [ "\$WIF_BYPASS" == "true" ]; then
            echo -e "${BOLD}${YELLOW}Currently in DEVELOPMENT mode with CSRF bypass${NC}"
        else
            echo -e "${BOLD}${GREEN}Currently in DEVELOPMENT mode${NC}"
        fi
    else
        echo -e "${BOLD}${BLUE}Currently in PRODUCTION mode${NC}"
    fi
}
# End WIF Mode Settings
EOF

    echo -e "${GREEN}Updated $SHELL_RC with mode indicator settings.${NC}"
    echo -e "${BLUE}Run 'source $SHELL_RC' to apply changes immediately.${NC}"
}

# Main script execution

# Check if mode indicator is already installed
if [ -n "$MODE_INDICATOR_INSTALLED" ]; then
    echo -e "${GREEN}Mode indicator is already installed in your shell.${NC}"
    echo -e "Use the following commands to switch modes:"
    echo -e "  ${BOLD}dev_mode${NC} - Switch to development mode"
    echo -e "  ${BOLD}dev_bypass_mode${NC} - Switch to development mode with CSRF bypass"
    echo -e "  ${BOLD}prod_mode${NC} - Switch to production mode"
    echo -e "  ${BOLD}show_mode${NC} - Display current mode"
    exit 0
fi

# Ask user which mode to set
echo -e "${BLUE}${BOLD}Mode Indicator Setup${NC}"
echo ""
echo "This will add a persistent mode indicator to your shell prompt"
echo "and create helper commands to easily switch between modes."
echo ""
echo "Choose which mode to set initially:"
echo "1) Development mode"
echo "2) Development mode with CSRF bypass"
echo "3) Production mode"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        set_mode "DEV" "false"
        echo -e "${GREEN}Set to DEVELOPMENT mode.${NC}"
        ;;
    2)
        set_mode "DEV" "true"
        echo -e "${YELLOW}Set to DEVELOPMENT mode with CSRF bypass.${NC}"
        ;;
    3)
        set_mode "PROD" "false"
        echo -e "${BLUE}Set to PRODUCTION mode.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice. Setting to PRODUCTION mode by default.${NC}"
        set_mode "PROD" "false"
        ;;
esac

echo ""
echo -e "${GREEN}Mode indicator has been installed!${NC}"
echo -e "You will now see ${BOLD}[DEV]${NC}, ${BOLD}[DEV-BYPASS]${NC}, or ${BOLD}[PROD]${NC} in your shell prompt."
echo ""
echo -e "Use the following commands to switch modes:"
echo -e "  ${BOLD}dev_mode${NC} - Switch to development mode"
echo -e "  ${BOLD}dev_bypass_mode${NC} - Switch to development mode with CSRF bypass"
echo -e "  ${BOLD}prod_mode${NC} - Switch to production mode"
echo -e "  ${BOLD}show_mode${NC} - Display current mode"
echo ""
echo -e "${BLUE}Please restart your shell or run 'source ~/.bashrc' or 'source ~/.zshrc' to apply changes.${NC}"

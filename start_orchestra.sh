#!/bin/bash
# Script to start Orchestra in either standard or recovery mode

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show usage
show_help() {
    echo -e "${BLUE}Orchestra Startup Script${NC}"
    echo -e "Usage: $0 [options]"
    echo -e ""
    echo -e "Options:"
    echo -e "  --standard      Start in standard mode with all features (default)"
    echo -e "  --recovery      Start in recovery mode with minimal features"
    echo -e "  --help          Show this help message"
    echo -e "  --no-extensions Skip checking for VS Code extensions"
    echo -e "  --no-monitor    Skip starting extension performance monitoring"
    echo -e "  --no-mcp        Skip starting the MCP memory system"
    echo -e ""
    echo -e "Example:"
    echo -e "  $0 --recovery   # Start in recovery mode"
}

# Parse arguments
MODE="standard"  # Default mode
CHECK_EXTENSIONS=true
START_MONITOR=true
START_MCP=true

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --standard) MODE="standard"; shift ;;
        --recovery) MODE="recovery"; shift ;;
        --no-extensions) CHECK_EXTENSIONS=false; shift ;;
        --no-monitor) START_MONITOR=false; shift ;;
        --no-mcp) START_MCP=false; shift ;;
        --help) show_help; exit 0 ;;
        *) echo -e "${RED}Unknown parameter: $1${NC}"; show_help; exit 1 ;;
    esac
done

# Check for VS Code extensions first if enabled
if [ "$CHECK_EXTENSIONS" = true ]; then
    echo -e "${YELLOW}Managing VS Code extensions...${NC}"
    
    # Check for optimized extension manager first
    if [ -f "/workspaces/orchestra-main/setup_extensions_optimized.sh" ]; then
        echo -e "${GREEN}Using optimized extension management system${NC}"
        bash /workspaces/orchestra-main/setup_extensions_optimized.sh
        
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}Warning: Some VS Code extensions might be missing.${NC}"
            echo -e "${YELLOW}This might affect your development experience.${NC}"
        fi
    # Fall back to legacy extension manager if optimized version not found
    elif [ -f "/workspaces/orchestra-main/setup_extensions.sh" ]; then
        echo -e "${YELLOW}Using legacy extension management system${NC}"
        echo -e "${YELLOW}Consider upgrading to the optimized system for better performance.${NC}"
        bash /workspaces/orchestra-main/setup_extensions.sh
        
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}Warning: Some VS Code extensions might be missing.${NC}"
            echo -e "${YELLOW}This might affect your development experience.${NC}"
        fi
    else
        echo -e "${YELLOW}VS Code extension setup script not found. Continuing without checking extensions.${NC}"
    fi
fi

# Start extension performance monitoring in the background if enabled
if [ "$START_MONITOR" = true ] && [ "$MODE" == "standard" ]; then
    if [ -f "/workspaces/orchestra-main/monitor_extensions.sh" ]; then
        echo -e "${YELLOW}Starting extension performance monitoring in the background...${NC}"
        bash /workspaces/orchestra-main/monitor_extensions.sh > /dev/null 2>&1 &
        MONITOR_PID=$!
        echo -e "${GREEN}Extension monitoring started (PID: $MONITOR_PID)${NC}"
    fi
fi

# Apply the toggle mode script first to ensure proper mode settings
echo -e "${YELLOW}Setting Orchestra mode to ${MODE^^}...${NC}"
if [ -f "/workspaces/orchestra-main/toggle_mode.py" ]; then
    if [ "$MODE" == "recovery" ]; then
        python /workspaces/orchestra-main/toggle_mode.py --recovery
    else
        python /workspaces/orchestra-main/toggle_mode.py --standard
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Mode set successfully to ${MODE^^}.${NC}"
    else
        echo -e "${RED}Failed to set mode to ${MODE^^}.${NC}"
        exit 1
    fi
else
    echo -e "${RED}toggle_mode.py not found. Cannot set mode properly.${NC}"
    exit 1
fi

# Start the MCP memory system if enabled
if [ "$START_MCP" = true ] && [ "$MODE" == "standard" ]; then
    if [ -f "/workspaces/orchestra-main/mcp_server/scripts/start_mcp_background.sh" ]; then
        echo -e "${YELLOW}Starting MCP Memory System...${NC}"
        bash /workspaces/orchestra-main/mcp_server/scripts/start_mcp_background.sh
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}MCP Memory System started successfully.${NC}"
        else
            echo -e "${YELLOW}Warning: Failed to start MCP Memory System. Orchestra will continue without it.${NC}"
        fi
    else
        echo -e "${YELLOW}MCP startup script not found. Skipping MCP Memory System.${NC}"
    fi
fi

# Run the application with the specified mode
echo -e "${GREEN}Starting Orchestra in ${MODE^^} mode...${NC}"
bash /workspaces/orchestra-main/run_api.sh --$MODE

#!/bin/bash
# monitor_extensions.sh - Run extension performance monitoring periodically
#
# This script runs the monitor_extension_performance.py script at regular intervals
# to track extension performance over time. It's designed to be started in the
# background during workspace initialization.

# Color definitions for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
WORKSPACE_ROOT="/workspaces/cherry_ai-main"
MONITOR_SCRIPT="${WORKSPACE_ROOT}/monitor_extension_performance.py"
LOG_DIR="${WORKSPACE_ROOT}/logs"
MONITOR_LOG="${LOG_DIR}/extension_monitor.log"
INTERVAL=1800  # 30 minutes in seconds

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Function to log messages
log_message() {
    local message=$1
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} - ${message}" | tee -a "${MONITOR_LOG}"
}

# Check if the monitor script exists
if [ ! -f "${MONITOR_SCRIPT}" ]; then
    log_message "${RED}Error: Monitor script not found at ${MONITOR_SCRIPT}${NC}"
    exit 1
fi

# Make sure the script is executable
chmod +x "${MONITOR_SCRIPT}"

# Log start
log_message "${GREEN}Starting extension performance monitoring${NC}"
log_message "${BLUE}Monitor will run every $(($INTERVAL / 60)) minutes${NC}"

# Run the monitor in a loop
while true; do
    # Run the monitor script
    log_message "${BLUE}Running extension performance monitor...${NC}"
    python3 "${MONITOR_SCRIPT}"

    # Check if the script ran successfully
    if [ $? -eq 0 ]; then
        log_message "${GREEN}Monitor completed successfully${NC}"
    else
        log_message "${RED}Monitor failed with exit code $?${NC}"
    fi

    # Wait for the next interval
    log_message "${BLUE}Waiting for ${INTERVAL} seconds before next run...${NC}"
    sleep ${INTERVAL}
done

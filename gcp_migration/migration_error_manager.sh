#!/bin/bash
#
# Migration Error Manager for AI Orchestra
#
# This script systematically resolves critical errors identified during
# the GCP migration process. It checks the MCP server, fixes issues,
# verifies data integrity, and documents all resolution steps.
#
# Usage: ./migration_error_manager.sh [options]
#

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
LOG_DIR="/var/log/mcp"
INCIDENT_DIR="incidents"
MCP_SERVICE="mcp-server"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VERBOSE=false
REPAIR=true
VERIFY=true
REPORT=true

# Print header
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          AI Orchestra Migration Error Manager              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Print usage
print_usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --log-dir=DIR      Log directory (default: $LOG_DIR)"
    echo "  --incident-dir=DIR Incident report directory (default: $INCIDENT_DIR)"
    echo "  --service=NAME     MCP service name (default: $MCP_SERVICE)"
    echo "  --no-repair        Skip repair attempts"
    echo "  --no-verify        Skip data integrity verification"
    echo "  --no-report        Skip incident report generation"
    echo "  --verbose          Enable verbose output"
    echo "  --help             Show this help message"
    echo
}

# Check if diagnostics and resolution tools are available
check_tools() {
    echo -e "${BLUE}Checking for required tools...${NC}"
    
    if [ ! -f "$SCRIPT_DIR/mcp_server_diagnostics.py" ]; then
        echo -e "${RED}Error: mcp_server_diagnostics.py not found in $SCRIPT_DIR${NC}"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/resolve_migration_errors.py" ]; then
        echo -e "${RED}Error: resolve_migration_errors.py not found in $SCRIPT_DIR${NC}"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All required tools are available${NC}"
    echo
}

# Check MCP server status
check_mcp_server() {
    echo -e "${BLUE}Checking MCP server status...${NC}"
    
    if systemctl status $MCP_SERVICE &> /dev/null; then
        echo -e "${GREEN}MCP server is running${NC}"
        echo
        return 0
    else
        echo -e "${RED}MCP server is not running${NC}"
        echo
        return 1
    fi
}

# Parse migration logs for critical errors
parse_logs() {
    echo -e "${BLUE}Parsing migration logs for critical errors...${NC}"
    
    VERBOSE_ARG=""
    if [ "$VERBOSE" = true ]; then
        VERBOSE_ARG="--verbose"
    fi
    
    python3 "$SCRIPT_DIR/resolve_migration_errors.py" --log-dir="$LOG_DIR" --check $VERBOSE_ARG
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}No critical errors found in logs${NC}"
    else
        echo -e "${RED}Critical errors found in logs${NC}"
    fi
    
    echo
    return $EXIT_CODE
}

# Run MCP server diagnostics
run_diagnostics() {
    echo -e "${BLUE}Running MCP server diagnostics...${NC}"
    
    VERBOSE_ARG=""
    if [ "$VERBOSE" = true ]; then
        VERBOSE_ARG="--verbose"
    fi
    
    python3 "$SCRIPT_DIR/mcp_server_diagnostics.py" --diagnostics --service="$MCP_SERVICE" $VERBOSE_ARG
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}MCP server diagnostics completed successfully${NC}"
    else
        echo -e "${RED}MCP server diagnostics found issues${NC}"
    fi
    
    echo
    return $EXIT_CODE
}

# Attempt to repair issues
repair_issues() {
    echo -e "${BLUE}Attempting to repair issues...${NC}"
    
    if [ "$REPAIR" = false ]; then
        echo -e "${YELLOW}Skipping repair as requested${NC}"
        echo
        return 0
    fi
    
    VERBOSE_ARG=""
    if [ "$VERBOSE" = true ]; then
        VERBOSE_ARG="--verbose"
    fi
    
    python3 "$SCRIPT_DIR/resolve_migration_errors.py" --log-dir="$LOG_DIR" --service="$MCP_SERVICE" --repair $VERBOSE_ARG
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}Repair completed successfully${NC}"
    else
        echo -e "${RED}Repair failed${NC}"
    fi
    
    echo
    return $EXIT_CODE
}

# Verify data integrity
verify_data() {
    echo -e "${BLUE}Verifying data integrity...${NC}"
    
    if [ "$VERIFY" = false ]; then
        echo -e "${YELLOW}Skipping verification as requested${NC}"
        echo
        return 0
    fi
    
    VERBOSE_ARG=""
    if [ "$VERBOSE" = true ]; then
        VERBOSE_ARG="--verbose"
    fi
    
    python3 "$SCRIPT_DIR/resolve_migration_errors.py" --log-dir="$LOG_DIR" --service="$MCP_SERVICE" --verify $VERBOSE_ARG
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}Data integrity verification passed${NC}"
    else
        echo -e "${RED}Data integrity verification failed${NC}"
    fi
    
    echo
    return $EXIT_CODE
}

# Generate incident report
generate_report() {
    echo -e "${BLUE}Generating incident report...${NC}"
    
    if [ "$REPORT" = false ]; then
        echo -e "${YELLOW}Skipping report generation as requested${NC}"
        echo
        return 0
    fi
    
    mkdir -p "$INCIDENT_DIR"
    
    VERBOSE_ARG=""
    if [ "$VERBOSE" = true ]; then
        VERBOSE_ARG="--verbose"
    fi
    
    python3 "$SCRIPT_DIR/resolve_migration_errors.py" --log-dir="$LOG_DIR" --service="$MCP_SERVICE" --report-dir="$INCIDENT_DIR" --report $VERBOSE_ARG
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}Incident report generated successfully${NC}"
    else
        echo -e "${RED}Failed to generate incident report${NC}"
    fi
    
    echo
    return $EXIT_CODE
}

# Main execution flow
main() {
    print_header
    
    # Check for tools
    check_tools
    
    # Parse command-line arguments
    for arg in "$@"; do
        case $arg in
            --log-dir=*)
                LOG_DIR="${arg#*=}"
                shift
                ;;
            --incident-dir=*)
                INCIDENT_DIR="${arg#*=}"
                shift
                ;;
            --service=*)
                MCP_SERVICE="${arg#*=}"
                shift
                ;;
            --no-repair)
                REPAIR=false
                shift
                ;;
            --no-verify)
                VERIFY=false
                shift
                ;;
            --no-report)
                REPORT=false
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $arg${NC}"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Show configuration
    echo -e "${BLUE}Configuration:${NC}"
    echo -e "  Log Directory: ${GREEN}$LOG_DIR${NC}"
    echo -e "  Incident Directory: ${GREEN}$INCIDENT_DIR${NC}"
    echo -e "  MCP Service: ${GREEN}$MCP_SERVICE${NC}"
    echo -e "  Repair: ${GREEN}$REPAIR${NC}"
    echo -e "  Verify: ${GREEN}$VERIFY${NC}"
    echo -e "  Report: ${GREEN}$REPORT${NC}"
    echo -e "  Verbose: ${GREEN}$VERBOSE${NC}"
    echo
    
    # Run diagnostics
    run_diagnostics
    DIAG_STATUS=$?
    
    # Parse logs for critical errors
    parse_logs
    LOG_STATUS=$?
    
    # Repair if needed
    if [ $DIAG_STATUS -ne 0 ] || [ $LOG_STATUS -ne 0 ]; then
        repair_issues
        REPAIR_STATUS=$?
    else
        echo -e "${GREEN}No issues detected, skipping repair${NC}"
        REPAIR_STATUS=0
    fi
    
    # Verify data integrity
    verify_data
    VERIFY_STATUS=$?
    
    # Generate incident report
    generate_report
    REPORT_STATUS=$?
    
    # Final summary
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                   Summary                               ${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo
    
    # Diagnostics status
    if [ $DIAG_STATUS -eq 0 ]; then
        echo -e "Diagnostics: ${GREEN}✓ Passed${NC}"
    else
        echo -e "Diagnostics: ${RED}✗ Failed${NC}"
    fi
    
    # Log parsing status
    if [ $LOG_STATUS -eq 0 ]; then
        echo -e "Log Analysis: ${GREEN}✓ No critical errors${NC}"
    else
        echo -e "Log Analysis: ${RED}✗ Critical errors found${NC}"
    fi
    
    # Repair status
    if [ $REPAIR_STATUS -eq 0 ]; then
        echo -e "Repair: ${GREEN}✓ Successful${NC}"
    else
        echo -e "Repair: ${RED}✗ Failed${NC}"
    fi
    
    # Verification status
    if [ $VERIFY_STATUS -eq 0 ]; then
        echo -e "Data Integrity: ${GREEN}✓ Verified${NC}"
    else
        echo -e "Data Integrity: ${RED}✗ Issues detected${NC}"
    fi
    
    # Report status
    if [ $REPORT_STATUS -eq 0 ]; then
        echo -e "Incident Report: ${GREEN}✓ Generated${NC}"
    else
        echo -e "Incident Report: ${RED}✗ Failed${NC}"
    fi
    
    echo
    
    # Overall status
    if [ $DIAG_STATUS -eq 0 ] && [ $LOG_STATUS -eq 0 ] && [ $REPAIR_STATUS -eq 0 ] && [ $VERIFY_STATUS -eq 0 ]; then
        echo -e "${GREEN}All checks passed. Migration can proceed.${NC}"
        exit_code=0
    elif [ $REPAIR_STATUS -eq 0 ] && [ $VERIFY_STATUS -eq 0 ]; then
        echo -e "${YELLOW}Issues were found but repaired successfully. Migration can proceed with caution.${NC}"
        exit_code=0
    else
        echo -e "${RED}Unresolved issues remain. Please review logs and incident report.${NC}"
        exit_code=1
    fi
    
    exit $exit_code
}

# Execute main function
main "$@"
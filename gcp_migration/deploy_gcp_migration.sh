#!/bin/bash
#
# AI Orchestra GCP Migration Deployment Script
#
# This script executes the GCP migration using the unified migration executor
# with proper environment setup and error handling.
#

set -e

# Default values
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"cherry-ai-project"}
LOCATION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PARENT_DIR="$(dirname "$BASE_DIR")"
CONFIG_DIR="${PARENT_DIR}/config"
LOG_DIR="${PARENT_DIR}/logs/migration"
PHASE=""
VERIFY_ONLY=false
VERBOSE=false

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
function print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║               AI Orchestra GCP Migration                   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Print usage
function print_usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --project=ID       GCP project ID (default: $PROJECT_ID)"
    echo "  --location=LOC     GCP location (default: $LOCATION)"
    echo "  --config-dir=DIR   Configuration directory (default: $CONFIG_DIR)"
    echo "  --log-dir=DIR      Log directory (default: $LOG_DIR)"
    echo "  --phase=PHASE      Specific phase to execute"
    echo "  --verify-only      Only verify without making changes"
    echo "  --verbose          Enable verbose output"
    echo "  --help             Show this help message"
    echo
    echo "Available phases:"
    echo "  core_infrastructure  - Core GCP infrastructure setup"
    echo "  workstation_config   - Cloud Workstation configuration"
    echo "  memory_system        - Memory system setup"
    echo "  hybrid_config        - Hybrid configuration setup"
    echo "  ai_coding            - AI coding assistant setup"
    echo "  api_deployment       - API deployment to Cloud Run"
    echo "  validation           - End-to-end validation"
    echo
    echo "Example:"
    echo "  $0 --project=my-project --phase=memory_system"
    echo "  $0 --verify-only"
}

# Check prerequisites
function check_prerequisites() {
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not found${NC}"
        exit 1
    fi

    # Check gcloud if not verify-only
    if [ "$VERIFY_ONLY" = false ]; then
        if ! command -v gcloud &> /dev/null; then
            echo -e "${RED}Error: Google Cloud SDK (gcloud) is required but not found${NC}"
            exit 1
        fi

        # Check gcloud auth
        if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
            echo -e "${YELLOW}Warning: Not authenticated with gcloud. Please run 'gcloud auth login'${NC}"
            echo -e "${YELLOW}Proceeding anyway since this might be a test environment...${NC}"
        fi
    fi

    # Create directories if they don't exist
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
}

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --project=*)
            PROJECT_ID="${arg#*=}"
            shift
            ;;
        --location=*)
            LOCATION="${arg#*=}"
            shift
            ;;
        --config-dir=*)
            CONFIG_DIR="${arg#*=}"
            shift
            ;;
        --log-dir=*)
            LOG_DIR="${arg#*=}"
            shift
            ;;
        --phase=*)
            PHASE="${arg#*=}"
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            print_header
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

# Print header
print_header

# Display execution parameters
echo -e "${BLUE}Execution Parameters:${NC}"
echo -e "  Project ID:       ${GREEN}$PROJECT_ID${NC}"
echo -e "  Location:         ${GREEN}$LOCATION${NC}"
echo -e "  Config Directory: ${GREEN}$CONFIG_DIR${NC}"
echo -e "  Log Directory:    ${GREEN}$LOG_DIR${NC}"
if [ -n "$PHASE" ]; then
    echo -e "  Phase:            ${GREEN}$PHASE${NC}"
else
    echo -e "  Phase:            ${GREEN}All phases${NC}"
fi
if [ "$VERIFY_ONLY" = true ]; then
    echo -e "  Mode:             ${YELLOW}Verify only${NC}"
else
    echo -e "  Mode:             ${GREEN}Execute${NC}"
fi
if [ "$VERBOSE" = true ]; then
    echo -e "  Verbose:          ${GREEN}Enabled${NC}"
else
    echo -e "  Verbose:          ${NC}Disabled${NC}"
fi
echo

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
check_prerequisites
echo -e "${GREEN}Prerequisites check passed${NC}"
echo

# Prepare command
CMD="$BASE_DIR/execute_unified_migration.py"
CMD="$CMD --project=$PROJECT_ID"
CMD="$CMD --location=$LOCATION"
CMD="$CMD --config-dir=$CONFIG_DIR"
CMD="$CMD --log-dir=$LOG_DIR"

if [ -n "$PHASE" ]; then
    CMD="$CMD --phase=$PHASE"
fi

if [ "$VERIFY_ONLY" = true ]; then
    CMD="$CMD --verify-only"
fi

if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Execute the migration
echo -e "${BLUE}Executing migration...${NC}"
echo -e "Command: ${YELLOW}python3 $CMD${NC}"
echo

if python3 $CMD; then
    echo
    echo -e "${GREEN}Migration completed successfully${NC}"
    
    # Show report location
    LATEST_REPORT="$LOG_DIR/reports/latest_report.md"
    if [ -f "$LATEST_REPORT" ]; then
        echo -e "${BLUE}Migration report: ${YELLOW}$LATEST_REPORT${NC}"
    fi
    
    exit 0
else
    EXIT_CODE=$?
    echo
    echo -e "${RED}Migration failed with exit code $EXIT_CODE${NC}"
    
    # Show report location
    LATEST_REPORT="$LOG_DIR/reports/latest_report.md"
    if [ -f "$LATEST_REPORT" ]; then
        echo -e "${BLUE}Failure report: ${YELLOW}$LATEST_REPORT${NC}"
    fi
    
    exit $EXIT_CODE
fi
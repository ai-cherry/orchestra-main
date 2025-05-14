#!/bin/bash
#
# AI Orchestra GCP Migration Manager
#
# This script provides a simplified interface for managing the GCP migration
# process. It handles initialization, execution, monitoring, and reporting.
#
# Usage:
#   ./manage_migration.sh [COMMAND] [OPTIONS]
#
# Commands:
#   init       Initialize migration environment
#   execute    Execute migration
#   status     Show migration status
#   report     Generate migration report
#   verify     Verify migration
#   monitor    Monitor migration progress
#   help       Show help
#

set -e

# Default values
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
LOCATION=${LOCATION:-"us-central1"}
CONFIG_DIR="./config"
LOG_DIR="./logs/migration"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
COLOR_GREEN="\033[0;32m"
COLOR_RED="\033[0;31m"
COLOR_YELLOW="\033[0;33m"
COLOR_BLUE="\033[0;34m"
COLOR_RESET="\033[0m"

# Function to show help
function show_help() {
    echo -e "${COLOR_BLUE}AI Orchestra GCP Migration Manager${COLOR_RESET}"
    echo
    echo "Usage:"
    echo "  ./manage_migration.sh [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  init                 Initialize migration environment"
    echo "  execute [--phase=X]  Execute migration (optionally specify phase)"
    echo "  status               Show migration status"
    echo "  report               Generate migration report"
    echo "  verify               Verify migration"
    echo "  monitor              Monitor migration progress"
    echo "  help                 Show this help"
    echo
    echo "Options:"
    echo "  --project=ID         GCP project ID (default: $PROJECT_ID)"
    echo "  --location=LOC       GCP location (default: $LOCATION)"
    echo "  --config-dir=DIR     Configuration directory (default: $CONFIG_DIR)"
    echo "  --log-dir=DIR        Log directory (default: $LOG_DIR)"
    echo "  --verify-only        Only verify without executing changes"
    echo
    echo "Examples:"
    echo "  ./manage_migration.sh init --project=my-project"
    echo "  ./manage_migration.sh execute"
    echo "  ./manage_migration.sh execute --phase=MEMORY_SYSTEM"
    echo "  ./manage_migration.sh status"
    echo "  ./manage_migration.sh report"
}

# Function to initialize migration environment
function init_migration() {
    echo -e "${COLOR_BLUE}Initializing migration environment...${COLOR_RESET}"
    
    # Create directories
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${COLOR_RED}Python 3 is required but not found${COLOR_RESET}"
        exit 1
    fi
    
    # Check for gcloud
    if ! command -v gcloud &> /dev/null; then
        echo -e "${COLOR_RED}Google Cloud SDK (gcloud) is required but not found${COLOR_RESET}"
        exit 1
    fi
    
    # Check gcloud auth
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        echo -e "${COLOR_YELLOW}Not authenticated with gcloud. Please run 'gcloud auth login'${COLOR_RESET}"
        exit 1
    fi
    
    # Configure gcloud project
    gcloud config set project "$PROJECT_ID"
    echo -e "${COLOR_GREEN}Using Google Cloud project: $PROJECT_ID${COLOR_RESET}"
    
    # Initialize hybrid config
    echo "Creating default configurations..."
    python3 "$SCRIPT_DIR/hybrid_config.py" --project="$PROJECT_ID" --config="$CONFIG_DIR" --create-defaults
    
    # Initialize migration monitor
    echo "Initializing migration monitor..."
    python3 "$SCRIPT_DIR/migration_monitor.py" --log-dir="$LOG_DIR" --status
    
    echo -e "${COLOR_GREEN}Migration environment initialized successfully${COLOR_RESET}"
    echo
    echo "Next steps:"
    echo "  1. Review configurations in $CONFIG_DIR"
    echo "  2. Run './manage_migration.sh execute' to start migration"
}

# Function to execute migration
function execute_migration() {
    echo -e "${COLOR_BLUE}Executing migration...${COLOR_RESET}"
    
    PHASE_ARG=""
    if [ -n "$PHASE" ]; then
        PHASE_ARG="--phase=$PHASE"
    fi
    
    VERIFY_ARG=""
    if [ "$VERIFY_ONLY" = "true" ]; then
        VERIFY_ARG="--verify-only"
    fi
    
    # Execute the migration
    python3 "$SCRIPT_DIR/execute_unified_migration.py" \
        --project="$PROJECT_ID" \
        --location="$LOCATION" \
        --config-dir="$CONFIG_DIR" \
        $PHASE_ARG \
        $VERIFY_ARG
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${COLOR_GREEN}Migration executed successfully${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}Migration failed with exit code $EXIT_CODE${COLOR_RESET}"
        echo "Check the logs for details."
    fi
    
    # Generate report
    python3 "$SCRIPT_DIR/migration_monitor.py" --log-dir="$LOG_DIR" --report
    
    return $EXIT_CODE
}

# Function to show migration status
function show_status() {
    echo -e "${COLOR_BLUE}Migration Status${COLOR_RESET}"
    python3 "$SCRIPT_DIR/migration_monitor.py" --log-dir="$LOG_DIR" --status
}

# Function to generate migration report
function generate_report() {
    echo -e "${COLOR_BLUE}Generating migration report...${COLOR_RESET}"
    python3 "$SCRIPT_DIR/migration_monitor.py" --log-dir="$LOG_DIR" --report
}

# Function to verify migration
function verify_migration() {
    echo -e "${COLOR_BLUE}Verifying migration...${COLOR_RESET}"
    
    # Execute with verify-only
    VERIFY_ONLY=true
    execute_migration
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${COLOR_GREEN}Migration verification successful${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}Migration verification failed${COLOR_RESET}"
    fi
    
    return $EXIT_CODE
}

# Function to monitor migration
function monitor_migration() {
    echo -e "${COLOR_BLUE}Monitoring migration...${COLOR_RESET}"
    
    INTERVAL=10
    COUNT=0
    
    echo "Press Ctrl+C to stop monitoring"
    
    # Monitor loop
    while true; do
        clear
        echo -e "${COLOR_BLUE}Migration Status (updated every ${INTERVAL}s)${COLOR_RESET}"
        echo "Last update: $(date)"
        echo
        
        python3 "$SCRIPT_DIR/migration_monitor.py" --log-dir="$LOG_DIR" --status
        
        # Every 10 updates, generate a new report
        COUNT=$((COUNT + 1))
        if [ $((COUNT % 10)) -eq 0 ]; then
            echo -e "${COLOR_YELLOW}Generating updated report...${COLOR_RESET}"
            python3 "$SCRIPT_DIR/migration_monitor.py" --log-dir="$LOG_DIR" --report
        fi
        
        sleep $INTERVAL
    done
}

# Parse command line arguments
COMMAND=${1:-"help"}
shift || true

# Parse options
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
        --help)
            COMMAND="help"
            shift
            ;;
        *)
            # Unknown option
            echo "Unknown option: $arg"
            show_help
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    init)
        init_migration
        ;;
    execute)
        execute_migration
        ;;
    status)
        show_status
        ;;
    report)
        generate_report
        ;;
    verify)
        verify_migration
        ;;
    monitor)
        monitor_migration
        ;;
    help|*)
        show_help
        ;;
esac
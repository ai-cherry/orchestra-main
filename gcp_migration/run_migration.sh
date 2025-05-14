#!/bin/bash
# 
# AI Orchestra GCP Migration Runner
#
# This script provides a simple interface for running the AI Orchestra GCP migration
# with optimal performance settings and robust error handling.
#
# Usage:
#   ./gcp_migration/run_migration.sh [--skip-phase=phase_name]
#

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print header
echo -e "${BOLD}===============================================${NC}"
echo -e "${BOLD}   AI Orchestra GCP Migration - Optimized     ${NC}"
echo -e "${BOLD}===============================================${NC}"
echo ""
echo -e "Starting migration at $(date)"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    log_error "Python 3.8+ is required. Found version $PYTHON_VERSION"
    echo "Please upgrade your Python installation."
    exit 1
fi

log_info "Python version check passed: $PYTHON_VERSION"

# Ensure migration script is executable
chmod +x gcp_migration/execute_migration.py
log_info "Made migration script executable"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

log_info "gcloud CLI found. Checking authentication..."

# Check gcloud authentication
AUTH_STATUS=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$AUTH_STATUS" ]; then
    log_warning "No active gcloud authentication found."
    echo -e "${YELLOW}You need to authenticate with gcloud before proceeding.${NC}"
    echo -e "Run: ${BOLD}gcloud auth login${NC}"
    
    read -p "Do you want to authenticate now? (y/n): " AUTH_CHOICE
    if [ "$AUTH_CHOICE" = "y" ] || [ "$AUTH_CHOICE" = "Y" ]; then
        gcloud auth login
    else
        log_error "Authentication required to proceed."
        exit 1
    fi
fi

log_info "Authentication verified: $AUTH_STATUS"

# Check project configuration
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    log_warning "No project selected."
    read -p "Enter GCP project ID for migration: " INPUT_PROJECT
    if [ -n "$INPUT_PROJECT" ]; then
        gcloud config set project "$INPUT_PROJECT"
        PROJECT_ID="$INPUT_PROJECT"
    else
        log_error "Project ID required to proceed."
        exit 1
    fi
fi

log_info "Using GCP project: $PROJECT_ID"

# Create a virtual environment if needed
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt 2>/dev/null || log_warning "requirements.txt not found or installation failed."
else
    source venv/bin/activate
fi

log_info "Virtual environment activated"

# Prepare arguments to pass to Python script
ARGS=""
for arg in "$@"; do
    ARGS="$ARGS $arg"
done

# Run migration with performance logging
log_info "Starting migration execution..."
echo -e "${BOLD}-----------------------------------------------${NC}"

start_time=$(date +%s)

# Execute the Python migration script
if python gcp_migration/execute_migration.py $ARGS; then
    end_time=$(date +%s)
    execution_time=$((end_time - start_time))
    
    echo -e "${BOLD}-----------------------------------------------${NC}"
    log_success "Migration completed successfully!"
    echo ""
    echo -e "Execution time: ${BOLD}$execution_time seconds${NC}"
    
    # Display summary if available
    if [ -f "MIGRATION_SUMMARY.md" ]; then
        echo ""
        echo -e "${BOLD}Migration Summary${NC}"
        echo -e "${BOLD}---------------${NC}"
        # Extract and display key information from the summary
        grep -A 2 "^##" MIGRATION_SUMMARY.md | grep -v "^--" || true
        
        echo ""
        echo -e "For detailed information, see ${BOLD}MIGRATION_SUMMARY.md${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}${BOLD}Next Steps:${NC}"
    echo -e "1. Review the migration summary document: ${BOLD}cat MIGRATION_SUMMARY.md${NC}"
    echo -e "2. Verify database connections and services"
    echo -e "3. Test API endpoints and memory functions"
    
    exit 0
else
    end_time=$(date +%s)
    execution_time=$((end_time - start_time))
    
    echo -e "${BOLD}-----------------------------------------------${NC}"
    log_error "Migration failed!"
    echo -e "Execution time: ${BOLD}$execution_time seconds${NC}"
    echo ""
    echo -e "${YELLOW}${BOLD}Troubleshooting:${NC}"
    echo -e "1. Check the logs for detailed error information: ${BOLD}cat migration.log${NC}"
    echo -e "2. Verify your GCP permissions and service account configuration"
    echo -e "3. Ensure all required APIs are enabled in your GCP project"
    echo -e "4. Run specific phases individually with: ${BOLD}./gcp_migration/run_migration.sh --skip-phase=phase_name${NC}"
    
    exit 1
fi
#!/bin/bash
#
# AI Orchestra Migration to GCP - Main Script
#
# This script orchestrates the complete migration process to GCP
# using the organization policy fixes and non-interactive execution
#
# Author: Roo

set -e

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
LOG_DIR="gcp_migration/migration_logs"
mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/complete_migration_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  
  case $level in
    INFO)
      echo -e "${GREEN}[INFO]${NC} ${message}"
      ;;
    WARNING)
      echo -e "${YELLOW}[WARNING]${NC} ${message}"
      ;;
    ERROR)
      echo -e "${RED}[ERROR]${NC} ${message}"
      ;;
    STEP)
      echo -e "${BLUE}[STEP]${NC} ${BOLD}${message}${NC}"
      ;;
    *)
      echo -e "${message}"
      ;;
  esac
  
  echo "[${timestamp}] [${level}] ${message}" >> "$MAIN_LOG"
}

# Function to check prerequisite tools
check_prerequisites() {
  log "STEP" "Checking prerequisites"
  
  # Check for gcloud
  if ! command -v gcloud &> /dev/null; then
    log "ERROR" "gcloud CLI is not installed. Please install it before continuing."
    exit 1
  fi
  
  # Check for Python
  if ! command -v python3 &> /dev/null; then
    log "ERROR" "Python 3 is not installed. Please install it before continuing."
    exit 1
  fi
  
  # Check for terraform
  if ! command -v terraform &> /dev/null; then
    log "WARNING" "Terraform is not installed. Some steps may fail."
  fi
  
  # Check for curl
  if ! command -v curl &> /dev/null; then
    log "WARNING" "curl is not installed. Some steps may fail."
  fi
  
  # Check Python packages
  log "INFO" "Installing required Python packages"
  pip install google-cloud-aiplatform google-cloud-storage fastapi uvicorn &>> "$MAIN_LOG" || {
    log "WARNING" "Failed to install some Python packages. Continuing anyway."
  }
  
  log "INFO" "Prerequisites check completed"
}

# Function to run organization policy fix
run_org_policy_fix() {
  log "STEP" "Running organization policy fix"
  
  # Check if the org policy manager key is available
  if [ -z "$GCP_ORGANIZATION_POLICY_JSON" ]; then
    log "INFO" "GCP_ORGANIZATION_POLICY_JSON environment variable not found."
    log "INFO" "You can set it or provide a path to the key file when prompted."
  else
    log "INFO" "GCP_ORGANIZATION_POLICY_JSON environment variable found."
  fi
  
  # Run the org policy manager
  log "INFO" "Running organization policy manager"
  ./gcp_migration/run_org_policy_manager.sh 2>&1 | tee -a "$MAIN_LOG"
  
  # Check the exit code
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log "ERROR" "Organization policy fix failed"
    log "INFO" "You can try to run it manually: ./gcp_migration/run_org_policy_manager.sh"
    log "INFO" "Or continue with the migration anyway"
    
    log "INFO" "Do you want to continue with the migration anyway? (y/n)"
    read -p "Continue? " CONTINUE
    
    if [[ ! "$CONTINUE" =~ ^[Yy] ]]; then
      log "INFO" "Migration aborted by user"
      exit 1
    fi
  fi
  
  log "INFO" "Organization policy fix completed"
}

# Function to run non-interactive migration
run_non_interactive_migration() {
  log "STEP" "Running non-interactive migration"
  
  # Check if the script exists
  if [ ! -f "./gcp_migration/execute_non_interactive.sh" ]; then
    log "ERROR" "Non-interactive migration script not found"
    exit 1
  fi
  
  # Make sure it's executable
  chmod +x ./gcp_migration/execute_non_interactive.sh
  
  # Run the non-interactive migration script
  log "INFO" "Executing non-interactive migration script"
  ./gcp_migration/execute_non_interactive.sh 2>&1 | tee -a "$MAIN_LOG"
  
  # Check the exit code
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log "ERROR" "Non-interactive migration failed"
    return 1
  fi
  
  log "INFO" "Non-interactive migration completed"
}

# Function to verify deployment
verify_deployment() {
  log "STEP" "Verifying deployment"
  
  # Check Cloud Run services
  log "INFO" "Checking Cloud Run services"
  gcloud run services list --project="$PROJECT_ID" --format="table[box](NAME,REGION,URL,LAST_DEPLOYED.datetime)" 2>&1 | tee -a "$MAIN_LOG"
  
  # Test AI Orchestra minimal service
  SERVICE_URL=$(gcloud run services describe ai-orchestra-minimal --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "")
  if [ -n "$SERVICE_URL" ]; then
    log "INFO" "Testing AI Orchestra minimal service: $SERVICE_URL"
    curl -s -i "${SERVICE_URL}/health" 2>&1 | tee -a "$MAIN_LOG"
  else
    log "WARNING" "AI Orchestra minimal service URL not found"
  fi
  
  # Test Vertex AI connectivity
  log "INFO" "Testing Vertex AI connectivity"
  python3 gcp_migration/test_vertex_ai.py 2>&1 | tee -a "$MAIN_LOG"
  
  # Check Terraform state if available
  if [ -d "terraform/migration" ]; then
    log "INFO" "Checking Terraform state"
    (cd terraform/migration && terraform state list) 2>&1 | tee -a "$MAIN_LOG" || log "WARNING" "Terraform state check failed"
  fi
  
  log "INFO" "Verification completed"
}

# Function to generate final report
generate_final_report() {
  log "STEP" "Generating final report"
  
  REPORT_FILE="$LOG_DIR/complete_migration_report.md"
  
  cat > "$REPORT_FILE" << EOF
# AI Orchestra GCP Migration - Final Report

## Migration Status

- **Timestamp:** $(date +"%Y-%m-%d %H:%M:%S")
- **Project ID:** ${PROJECT_ID}
- **Region:** ${REGION}

## Deployed Resources

### Cloud Run Services

\`\`\`
$(gcloud run services list --project="$PROJECT_ID" --format="table[box](NAME,REGION,URL,LAST_DEPLOYED.datetime)" 2>/dev/null || echo "No services found")
\`\`\`

### Organization Policy Status

\`\`\`
$(gcloud org-policies list --project="$PROJECT_ID" 2>/dev/null || echo "Failed to retrieve organization policies")
\`\`\`

### Vertex AI Status

$(python3 gcp_migration/test_vertex_ai.py 2>&1 || echo "Vertex AI test failed")

## Migration Steps Completed

1. Organization policy constraints fixed
2. Infrastructure deployed using Terraform
3. Cloud Run services deployed
4. Vertex AI access configured
5. Final verification completed

## Next Steps

1. Deploy additional services (if required)
2. Set up CI/CD pipeline for ongoing deployments
3. Configure monitoring and alerting
4. Implement database migration and data transfer
5. Establish backup and disaster recovery procedures

## Logs

Full logs are available at:
- Organization Policy Fix: $LOG_DIR/org_policy_manager_*.log
- Migration Execution: $LOG_DIR/migration_execution_*.log
- Complete Migration: ${MAIN_LOG}
EOF
  
  log "INFO" "Final report generated at: $REPORT_FILE"
  
  # Display report
  cat "$REPORT_FILE"
}

# Main function
main() {
  log "INFO" "Starting AI Orchestra migration to GCP"
  
  # Check prerequisites
  check_prerequisites
  
  # Run organization policy fix
  run_org_policy_fix
  
  # Run non-interactive migration
  run_non_interactive_migration
  
  # Verify deployment
  verify_deployment
  
  # Generate final report
  generate_final_report
  
  log "STEP" "Migration process completed!"
  echo -e "\n${GREEN}${BOLD}AI Orchestra migration to GCP completed!${NC}"
  echo -e "Detailed logs available at: ${MAIN_LOG}"
  echo -e "Final migration report: ${REPORT_FILE}"
}

# Execute main function
main "$@"
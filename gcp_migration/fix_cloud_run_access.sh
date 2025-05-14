#!/bin/bash
#
# Fix Cloud Run Access and IAM Permissions
#
# This script diagnoses and fixes permission issues with Cloud Run and Vertex AI
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
SERVICE_NAME="ai-orchestra-minimal"
SERVICE_ACCOUNT="codespaces-powerful-sa@${PROJECT_ID}.iam.gserviceaccount.com"
LOG_FILE="gcp_migration/migration_logs/fix_permissions_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

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
  
  echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# Run command and log output
run_command() {
  local cmd="$1"
  local desc="$2"
  
  log "INFO" "Executing: $desc"
  echo -e "${YELLOW}Running:${NC} $cmd"
  
  if OUTPUT=$(eval "$cmd" 2>&1); then
    log "INFO" "Command succeeded"
    echo "$OUTPUT" | tee -a "$LOG_FILE"
    return 0
  else
    local exit_code=$?
    log "ERROR" "Command failed (exit code: ${exit_code})"
    echo "$OUTPUT" | tee -a "$LOG_FILE"
    return $exit_code
  fi
}

# Check current service configuration 
check_service() {
  log "STEP" "1. Checking current Cloud Run service configuration"
  
  run_command "gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format=json" "Get service details" | tee /tmp/service_config.json
  
  # Extract important info
  SERVICE_URL=$(jq -r '.status.url' /tmp/service_config.json)
  INVOKER_MEMBERS=$(gcloud run services get-iam-policy ${SERVICE_NAME} --region=${REGION} --format=json | jq -r '.bindings[] | select(.role=="roles/run.invoker") | .members[]' 2>/dev/null || echo "None")
  
  log "INFO" "Service URL: ${SERVICE_URL}"
  log "INFO" "Current invoker members: ${INVOKER_MEMBERS}"
  
  # Test service
  log "INFO" "Testing service access..."
  run_command "curl -s -i ${SERVICE_URL}/health" "Test service health endpoint" || true
}

# Try to fix Cloud Run invoker permissions 
fix_cloud_run_permissions() {
  log "STEP" "2. Fixing Cloud Run invoker permissions"
  
  log "INFO" "Checking current IAM policy bindings..."
  run_command "gcloud run services get-iam-policy ${SERVICE_NAME} --region=${REGION}" "Get IAM policy"
  
  log "INFO" "Recreating Cloud Run service with unauthenticated access..."
  run_command "gcloud run services update ${SERVICE_NAME} --region=${REGION} --no-allow-unauthenticated" "Remove unauthenticated access" || true
  run_command "gcloud run services update ${SERVICE_NAME} --region=${REGION} --allow-unauthenticated" "Allow unauthenticated access" || {
    log "WARNING" "Failed to set allow-unauthenticated directly"
    
    # Trying alternative approach with IAM binding
    log "INFO" "Trying alternative approach with service identity..."
    SERVICE_IDENTITY=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(serviceIdentity.email)")
    log "INFO" "Service identity: ${SERVICE_IDENTITY}"
    
    # Find cloud run service agent
    CLOUD_RUN_SERVICE_AGENT="${PROJECT_ID}@serverless-robot-prod.iam.gserviceaccount.com"
    log "INFO" "Cloud Run service agent: ${CLOUD_RUN_SERVICE_AGENT}"
    
    # Grant permissions to service agent
    run_command "gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:${CLOUD_RUN_SERVICE_AGENT} --role=roles/run.invoker" "Grant run.invoker to service agent" || true
    
    # Try setting IAM policy with authenticated users
    log "INFO" "Adding authenticated users as invokers..."
    run_command "gcloud run services add-iam-policy-binding ${SERVICE_NAME} --region=${REGION} --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/run.invoker" "Add service account as invoker" || true
  }
  
  # Test service again
  log "INFO" "Testing service access after permission changes..."
  run_command "curl -s -i ${SERVICE_URL}/health" "Test service health endpoint again" || true
}

# Try to redeploy service with unauthenticated access
redeploy_service() {
  log "STEP" "3. Redeploying service with correct permissions"
  
  # Extract current image
  SERVICE_IMAGE=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(spec.template.spec.containers[0].image)")
  log "INFO" "Current service image: ${SERVICE_IMAGE}"
  
  if [ -n "$SERVICE_IMAGE" ]; then
    log "INFO" "Redeploying service with explicit unauthenticated access..."
    run_command "gcloud run deploy ${SERVICE_NAME} --image=${SERVICE_IMAGE} --region=${REGION} --platform=managed --allow-unauthenticated --quiet" "Redeploy service" || true
  else
    log "ERROR" "Could not determine service image"
  fi
  
  # Test service again
  log "INFO" "Testing service access after redeployment..."
  run_command "curl -s -i ${SERVICE_URL}/health" "Test service health endpoint after redeployment" || true
}

# Fix Vertex AI permissions
fix_vertex_ai_permissions() {
  log "STEP" "4. Fixing Vertex AI permissions"
  
  log "INFO" "Granting Vertex AI permissions to service account..."
  run_command "gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/aiplatform.user" "Grant aiplatform.user role"
  run_command "gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/aiplatform.serviceAgent" "Grant aiplatform.serviceAgent role"
  
  log "INFO" "Testing Vertex AI connectivity..."
  run_command "python3 gcp_migration/test_vertex_ai.py" "Test Vertex AI connectivity" || true
}

# Diagnose project settings
diagnose_project_settings() {
  log "STEP" "5. Diagnosing project settings"
  
  log "INFO" "Checking project settings..."
  run_command "gcloud projects describe ${PROJECT_ID} --format=json" "Get project details"
  
  log "INFO" "Checking org policies..."
  run_command "gcloud org-policies list --project=${PROJECT_ID}" "List org policies" || {
    log "INFO" "Could not list org policies directly, trying to check specific constraints..."
    run_command "gcloud org-policies describe constraints/iam.allowedPolicyMemberDomains --project=${PROJECT_ID}" "Check allowed policy member domains" || log "INFO" "No org policy for allowedPolicyMemberDomains"
  }
  
  log "INFO" "Checking service account permissions..."
  run_command "gcloud projects get-iam-policy ${PROJECT_ID} --format=json | jq '.bindings[] | select(.members[] | contains(\"${SERVICE_ACCOUNT}\"))'" "Check service account permissions"
}

# Generate Cloud Shell commands
generate_cloud_shell_commands() {
  log "STEP" "6. Generating Cloud Shell commands"
  
  CLOUD_SHELL_SCRIPT="gcp_migration/cloud_shell_commands.sh"
  
  cat > "$CLOUD_SHELL_SCRIPT" << EOF
#!/bin/bash
#
# Cloud Shell Commands for AI Orchestra GCP Migration
#
# Run these commands in Google Cloud Shell to fix permissions
#

# Set project
gcloud config set project ${PROJECT_ID}

# Check for organization policies that might restrict service account permissions
gcloud org-policies list --project=${PROJECT_ID}

# Check for domain restrictions policy
gcloud org-policies describe constraints/iam.allowedPolicyMemberDomains --project=${PROJECT_ID}

# Try to make Cloud Run service public
gcloud run services update ${SERVICE_NAME} --region=${REGION} --allow-unauthenticated

# Add IAM policy binding for allUsers
cat > /tmp/policy.json << 'EOT'
{
  "bindings": [
    {
      "role": "roles/run.invoker",
      "members": ["allUsers"]
    }
  ]
}
EOT
gcloud run services set-iam-policy ${SERVICE_NAME} /tmp/policy.json --region=${REGION}

# Add Vertex AI permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/aiplatform.user
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/aiplatform.serviceAgent
EOF

  chmod +x "$CLOUD_SHELL_SCRIPT"
  log "INFO" "Cloud Shell commands generated at: ${CLOUD_SHELL_SCRIPT}"
  
  # Show the script
  log "INFO" "Cloud Shell commands:"
  cat "$CLOUD_SHELL_SCRIPT" | tee -a "$LOG_FILE"
}

# Main function
main() {
  log "INFO" "Starting permission fixes for AI Orchestra GCP migration..."
  
  check_service
  fix_cloud_run_permissions
  redeploy_service
  fix_vertex_ai_permissions
  diagnose_project_settings
  generate_cloud_shell_commands
  
  log "INFO" "Permission fixes completed. Check the log file for details: ${LOG_FILE}"
}

# Execute main function
main
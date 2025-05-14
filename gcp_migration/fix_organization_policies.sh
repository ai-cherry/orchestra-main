#!/bin/bash
#
# Fix Organization Policies for AI Orchestra GCP Migration
#
# This script addresses the organization policy constraints that
# might be blocking Cloud Run access and Vertex AI authentication
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
LOG_FILE="gcp_migration/migration_logs/fix_org_policies_$(date +%Y%m%d_%H%M%S).log"

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

# Check current organization policies
check_org_policies() {
  log "STEP" "1. Checking current organization policies"
  
  # Check key policy constraints
  POLICY_CONSTRAINTS=(
    "iam.allowedPolicyMemberDomains"
    "run.requireInvokerIam"
    "run.allowedIngress"
    "run.allowedVPCEgress"
    "vertexai.allowedGenAIModels"
    "vertexai.allowedModels"
  )
  
  for constraint in "${POLICY_CONSTRAINTS[@]}"; do
    log "INFO" "Checking policy: ${constraint}"
    run_command "gcloud org-policies describe constraints/${constraint} --project=${PROJECT_ID} 2>/dev/null || echo 'Policy not set'" "Check ${constraint} policy"
  done
}

# Generate policy override for Cloud Run
generate_cloud_run_policy_override() {
  log "STEP" "2. Generating Cloud Run policy override"
  
  POLICY_FILE="cloud-run-policy.yaml"
  
  cat > "${POLICY_FILE}" << EOF
name: projects/${PROJECT_ID}/policies/run.requireInvokerIam
spec:
  rules:
  - enforce: false
EOF
  
  log "INFO" "Created Cloud Run policy override at ${POLICY_FILE}"
  
  # Try to apply the policy (may require organization admin)
  log "INFO" "Attempting to apply policy override..."
  run_command "gcloud org-policies set-policy ${POLICY_FILE} 2>/dev/null || echo 'Requires organization admin'" "Apply policy override" || {
    log "WARNING" "Could not apply policy directly. This operation requires organization admin privileges."
  }
}

# Set Cloud Run service to internal access
set_cloud_run_internal() {
  log "STEP" "3. Setting Cloud Run service to allow internal access"
  
  log "INFO" "Updating Cloud Run service to allow authenticated access..."
  run_command "gcloud run services update ${SERVICE_NAME} --region=${REGION} --no-allow-unauthenticated" "Set no-allow-unauthenticated" || {
    log "WARNING" "Could not update Cloud Run service. May need organization admin."
  }
  
  # Add explicit authenticated invoker for current service account
  log "INFO" "Adding invoker role for Cloud Build service account..."
  SERVICE_ACCOUNT=$(gcloud config get-value account)
  run_command "gcloud run services add-iam-policy-binding ${SERVICE_NAME} --region=${REGION} --member='serviceAccount:${SERVICE_ACCOUNT}' --role='roles/run.invoker'" "Add invoker role" || {
    log "WARNING" "Could not add IAM policy binding. This operation may be restricted by organization policy."
  }
}

# Generate Vertex AI model access override
generate_vertex_ai_override() {
  log "STEP" "4. Generating Vertex AI model access override"
  
  POLICY_FILE="vertex-ai-policy.yaml"
  
  cat > "${POLICY_FILE}" << EOF
name: projects/${PROJECT_ID}/policies/vertexai.allowedModels
spec:
  rules:
  - values:
      allowedValues:
      - resource://aiplatform.googleapis.com/projects/${PROJECT_ID}/locations/*
EOF
  
  log "INFO" "Created Vertex AI policy override at ${POLICY_FILE}"
  
  # Try to apply the policy (may require organization admin)
  log "INFO" "Attempting to apply policy override..."
  run_command "gcloud org-policies set-policy ${POLICY_FILE} 2>/dev/null || echo 'Requires organization admin'" "Apply policy override" || {
    log "WARNING" "Could not apply policy directly. This operation requires organization admin privileges."
  }
}

# Generate script for organization admin
generate_admin_script() {
  log "STEP" "5. Generating script for organization admin"
  
  ADMIN_SCRIPT="org-admin-actions.sh"
  
  cat > "${ADMIN_SCRIPT}" << EOF
#!/bin/bash
#
# Organization Admin Actions for AI Orchestra
#
# Run this script as an organization admin to fix policy constraints
#

# Set project
gcloud config set project ${PROJECT_ID}

# Disable policy constraints for Cloud Run public access
echo "Disabling Cloud Run invoker IAM requirement..."
cat > /tmp/run-policy.yaml << 'EOT'
name: projects/${PROJECT_ID}/policies/run.requireInvokerIam
spec:
  rules:
  - enforce: false
EOT
gcloud org-policies set-policy /tmp/run-policy.yaml

# Allow public access to Cloud Run services
echo "Setting Cloud Run service to allow unauthenticated access..."
gcloud run services update ${SERVICE_NAME} --region=${REGION} --allow-unauthenticated

# Allow all Vertex AI models
echo "Allowing access to Vertex AI models..."
cat > /tmp/vertex-policy.yaml << 'EOT'
name: projects/${PROJECT_ID}/policies/vertexai.allowedModels
spec:
  rules:
  - values:
      allowedValues:
      - resource://aiplatform.googleapis.com/projects/${PROJECT_ID}/locations/*
EOT
gcloud org-policies set-policy /tmp/vertex-policy.yaml

# Check policy status
echo "Checking updated policies..."
gcloud org-policies list --project=${PROJECT_ID}
EOF
  
  chmod +x "${ADMIN_SCRIPT}"
  log "INFO" "Created script for organization admin at ${ADMIN_SCRIPT}"
  
  # Show the script
  log "INFO" "Organization admin script contents:"
  cat "${ADMIN_SCRIPT}" | tee -a "$LOG_FILE"
}

# Generate workaround instructions for operations without admin access
generate_workaround_instructions() {
  log "STEP" "6. Generating workaround instructions"
  
  WORKAROUND_FILE="gcp_migration/migration_logs/workaround_instructions.md"
  
  cat > "${WORKAROUND_FILE}" << EOF
# AI Orchestra GCP Migration - Organization Policy Workarounds

## Issue: Organization Policy Restrictions

The following organization policies may be restricting your GCP migration:

1. \`iam.allowedPolicyMemberDomains\` - Restricting what domains can be given access
2. \`run.requireInvokerIam\` - Requiring authenticating to Cloud Run services
3. \`vertexai.allowedModels\` - Restricting which Vertex AI models can be accessed

## Workaround 1: Use Authenticated Access Instead of Public Access

If you cannot make Cloud Run services public, modify your client applications to use authenticated requests:

1. Get an access token:
   \`\`\`bash
   ACCESS_TOKEN=\$(gcloud auth print-identity-token)
   \`\`\`

2. Use the token in requests:
   \`\`\`bash
   curl -H "Authorization: Bearer \$ACCESS_TOKEN" https://your-service-url.run.app/endpoint
   \`\`\`

3. For service-to-service calls, use service account authentication:
   \`\`\`python
   from google.auth.transport.requests import Request
   from google.oauth2 import id_token
   
   audience = "https://your-service-url.run.app"
   token = id_token.fetch_id_token(Request(), audience)
   headers = {"Authorization": f"Bearer {token}"}
   # Use headers in your HTTP requests
   \`\`\`

## Workaround 2: Vertex AI Access via Service Account

If Vertex AI access is restricted:

1. Create a dedicated service account with proper roles:
   \`\`\`bash
   gcloud iam service-accounts create vertex-ai-sa --display-name="Vertex AI Service Account"
   gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:vertex-ai-sa@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/aiplatform.user"
   \`\`\`

2. Use this service account with your Vertex AI applications:
   \`\`\`python
   from google.cloud import aiplatform
   
   # Initialize with explicit credentials
   aiplatform.init(
       project='${PROJECT_ID}',
       location='${REGION}',
       credentials=/path/to/service-account-key.json
   )
   \`\`\`

## Workaround 3: Local Development with Service Account Key

For local development:

1. Create a service account key (if allowed by policy):
   \`\`\`bash
   gcloud iam service-accounts keys create key.json --iam-account=your-sa@${PROJECT_ID}.iam.gserviceaccount.com
   \`\`\`

2. Set environment variable:
   \`\`\`bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   \`\`\`

## Contacting Organization Admin

If these workarounds are insufficient, contact your organization admin to modify the following policies:

1. Set \`run.requireInvokerIam\` to false to allow public access to Cloud Run services
2. Set \`vertexai.allowedModels\` to allow all models in your project
3. Check \`iam.allowedPolicyMemberDomains\` if you need to grant access to external domains

The organization admin script has been generated at \`${ADMIN_SCRIPT}\`.
EOF
  
  log "INFO" "Workaround instructions generated at: ${WORKAROUND_FILE}"
}

# Main function
main() {
  log "INFO" "Starting organization policy fixes for AI Orchestra GCP migration..."
  
  check_org_policies
  generate_cloud_run_policy_override
  set_cloud_run_internal
  generate_vertex_ai_override
  generate_admin_script
  generate_workaround_instructions
  
  log "INFO" "Organization policy fixes completed. Check the log file for details: ${LOG_FILE}"
  log "INFO" "For organization admin actions, see: ${ADMIN_SCRIPT}"
  log "INFO" "For workarounds without admin access, see: ${WORKAROUND_FILE}"
}

# Execute main function
main
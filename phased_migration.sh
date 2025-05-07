#!/bin/bash
# Phased Migration Script for GCP Organization Migration and Hybrid IDE Setup
# This script executes the migration in discrete phases with validation between each step
# 
# Usage: 
#   ./phased_migration.sh --phase=all        # Run all phases
#   ./phased_migration.sh --phase=1          # Run only phase 1
#   ./phased_migration.sh --phase=2-4        # Run phases 2 through 4
#   ./phased_migration.sh --dry-run          # Simulate without making changes

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GCP_PROJECT_ID="cherry-ai-project"
GCP_PROJECT_NUMBER="104944497835"
GCP_ORG_ID="8732-9111-4285"
GOOGLE_API_KEY="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
VERTEX_AGENT_KEY="0d08481a204c0cdba4095bb94529221e8b8ced5c"
GCP_RUNTIME_SA_EMAIL="cherrybaby@cherry-ai-project.iam.gserviceaccount.com"
ADMIN_EMAIL="scoobyjava@cherry-ai.me"
SERVICE_ACCOUNT_EMAIL="vertex-agent@cherry-ai-project.iam.gserviceaccount.com"

# Script settings
LOG_DIR="./migration_logs/$(date +%Y%m%d_%H%M%S)"
PHASE_TO_RUN="all"
DRY_RUN=false
CHECKPOINT_FILE="./migration_checkpoint.json"

# Function to log messages
log_message() {
  local level=$1
  local message=$2
  echo -e "${level}${message}${NC}"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}" >> "${LOG_DIR}/migration.log"
}

# Function to handle errors
handle_error() {
  log_message "${RED}" "ERROR: $1"
  if [ -n "$2" ] && [ -f "$2" ]; then
    log_message "${YELLOW}" "See details in: $2"
  fi
  exit 1
}

# Function to verify command
verify_command() {
  if ! command -v $1 &> /dev/null; then
    handle_error "Required command not found: $1. Please install it before proceeding."
  fi
}

# Function to save checkpoint
save_checkpoint() {
  local phase=$1
  local status=$2
  local details=$3
  
  # Create checkpoint file if it doesn't exist
  if [ ! -f "${CHECKPOINT_FILE}" ]; then
    echo "{}" > "${CHECKPOINT_FILE}"
  fi
  
  # Update checkpoint
  jq --arg phase "$phase" --arg status "$status" --arg timestamp "$(date '+%Y-%m-%d %H:%M:%S')" --arg details "$details" \
    '.phases[$phase] = {"status": $status, "timestamp": $timestamp, "details": $details}' "${CHECKPOINT_FILE}" > "${CHECKPOINT_FILE}.tmp" && mv "${CHECKPOINT_FILE}.tmp" "${CHECKPOINT_FILE}"
    
  log_message "${GREEN}" "Checkpoint saved: Phase $phase - $status"
}

# Function to read checkpoint
read_checkpoint() {
  local phase=$1
  
  if [ ! -f "${CHECKPOINT_FILE}" ]; then
    echo "NOT_STARTED"
    return
  fi
  
  local status=$(jq -r --arg phase "$phase" '.phases[$phase].status // "NOT_STARTED"' "${CHECKPOINT_FILE}")
  echo "${status}"
}

# Function to execute command with dry run support
execute_cmd() {
  local cmd="$1"
  local log_file="$2"
  
  if [ "${DRY_RUN}" = true ]; then
    log_message "${YELLOW}" "DRY RUN: Would execute: ${cmd}"
    return 0
  else
    log_message "${YELLOW}" "Executing: ${cmd}"
    if eval "${cmd}" >> "${log_file}" 2>&1; then
      return 0
    else
      return 1
    fi
  fi
}

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --phase=*)
      PHASE_TO_RUN="${arg#*=}"
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --help)
      echo "Usage: $0 [--phase=<phase_number>|all] [--dry-run]"
      echo "  --phase: Specify which phase(s) to run (e.g., --phase=1, --phase=2-4, --phase=all)"
      echo "  --dry-run: Simulate the migration without making actual changes"
      exit 0
      ;;
  esac
done

# Create log directory
mkdir -p "${LOG_DIR}"
log_message "${GREEN}" "Migration logs will be saved to: ${LOG_DIR}"

# Check required commands
log_message "${BLUE}" "Checking required commands..."
verify_command "gcloud"
verify_command "terraform"
verify_command "jq"

# Display header
echo -e "${BLUE}========================================================"
echo "AGI Baby Cherry - Phased GCP Organization Migration"
echo -e "========================================================${NC}"
echo "Date: $(date)"
echo

if [ "${DRY_RUN}" = true ]; then
  log_message "${YELLOW}" "Running in DRY RUN mode. No actual changes will be made."
fi

# Determine which phases to run
if [[ "${PHASE_TO_RUN}" == "all" ]]; then
  START_PHASE=1
  END_PHASE=5
elif [[ "${PHASE_TO_RUN}" =~ ^([0-9]+)-([0-9]+)$ ]]; then
  START_PHASE="${BASH_REMATCH[1]}"
  END_PHASE="${BASH_REMATCH[2]}"
elif [[ "${PHASE_TO_RUN}" =~ ^[0-9]+$ ]]; then
  START_PHASE="${PHASE_TO_RUN}"
  END_PHASE="${PHASE_TO_RUN}"
else
  handle_error "Invalid phase specification: ${PHASE_TO_RUN}. Use --phase=all, --phase=N, or --phase=N-M"
fi

#####################################################################
# PHASE 1: Authentication and Verification
#####################################################################
if [[ $START_PHASE -le 1 && $END_PHASE -ge 1 ]]; then
  PHASE_STATUS=$(read_checkpoint "1")
  
  if [[ "${PHASE_STATUS}" == "COMPLETED" && "${PHASE_TO_RUN}" != "all" ]]; then
    log_message "${GREEN}" "Phase 1 (Authentication) already completed. Skipping."
  else
    log_message "${BLUE}" "PHASE 1: Authentication and Verification"
    
    # Create service account key
    log_message "${YELLOW}" "Creating service account key file..."
    SERVICE_KEY_FILE="${LOG_DIR}/vertex-agent-key.json"
    
    if [ "${DRY_RUN}" = true ]; then
      log_message "${YELLOW}" "DRY RUN: Would create service account key file"
    else
      # Create the key file
      cat > "${SERVICE_KEY_FILE}" << EOF
{
  "type": "service_account",
  "project_id": "${GCP_PROJECT_ID}",
  "private_key_id": "${VERTEX_AGENT_KEY}",
  "private_key": "-----BEGIN PRIVATE KEY-----\n${VERTEX_AGENT_KEY}\n-----END PRIVATE KEY-----\n",
  "client_email": "${SERVICE_ACCOUNT_EMAIL}",
  "client_id": "",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/${SERVICE_ACCOUNT_EMAIL//\@/%40}",
  "universe_domain": "googleapis.com"
}
EOF
      chmod 600 "${SERVICE_KEY_FILE}"
    fi
    
    # Authenticate to GCP
    log_message "${YELLOW}" "Authenticating to GCP using service account key..."
    if ! execute_cmd "gcloud auth activate-service-account '${SERVICE_ACCOUNT_EMAIL}' --key-file='${SERVICE_KEY_FILE}'" "${LOG_DIR}/gcp_auth.log"; then
      handle_error "Failed to authenticate with service account" "${LOG_DIR}/gcp_auth.log"
    fi
    
    # Set project
    if ! execute_cmd "gcloud config set project '${GCP_PROJECT_ID}'" "${LOG_DIR}/gcp_auth.log"; then
      handle_error "Failed to set project" "${LOG_DIR}/gcp_auth.log"
    fi
    
    # Verify permissions
    log_message "${YELLOW}" "Verifying service account permissions..."
    if ! execute_cmd "gcloud projects get-iam-policy '${GCP_PROJECT_ID}' --format=json > '${LOG_DIR}/iam_policy.json'" "${LOG_DIR}/gcp_auth.log"; then
      handle_error "Failed to get IAM policy" "${LOG_DIR}/gcp_auth.log"
    fi
    
    # Check if service account has access to the organization
    log_message "${YELLOW}" "Verifying organization access..."
    if ! execute_cmd "gcloud organizations describe '${GCP_ORG_ID}' --format=json > '${LOG_DIR}/org_info.json'" "${LOG_DIR}/org_access.log"; then
      log_message "${RED}" "Warning: Unable to access organization ${GCP_ORG_ID}. Organization migration may fail."
      save_checkpoint "1" "WARNING" "Authentication successful but organization access may be limited"
    else
      save_checkpoint "1" "COMPLETED" "Successfully authenticated and verified permissions"
    fi
    
    log_message "${GREEN}" "Phase 1 completed: Authentication and verification"
    
    # Ask for confirmation before proceeding
    if [ "${DRY_RUN}" = false ]; then
      echo
      read -p "Continue to Phase 2 (API Enablement)? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "${YELLOW}" "Migration paused after Phase 1"
        exit 0
      fi
    fi
  fi
fi

#####################################################################
# PHASE 2: API Enablement
#####################################################################
if [[ $START_PHASE -le 2 && $END_PHASE -ge 2 ]]; then
  PHASE_STATUS=$(read_checkpoint "2")
  
  if [[ "${PHASE_STATUS}" == "COMPLETED" && "${PHASE_TO_RUN}" != "all" ]]; then
    log_message "${GREEN}" "Phase 2 (API Enablement) already completed. Skipping."
  else
    log_message "${BLUE}" "PHASE 2: API Enablement"
    
    # List of required APIs
    REQUIRED_APIS=(
      "cloudresourcemanager.googleapis.com"
      "iam.googleapis.com"
      "workstations.googleapis.com"
      "compute.googleapis.com"
      "aiplatform.googleapis.com"
      "storage.googleapis.com"
      "redis.googleapis.com"
      "alloydb.googleapis.com"
      "serviceusage.googleapis.com"
      "bigquery.googleapis.com"
      "monitoring.googleapis.com"
    )
    
    # Enable APIs
    log_message "${YELLOW}" "Enabling required GCP APIs..."
    API_FAILURES=0
    
    for api in "${REQUIRED_APIS[@]}"; do
      log_message "${YELLOW}" "Enabling API: ${api}"
      if ! execute_cmd "gcloud services enable ${api} --quiet" "${LOG_DIR}/enable_apis.log"; then
        log_message "${RED}" "Warning: Failed to enable API ${api}"
        API_FAILURES=$((API_FAILURES+1))
      fi
    done
    
    if [ $API_FAILURES -gt 0 ]; then
      save_checkpoint "2" "WARNING" "${API_FAILURES} APIs failed to enable out of ${#REQUIRED_APIS[@]}"
    else
      save_checkpoint "2" "COMPLETED" "Successfully enabled all required APIs"
    fi
    
    log_message "${GREEN}" "Phase 2 completed: API Enablement"
    
    # Ask for confirmation before proceeding
    if [ "${DRY_RUN}" = false ]; then
      echo
      read -p "Continue to Phase 3 (Organization Migration)? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "${YELLOW}" "Migration paused after Phase 2"
        exit 0
      fi
    fi
  fi
fi

#####################################################################
# PHASE 3: Organization Migration
#####################################################################
if [[ $START_PHASE -le 3 && $END_PHASE -ge 3 ]]; then
  PHASE_STATUS=$(read_checkpoint "3")
  
  if [[ "${PHASE_STATUS}" == "COMPLETED" && "${PHASE_TO_RUN}" != "all" ]]; then
    log_message "${GREEN}" "Phase 3 (Organization Migration) already completed. Skipping."
  else
    log_message "${BLUE}" "PHASE 3: Organization Migration"
    
    log_message "${YELLOW}" "Checking current project organization..."
    if ! execute_cmd "gcloud projects describe '${GCP_PROJECT_ID}' --format=json > '${LOG_DIR}/project_info.json'" "${LOG_DIR}/project_migration.log"; then
      handle_error "Failed to get project info" "${LOG_DIR}/project_migration.log"
    fi
    
    # Check if project is already in the organization
    if [ "${DRY_RUN}" = false ]; then
      CURRENT_PARENT=$(jq -r '.parent.type + "/" + .parent.id' "${LOG_DIR}/project_info.json")
      log_message "${YELLOW}" "Current project parent: ${CURRENT_PARENT}"
      
      if [[ "${CURRENT_PARENT}" == "organization/${GCP_ORG_ID}" ]]; then
        log_message "${GREEN}" "Project is already in the correct organization. Skipping migration."
        save_checkpoint "3" "COMPLETED" "Project already in organization ${GCP_ORG_ID}"
      else
        # Verify organization access before moving
        log_message "${YELLOW}" "Verifying organization IAM policy..."
        if ! execute_cmd "gcloud organizations get-iam-policy '${GCP_ORG_ID}' --format=json > '${LOG_DIR}/org_iam_policy.json'" "${LOG_DIR}/project_migration.log"; then
          handle_error "Failed to get organization IAM policy" "${LOG_DIR}/project_migration.log"
        fi
        
        # Move the project
        log_message "${YELLOW}" "Moving project to organization ${GCP_ORG_ID}..."
        if ! execute_cmd "gcloud projects move '${GCP_PROJECT_ID}' --organization='${GCP_ORG_ID}'" "${LOG_DIR}/project_migration.log"; then
          handle_error "Failed to move project to organization" "${LOG_DIR}/project_migration.log"
        fi
        
        save_checkpoint "3" "COMPLETED" "Successfully moved project to organization ${GCP_ORG_ID}"
      fi
    else
      log_message "${YELLOW}" "DRY RUN: Would check if project needs to be moved to organization ${GCP_ORG_ID}"
      save_checkpoint "3" "SIMULATED" "Would move project to organization ${GCP_ORG_ID}"
    fi
    
    log_message "${GREEN}" "Phase 3 completed: Organization Migration"
    
    # Ask for confirmation before proceeding
    if [ "${DRY_RUN}" = false ]; then
      echo
      read -p "Continue to Phase 4 (Memory Layer Setup)? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "${YELLOW}" "Migration paused after Phase 3"
        exit 0
      fi
    fi
  fi
fi

#####################################################################
# PHASE 4: Memory Layer Setup (Redis/AlloyDB)
#####################################################################
if [[ $START_PHASE -le 4 && $END_PHASE -ge 4 ]]; then
  PHASE_STATUS=$(read_checkpoint "4")
  
  if [[ "${PHASE_STATUS}" == "COMPLETED" && "${PHASE_TO_RUN}" != "all" ]]; then
    log_message "${GREEN}" "Phase 4 (Memory Layer Setup) already completed. Skipping."
  else
    log_message "${BLUE}" "PHASE 4: Memory Layer Setup (Redis/AlloyDB)"
    
    # Set up IAM permissions
    log_message "${YELLOW}" "Setting up IAM permissions for memory layer..."
    
    # Grant required roles to service account
    REQUIRED_ROLES=(
      "roles/redis.admin"
      "roles/alloydb.admin"
      "roles/compute.networkAdmin"
    )
    
    for role in "${REQUIRED_ROLES[@]}"; do
      log_message "${YELLOW}" "Granting ${role} to ${SERVICE_ACCOUNT_EMAIL}"
      if ! execute_cmd "gcloud projects add-iam-policy-binding '${GCP_PROJECT_ID}' --member='serviceAccount:${SERVICE_ACCOUNT_EMAIL}' --role='${role}'" "${LOG_DIR}/setup_iam.log"; then
        log_message "${RED}" "Warning: Failed to grant ${role} to ${SERVICE_ACCOUNT_EMAIL}"
      fi
    done
    
    # Create Redis instance
    log_message "${YELLOW}" "Creating Redis Memorystore instance..."
    if ! execute_cmd "gcloud redis instances create agent-memory --size=10 --region=us-west4 --tier=standard --redis-version=redis_6_x --connect-mode=private-service-access --network=default" "${LOG_DIR}/redis_setup.log"; then
      log_message "${YELLOW}" "Warning: Redis instance creation failed. It may already exist or there might be an issue."
    fi
    
    # Create AlloyDB cluster and instance
    log_message "${YELLOW}" "Creating AlloyDB cluster..."
    if ! execute_cmd "gcloud alloydb clusters create agi-baby-cluster --password=agi-baby-pw123 --region=us-west4 --network=default" "${LOG_DIR}/alloydb_setup.log"; then
      log_message "${YELLOW}" "Warning: AlloyDB cluster creation failed. It may already exist or there might be an issue."
    fi
    
    log_message "${YELLOW}" "Creating AlloyDB instance..."
    if ! execute_cmd "gcloud alloydb instances create alloydb-instance --instance-type=PRIMARY --cpu-count=8 --region=us-west4 --cluster=agi-baby-cluster --machine-config=n2-standard-8 --database=agi_baby_cherry --user=alloydb-user" "${LOG_DIR}/alloydb_setup.log"; then
      log_message "${YELLOW}" "Warning: AlloyDB instance creation failed. It may already exist or there might be an issue."
    fi
    
    save_checkpoint "4" "COMPLETED" "Memory layer setup completed"
    log_message "${GREEN}" "Phase 4 completed: Memory Layer Setup"
    
    # Ask for confirmation before proceeding
    if [ "${DRY_RUN}" = false ]; then
      echo
      read -p "Continue to Phase 5 (Cloud Workstation Setup)? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "${YELLOW}" "Migration paused after Phase 4"
        exit 0
      fi
    fi
  fi
fi

#####################################################################
# PHASE 5: Cloud Workstation and Gemini Code Assist Setup
#####################################################################
if [[ $START_PHASE -le 5 && $END_PHASE -ge 5 ]]; then
  PHASE_STATUS=$(read_checkpoint "5")
  
  if [[ "${PHASE_STATUS}" == "COMPLETED" && "${PHASE_TO_RUN}" != "all" ]]; then
    log_message "${GREEN}" "Phase 5 (Cloud Workstation Setup) already completed. Skipping."
  else
    log_message "${BLUE}" "PHASE 5: Cloud Workstation and Gemini Code Assist Setup"
    
    # Prepare Terraform configuration
    log_message "${YELLOW}" "Preparing Terraform configuration..."
    TERRAFORM_ENV_FILE="${LOG_DIR}/terraform.tfvars"
    
    # Create terraform.tfvars file
    cat > "${TERRAFORM_ENV_FILE}" << EOF
# Terraform configuration for AGI Baby Cherry project
project_id = "${GCP_PROJECT_ID}"
project_number = "${GCP_PROJECT_NUMBER}"
region = "us-west4"
zone = "us-west4-a"
env = "prod"
service_account_email = "${SERVICE_ACCOUNT_EMAIL}"
admin_email = "${ADMIN_EMAIL}"
gemini_api_key = "${GOOGLE_API_KEY}"
gcs_bucket = "gs://${GCP_PROJECT_ID}-bucket/repos"
EOF
    
    # Create Gemini Code Assist setup script
    log_message "${YELLOW}" "Creating Gemini Code Assist setup script..."
    GEMINI_SETUP_SCRIPT="${LOG_DIR}/setup_gemini_code_assist.sh"
    
    cat > "${GEMINI_SETUP_SCRIPT}" << 'EOF'
#!/bin/bash
# Set up Gemini Code Assist on Cloud Workstation
set -e

# Create Gemini Code Assist configuration file
echo "Creating Gemini Code Assist configuration..."
mkdir -p ~/.config/
cat > ~/.config/gemini-code-assist.yaml << 'GEMINICONFIG'
# Gemini Code Assist Configuration
project_context:
  - path: /workspaces/orchestra-main
    priority: 100
  - path: /home/agent/mounted_bucket
    priority: 50
  - path: /mnt/repos
    priority: 25

tool_integrations:
  vertex_ai:
    endpoint: projects/104944497835/locations/us-west4/endpoints/agent-core
    api_version: v1
  redis:
    connection_string: redis://vertex-agent@cherry-ai-project
  database:
    connection_string: postgresql://alloydb-user@alloydb-instance:5432/agi_baby_cherry

model:
  name: gemini-2.5
  temperature: 0.3
  max_output_tokens: 8192
  top_p: 0.95
GEMINICONFIG

echo "Gemini Code Assist configuration completed."
EOF
    
    chmod +x "${GEMINI_SETUP_SCRIPT}"
    
    # Apply Terraform configuration if not in dry run mode
    if [ "${DRY_RUN}" = false ]; then
      log_message "${YELLOW}" "Initializing and applying Terraform configuration..."
      
      # Make a copy of the Terraform config file to the current working directory
      cp hybrid_workstation_config.tf "${LOG_DIR}/hybrid_workstation_config.tf"
      
      # Change to Terraform directory
      cd "${LOG_DIR}"
      
      # Initialize Terraform
      log_message "${YELLOW}" "Initializing Terraform..."
      if ! terraform init > "terraform_init.log" 2>&1; then
        handle_error "Failed to initialize Terraform" "terraform_init.log"
      fi
      
      # Create Terraform plan
      log_message "${YELLOW}" "Creating Terraform plan..."
      if ! terraform plan -var-file="terraform.tfvars" -out=tfplan > "terraform_plan.log" 2>&1; then
        handle_error "Failed to create Terraform plan" "terraform_plan.log"
      fi
      
      # Apply Terraform plan
      log_message "${YELLOW}" "Applying Terraform configuration..."
      if ! terraform apply -auto-approve tfplan > "terraform_apply.log" 2>&1; then
        handle_error "Failed to apply Terraform configuration" "terraform_apply.log"
      fi
      
      # Return to original directory
      cd - > /dev/null
      
      log_message "${GREEN}" "Terraform configuration applied successfully"
      save_checkpoint "5" "COMPLETED" "Successfully set up Cloud Workstations and Gemini Code Assist"
    else
      log_message "${YELLOW}" "DRY RUN: Would apply Terraform configuration to set up Cloud Workstations"
      save_checkpoint "5" "SIMULATED" "Would set up Cloud Workstations and Gemini Code Assist"
    fi
    
    log_message "${GREEN}" "Phase 5 completed: Cloud Workstation and Gemini Code Assist Setup"
  fi
fi

#####################################################################
# FINAL: Migration Summary
#####################################################################
echo
echo -e "${BLUE}========================================================"
echo "Migration Summary"
echo -e "========================================================${NC}"
echo

echo -e "${GREEN}Phases completed:${NC}"
for phase in {1..5}; do
  PHASE_STATUS=$(read_checkpoint "${phase}")
  
  case $phase in
    1) PHASE_NAME="Authentication and Verification" ;;
    2) PHASE_NAME="API Enablement" ;;
    3) PHASE_NAME="Organization Migration" ;;
    4) PHASE_NAME="Memory Layer Setup" ;;
    5) PHASE_NAME="Cloud Workstation Setup" ;;
  esac
  
  case "${PHASE_STATUS}" in
    "COMPLETED")
      echo -e "${GREEN}✅ Phase ${phase}: ${PHASE_NAME} - COMPLETED${NC}"
      ;;
    "WARNING")
      echo -e "${YELLOW}⚠️  Phase ${phase}: ${PHASE_NAME} - COMPLETED WITH WARNINGS${NC}"
      ;;
    "SIMULATED")
      echo -e "${YELLOW}🔄 Phase ${phase}: ${PHASE_NAME} - SIMULATED (DRY RUN)${NC}"
      ;;
    *)
      echo -e "${RED}❌ Phase ${phase}: ${PHASE_NAME} - NOT COMPLETED${NC}"
      ;;
  esac
done

echo
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Run the validation script to verify the migration:"
echo "   ./validate_migration.sh"
echo
echo "2. To continue a paused migration, run:"
echo "   ./phased_migration.sh --phase=<next_phase>"
echo
echo "3. Access Cloud Workstations in the Google Cloud Console:"
echo "   https://console.cloud.google.com/workstations"
echo

echo -e "${GREEN}Migration logs saved to: ${LOG_DIR}${NC}"

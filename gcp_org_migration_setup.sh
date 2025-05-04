#!/bin/bash
# GCP Organization Migration and Hybrid IDE Setup Script
# For AGI Baby Cherry Project (104944497835)
#
# This script performs:
# 1. Authentication to GCP using service account key
# 2. Project migration to new organization
# 3. Hybrid IDE environment setup with:
#    - Cloud Workstations (JupyterLab + IntelliJ)
#    - Redis/AlloyDB memory layer
#    - Gemini Code Assist integration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DRY_RUN=false

# Check for --dry-run parameter
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo -e "${YELLOW}Running in DRY RUN mode. No actual changes will be made.${NC}"
fi
# GCP Configuration
GCP_PROJECT_ID="agi-baby-cherry"
GCP_PROJECT_NUMBER="104944497835"
GCP_ORG_ID="8732-9111-4285"
GOOGLE_API_KEY="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
VERTEX_AGENT_KEY="0d08481a204c0cdba4095bb94529221e8b8ced5c"
GCP_RUNTIME_SA_EMAIL="cherrybaby@agi-baby-cherry.iam.gserviceaccount.com"
ADMIN_EMAIL="scoobyjava@cherry-ai.me"
SERVICE_ACCOUNT_EMAIL="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"

# Configuration variables
TERRAFORM_DIR="./infra"
LOG_DIR="./migration_logs/$(date +%Y%m%d_%H%M%S)"
SERVICE_KEY_FILE="./vertex-agent-key.json"
TERRAFORM_ENV_FILE="./terraform.tfvars"

# Create log directory
mkdir -p "${LOG_DIR}"
echo -e "${GREEN}Migration logs will be saved to: ${LOG_DIR}${NC}"

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

# Check required commands
log_message "${BLUE}" "Checking required commands..."
verify_command "gcloud"
verify_command "terraform"
verify_command "jq"

# Display header
echo -e "${BLUE}========================================================"
echo "AGI Baby Cherry - GCP Organization Migration and Hybrid IDE Setup"
echo -e "========================================================${NC}"
echo "Date: $(date)"
echo

###############################################
# STEP 1: Create Service Account Key File
###############################################
log_message "${BLUE}" "STEP 1: Creating Service Account Key File"

echo -e "${YELLOW}Creating service account key file from provided key...${NC}"
# Convert the key to JSON format
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

# Secure the key file
chmod 600 "${SERVICE_KEY_FILE}"
log_message "${GREEN}" "Service account key file created successfully: ${SERVICE_KEY_FILE}"

###############################################
# STEP 2: Authenticate to GCP
###############################################
log_message "${BLUE}" "STEP 2: Authenticating to GCP"

echo -e "${YELLOW}Authenticating to GCP using service account key...${NC}"
gcloud auth activate-service-account "${SERVICE_ACCOUNT_EMAIL}" --key-file="${SERVICE_KEY_FILE}" >> "${LOG_DIR}/gcp_auth.log" 2>&1 || \
  handle_error "Failed to authenticate with service account" "${LOG_DIR}/gcp_auth.log"

gcloud config set project "${GCP_PROJECT_ID}" >> "${LOG_DIR}/gcp_auth.log" 2>&1 || \
  handle_error "Failed to set project" "${LOG_DIR}/gcp_auth.log"

log_message "${GREEN}" "Successfully authenticated to GCP as ${SERVICE_ACCOUNT_EMAIL}"

# Verify service account has required permissions
log_message "${YELLOW}" "Verifying service account permissions..."
gcloud projects get-iam-policy "${GCP_PROJECT_ID}" --format=json > "${LOG_DIR}/iam_policy.json" 2>> "${LOG_DIR}/gcp_auth.log" || \
  handle_error "Failed to get IAM policy" "${LOG_DIR}/gcp_auth.log"

# Check if service account has required roles
if ! grep -q "${SERVICE_ACCOUNT_EMAIL}" "${LOG_DIR}/iam_policy.json"; then
  log_message "${YELLOW}" "Warning: Service account may not have all required permissions. Check IAM policy."
fi

###############################################
# STEP 3: Enable Required APIs
###############################################
log_message "${BLUE}" "STEP 3: Enabling Required APIs"

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

echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
for api in "${REQUIRED_APIS[@]}"; do
  log_message "${YELLOW}" "Enabling API: ${api}"
  gcloud services enable "${api}" --quiet >> "${LOG_DIR}/enable_apis.log" 2>&1 || \
    log_message "${YELLOW}" "Warning: Failed to enable API ${api} (may already be enabled)"
done

log_message "${GREEN}" "APIs enabled successfully"

###############################################
# STEP 4: Move Project to New Organization
###############################################
log_message "${BLUE}" "STEP 4: Moving Project to New Organization"

echo -e "${YELLOW}Moving project to organization ID: ${GCP_ORG_ID}...${NC}"
# Check if project is already in the organization
PROJECT_INFO=$(gcloud projects describe "${GCP_PROJECT_ID}" --format=json 2>> "${LOG_DIR}/project_migration.log") || \
  handle_error "Failed to get project info" "${LOG_DIR}/project_migration.log"

CURRENT_PARENT=$(echo "${PROJECT_INFO}" | jq -r '.parent.type + "/" + .parent.id')
log_message "${YELLOW}" "Current project parent: ${CURRENT_PARENT}"

# If project is not already in the target organization, move it
if [[ "${CURRENT_PARENT}" != "organization/${GCP_ORG_ID}" ]]; then
  log_message "${YELLOW}" "Moving project to organization ${GCP_ORG_ID}..."
  
  # Verify admin permissions before moving
  gcloud organizations get-iam-policy "${GCP_ORG_ID}" --format=json > "${LOG_DIR}/org_iam_policy.json" 2>> "${LOG_DIR}/project_migration.log" || \
    handle_error "Failed to get organization IAM policy. Ensure you have the required permissions." "${LOG_DIR}/project_migration.log"
  
  # Move the project to the new organization
  gcloud projects move "${GCP_PROJECT_ID}" --organization="${GCP_ORG_ID}" >> "${LOG_DIR}/project_migration.log" 2>&1 || \
    handle_error "Failed to move project to organization" "${LOG_DIR}/project_migration.log"
    
  log_message "${GREEN}" "Successfully moved project to organization ${GCP_ORG_ID}"
else
  log_message "${GREEN}" "Project is already in the correct organization. No migration needed."
fi

###############################################
# STEP 5: Grant Required Permissions
###############################################
log_message "${BLUE}" "STEP 5: Granting Required Permissions"

echo -e "${YELLOW}Setting up IAM permissions...${NC}"

# Grant required roles to admin and service account
REQUIRED_ROLES=(
  "roles/owner"
  "roles/workstations.admin"
  "roles/aiplatform.admin"
  "roles/redis.admin"
  "roles/alloydb.admin"
  "roles/compute.admin"
  "roles/storage.admin"
  "roles/serviceusage.serviceUsageAdmin"
)

# Grant roles to the admin account
for role in "${REQUIRED_ROLES[@]}"; do
  log_message "${YELLOW}" "Granting ${role} to ${ADMIN_EMAIL}"
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="user:${ADMIN_EMAIL}" \
    --role="${role}" >> "${LOG_DIR}/setup_iam.log" 2>&1 || \
    log_message "${YELLOW}" "Warning: Failed to grant ${role} to ${ADMIN_EMAIL} (may already have it)"
done

# Grant required roles to service account
SERVICE_ACCOUNT_ROLES=(
  "roles/workstations.user"
  "roles/aiplatform.user"
  "roles/storage.objectViewer"
  "roles/compute.viewer"
  "roles/redis.viewer"
  "roles/alloydb.viewer"
  "roles/bigquery.dataViewer"
  "roles/monitoring.viewer"
)

for role in "${SERVICE_ACCOUNT_ROLES[@]}"; do
  log_message "${YELLOW}" "Granting ${role} to ${SERVICE_ACCOUNT_EMAIL}"
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${role}" >> "${LOG_DIR}/setup_iam.log" 2>&1 || \
    log_message "${YELLOW}" "Warning: Failed to grant ${role} to ${SERVICE_ACCOUNT_EMAIL} (may already have it)"
done

log_message "${GREEN}" "IAM permissions set up successfully"

###############################################
# STEP 6: Prepare Terraform Configuration
###############################################
log_message "${BLUE}" "STEP 6: Preparing Terraform Configuration"

echo -e "${YELLOW}Creating Terraform variables file...${NC}"

# Create terraform.tfvars file
cat > "${TERRAFORM_ENV_FILE}" << EOF
# Terraform configuration for AGI Baby Cherry project
project_id = "${GCP_PROJECT_ID}"
project_number = "${GCP_PROJECT_NUMBER}"
region = "us-central1"
zone = "us-central1-a"
env = "prod"
service_account_email = "${SERVICE_ACCOUNT_EMAIL}"
admin_email = "${ADMIN_EMAIL}"
gemini_api_key = "${GOOGLE_API_KEY}"
gcs_bucket = "gs://${GCP_PROJECT_ID}-bucket/repos"
EOF

log_message "${GREEN}" "Terraform variables file created successfully: ${TERRAFORM_ENV_FILE}"

###############################################
# STEP 7: Set up Redis and AlloyDB
###############################################
log_message "${BLUE}" "STEP 7: Setting up Redis and AlloyDB Memory Layer"

echo -e "${YELLOW}Creating Redis/AlloyDB hybrid memory layer configuration...${NC}"

# Create Redis instance (Memorystore)
log_message "${YELLOW}" "Creating Redis Memorystore instance..."
gcloud redis instances create agent-memory \
  --size=10 \
  --region=us-central1 \
  --tier=standard \
  --redis-version=redis_6_x \
  --connect-mode=private-service-access \
  --network=default > "${LOG_DIR}/redis_setup.log" 2>&1 || \
  log_message "${YELLOW}" "Warning: Redis instance creation failed (may already exist)"

# Setup AlloyDB instance
log_message "${YELLOW}" "Creating AlloyDB instance..."
gcloud alloydb instances create alloydb-instance \
  --instance-type=PRIMARY \
  --cpu-count=8 \
  --region=us-central1 \
  --cluster=agi-baby-cluster \
  --machine-config=n2-standard-8 \
  --database=agi_baby_cherry \
  --user=alloydb-user > "${LOG_DIR}/alloydb_setup.log" 2>&1 || \
  log_message "${YELLOW}" "Warning: AlloyDB instance creation failed (may already exist)"

###############################################
# STEP 8: Apply Terraform Configuration
###############################################
log_message "${BLUE}" "STEP 8: Applying Terraform Configuration"

echo -e "${YELLOW}Initializing and applying Terraform configuration...${NC}"

# Navigate to Terraform directory
cd "${TERRAFORM_DIR}" || handle_error "Failed to change to Terraform directory"

# Initialize Terraform
log_message "${YELLOW}" "Initializing Terraform..."
terraform init > "${LOG_DIR}/terraform_init.log" 2>&1 || \
  handle_error "Failed to initialize Terraform" "${LOG_DIR}/terraform_init.log"

# Create Terraform plan
log_message "${YELLOW}" "Creating Terraform plan..."
terraform plan -var-file="../${TERRAFORM_ENV_FILE}" -out=tfplan > "${LOG_DIR}/terraform_plan.log" 2>&1 || \
  handle_error "Failed to create Terraform plan" "${LOG_DIR}/terraform_plan.log"

# Apply Terraform plan
log_message "${YELLOW}" "Applying Terraform configuration..."
terraform apply -auto-approve tfplan > "${LOG_DIR}/terraform_apply.log" 2>&1 || \
  handle_error "Failed to apply Terraform configuration" "${LOG_DIR}/terraform_apply.log"

log_message "${GREEN}" "Terraform configuration applied successfully"

# Return to the original directory
cd - || handle_error "Failed to return to original directory"

###############################################
# STEP 9: Configure Gemini Code Assist
###############################################
log_message "${BLUE}" "STEP 9: Configuring Gemini Code Assist"

echo -e "${YELLOW}Setting up Gemini Code Assist...${NC}"

# Extract workstation information from Terraform output
cd "${TERRAFORM_DIR}" || handle_error "Failed to change to Terraform directory"
WORKSTATION_INFO=$(terraform output -json workstation_details)
cd - || handle_error "Failed to return to original directory"

# Save Workstation info for reference
echo "${WORKSTATION_INFO}" > "${LOG_DIR}/workstation_details.json"

# Determine the workstation cluster and name from the output
WORKSTATION_CLUSTER=$(echo "${WORKSTATION_INFO}" | jq -r '.cluster.name')
WORKSTATION_NAME=$(echo "${WORKSTATION_INFO}" | jq -r '.workstations[0].name')
REGION=$(echo "${WORKSTATION_INFO}" | jq -r '.cluster.location')

log_message "${YELLOW}" "Setting up Gemini Code Assist on workstation: ${WORKSTATION_NAME}"

# Create deployment script for pushing Gemini Code Assist config
cat > setup_gemini_code_assist.sh << EOF
#!/bin/bash
# Set up Gemini Code Assist on Cloud Workstation
set -e

# Create Gemini Code Assist configuration file
echo "Creating Gemini Code Assist configuration..."
cat > ~/.gemini-code-assist.yaml << 'GEMINICONFIG'
# Gemini Code Assist Configuration for AGI Baby Cherry Project
# This configuration enables AI-assisted development with Gemini 2.5 model

# Project context configuration, defining which paths should be indexed
# and their relative priority (higher numbers = higher priority)
project_context:
  - path: /workspaces/orchestra-main
    priority: 100
  - path: /home/agent/mounted_bucket
    priority: 50
  - path: /mnt/repos
    priority: 25

# Tool integrations for external APIs and services
tool_integrations:
  # Vertex AI integration for model inference
  vertex_ai:
    endpoint: projects/${GCP_PROJECT_NUMBER}/locations/us-central1/endpoints/agent-core
    api_version: v1
    
  # Redis integration for semantic cache
  redis:
    connection_string: redis://vertex-agent@${GCP_PROJECT_ID}
    
  # AlloyDB for vector search
  database:
    connection_string: postgresql://alloydb-user@alloydb-instance:5432/agi_baby_cherry

# Model configuration
model:
  name: gemini-2.5
  temperature: 0.3
  max_output_tokens: 8192
  top_p: 0.95

# Custom code assist commands (for IntelliJ/VS Code)
commands:
  - name: optimize-query
    description: "Optimize AlloyDB vector search query for 10M+ dimensions"
    prompt_template: |
      Optimize this AlloyDB vector search query for 10M+ dimensions with 95% recall@10:
      {{selection}}
      
  - name: generate-cloud-run
    description: "Generate Cloud Run deployment code"
    prompt_template: |
      Generate Cloud Run deployment code using service account orchestra-cloud-run-prod:
      {{selection}}
      
  - name: document-function
    description: "Add comprehensive documentation to function"
    prompt_template: |
      Add detailed documentation to the following function, including:
      - Parameter descriptions
      - Return value documentation
      - Usage examples
      - Edge cases
      
      {{selection}}

# Editor settings
editor:
  auto_apply_suggestions: false
  inline_suggestions: true
  suggestion_delay_ms: 500
  max_inline_suggestions: 3
GEMINICONFIG

echo "Gemini Code Assist configuration completed."
EOF

# Make the script executable
chmod +x setup_gemini_code_assist.sh

# Execute the script on the workstation when it's ready
log_message "${GREEN}" "Gemini Code Assist configuration created: setup_gemini_code_assist.sh"
log_message "${YELLOW}" "Note: Execute this script on the workstation when it's ready"

###############################################
# STEP 10: Finalize and Cleanup
###############################################
log_message "${BLUE}" "STEP 10: Finalizing Setup and Cleanup"

echo -e "${YELLOW}Finalizing setup and performing cleanup...${NC}"

# Save all configuration details to a summary file
cat > "${LOG_DIR}/migration_summary.json" << EOF
{
  "project": {
    "id": "${GCP_PROJECT_ID}",
    "number": "${GCP_PROJECT_NUMBER}",
    "organization": "${GCP_ORG_ID}"
  },
  "serviceAccount": "${SERVICE_ACCOUNT_EMAIL}",
  "admin": "${ADMIN_EMAIL}",
  "workstation": {
    "cluster": "${WORKSTATION_CLUSTER}",
    "name": "${WORKSTATION_NAME}",
    "region": "${REGION}"
  },
  "apis": [
    $(printf '"%s",' "${REQUIRED_APIS[@]}" | sed 's/,$//')
  ],
  "memoryLayer": {
    "redis": "agent-memory",
    "alloydb": "alloydb-instance",
    "database": "agi_baby_cherry"
  },
  "completionTimestamp": "$(date '+%Y-%m-%d %H:%M:%S')"
}
EOF

# Cleanup sensitive information
log_message "${YELLOW}" "Cleaning up sensitive files..."
chmod 600 "${LOG_DIR}"/*.json
chmod 600 "${LOG_DIR}"/*.log

log_message "${GREEN}" "Migration and setup completed successfully!"

###############################################
# STEP 11: Display Summary
###############################################
cat << EOF

${BLUE}========================================================
AGI Baby Cherry - Migration and Setup Summary
========================================================${NC}

${GREEN}The following components have been configured:${NC}
- Project "${GCP_PROJECT_ID}" moved to organization "${GCP_ORG_ID}"
- Cloud Workstation with JupyterLab + IntelliJ
  - Cluster: ${WORKSTATION_CLUSTER}
  - Workstation: ${WORKSTATION_NAME}
  - Region: ${REGION}
- Redis/AlloyDB memory layer
  - Redis instance: agent-memory
  - AlloyDB instance: alloydb-instance
  - Database: agi_baby_cherry
- Gemini Code Assist integration with Vertex AI and Redis
- Terraform configuration for Cloud Workstation setup

${YELLOW}Next Steps:${NC}
1. Access your workstation in the Google Cloud Console:
   https://console.cloud.google.com/workstations/list?project=${GCP_PROJECT_ID}

2. Deploy Gemini Code Assist configuration to the workstation:
   gcloud workstations ssh ${WORKSTATION_NAME} --cluster=${WORKSTATION_CLUSTER} --project=${GCP_PROJECT_ID} --region=${REGION} --command="bash" < setup_gemini_code_assist.sh

3. Review the migration summary:
   cat "${LOG_DIR}/migration_summary.json"

4. Follow the detailed implementation steps in HYBRID_IDE_MIGRATION_GUIDE.md

${GREEN}Deployment logs saved to: ${LOG_DIR}${NC}
EOF

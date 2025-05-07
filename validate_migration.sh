#!/bin/bash
# Validation Script for GCP Organization Migration and Hybrid IDE Setup
# This script tests if all components have been successfully configured
# 
# Usage: ./validate_migration.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GCP Configuration from our setup script
GCP_PROJECT_ID="cherry-ai-project"
GCP_PROJECT_NUMBER="104944497835"
GCP_ORG_ID="873291114285"  # Corrected numeric ID without hyphens
GOOGLE_API_KEY="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
SERVICE_ACCOUNT_EMAIL="vertex-agent@cherry-ai-project.iam.gserviceaccount.com"

# Validation results storage
VALIDATION_LOG="./validation_results_$(date +%Y%m%d_%H%M%S).log"
FAILED_TESTS=0
PASSED_TESTS=0

# Function to log messages
log_message() {
  local level=$1
  local message=$2
  echo -e "${level}${message}${NC}"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}" >> "${VALIDATION_LOG}"
}

# Function to record test results
record_test() {
  local test_name=$1
  local result=$2
  local details=$3
  
  if [ "$result" = "PASS" ]; then
    log_message "${GREEN}" "✅ PASS: ${test_name}"
    PASSED_TESTS=$((PASSED_TESTS+1))
  else
    log_message "${RED}" "❌ FAIL: ${test_name} - ${details}"
    FAILED_TESTS=$((FAILED_TESTS+1))
  fi
}

# Display header
echo -e "${BLUE}========================================================"
echo "Validation Test for AGI Baby Cherry GCP Migration"
echo -e "========================================================${NC}"
echo "Date: $(date)"
echo "Results will be logged to: ${VALIDATION_LOG}"
echo

###############################################
# STEP 1: Test GCP Authentication
###############################################
log_message "${BLUE}" "STEP 1: Testing GCP Authentication"

echo -e "${YELLOW}Verifying GCP authentication...${NC}"
if gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
  ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
  record_test "GCP Authentication" "PASS" "Authenticated as ${ACTIVE_ACCOUNT}"
else
  record_test "GCP Authentication" "FAIL" "No active GCP account found"
fi

###############################################
# STEP 2: Verify Project Organization
###############################################
log_message "${BLUE}" "STEP 2: Verifying Project Organization"

echo -e "${YELLOW}Checking if project is in the correct organization...${NC}"
PROJECT_INFO=$(gcloud projects describe "${GCP_PROJECT_ID}" --format=json 2>/dev/null || echo '{"error":"Failed to get project info"}')

if [[ "$PROJECT_INFO" == *"error"* ]]; then
  record_test "Project Exists" "FAIL" "Could not access project ${GCP_PROJECT_ID}"
else
  record_test "Project Exists" "PASS" "Project ${GCP_PROJECT_ID} exists and is accessible"
  
  # Check if project is in the correct organization
  CURRENT_PARENT=$(echo "${PROJECT_INFO}" | jq -r '.parent.type + "/" + .parent.id')
  
  if [[ "${CURRENT_PARENT}" == "organization/${GCP_ORG_ID}" ]]; then
    record_test "Project Organization" "PASS" "Project is correctly in organization ${GCP_ORG_ID}"
  else
    record_test "Project Organization" "FAIL" "Project is in ${CURRENT_PARENT}, not in organization/${GCP_ORG_ID}"
  fi
fi

###############################################
# STEP 3: Verify Enabled APIs
###############################################
log_message "${BLUE}" "STEP 3: Verifying Required APIs"

# List of required APIs to check
REQUIRED_APIS=(
  "workstations.googleapis.com"
  "compute.googleapis.com"
  "aiplatform.googleapis.com"
  "storage.googleapis.com"
  "redis.googleapis.com"
  "alloydb.googleapis.com"
  "bigquery.googleapis.com"
  "monitoring.googleapis.com"
)

echo -e "${YELLOW}Checking if required APIs are enabled...${NC}"
ENABLED_APIS=$(gcloud services list --project=${GCP_PROJECT_ID} --format="value(config.name)" 2>/dev/null || echo "Failed to list APIs")

if [[ "$ENABLED_APIS" == "Failed to list APIs" ]]; then
  record_test "API Listing" "FAIL" "Could not list enabled APIs"
else
  for api in "${REQUIRED_APIS[@]}"; do
    if echo "${ENABLED_APIS}" | grep -q "${api}"; then
      record_test "API: ${api}" "PASS" "API is enabled"
    else
      record_test "API: ${api}" "FAIL" "API is not enabled"
    fi
  done
fi

###############################################
# STEP 4: Verify Cloud Workstation Setup
###############################################
log_message "${BLUE}" "STEP 4: Verifying Cloud Workstation Setup"

echo -e "${YELLOW}Checking Cloud Workstation configuration...${NC}"

# Check if workstation cluster exists
CLUSTER_LIST=$(gcloud workstations clusters list --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "Failed to list clusters")

if [[ "$CLUSTER_LIST" == "Failed to list clusters" ]]; then
  record_test "Workstation Clusters" "FAIL" "Could not list workstation clusters"
else
  if [[ "$CLUSTER_LIST" == *"hybrid-ide-cluster"* ]]; then
    record_test "Workstation Cluster" "PASS" "Hybrid IDE cluster exists"
    
    # Get more details about the cluster
    CLUSTER_INFO=$(gcloud workstations clusters describe hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --format=json 2>/dev/null || echo '{"error":"Failed to get cluster info"}')
    
    if [[ "$CLUSTER_INFO" != *"error"* ]]; then
      CLUSTER_LOCATION=$(echo "${CLUSTER_INFO}" | jq -r '.location')
      record_test "Cluster Location" "PASS" "Cluster is in region: ${CLUSTER_LOCATION}"
    else
      record_test "Cluster Details" "FAIL" "Could not get cluster details"
    fi
    
    # Check workstation configs
    CONFIG_LIST=$(gcloud workstations configs list --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "Failed to list configs")
    
    if [[ "$CONFIG_LIST" != "Failed to list configs" ]]; then
      if [[ "$CONFIG_LIST" == *"hybrid-ide-config"* ]]; then
        record_test "Workstation Configuration" "PASS" "Hybrid IDE configuration exists"
        
        # Get details about the config
        CONFIG_INFO=$(gcloud workstations configs describe hybrid-ide-config-prod --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --format=json 2>/dev/null || echo '{"error":"Failed to get config info"}')
        
        if [[ "$CONFIG_INFO" != *"error"* ]]; then
          # Verify machine type
          MACHINE_TYPE=$(echo "${CONFIG_INFO}" | jq -r '.host.gceInstance.machineType')
          if [[ "${MACHINE_TYPE}" == *"n2d-standard-32"* ]]; then
            record_test "Machine Type" "PASS" "Correct machine type: ${MACHINE_TYPE}"
          else
            record_test "Machine Type" "FAIL" "Incorrect machine type: ${MACHINE_TYPE}"
          fi
          
          # Verify accelerators
          ACCELERATOR_TYPE=$(echo "${CONFIG_INFO}" | jq -r '.host.gceInstance.accelerators[0].type')
          ACCELERATOR_COUNT=$(echo "${CONFIG_INFO}" | jq -r '.host.gceInstance.accelerators[0].count')
          if [[ "${ACCELERATOR_TYPE}" == *"nvidia-tesla-t4"* && "${ACCELERATOR_COUNT}" == "2" ]]; then
            record_test "GPU Configuration" "PASS" "Correct GPU setup: ${ACCELERATOR_COUNT}x ${ACCELERATOR_TYPE}"
          else
            record_test "GPU Configuration" "FAIL" "Incorrect GPU setup: ${ACCELERATOR_COUNT}x ${ACCELERATOR_TYPE}"
          fi
          
          # Verify boot disk size
          BOOT_DISK_SIZE=$(echo "${CONFIG_INFO}" | jq -r '.host.gceInstance.bootDiskSizeGb')
          if [[ "${BOOT_DISK_SIZE}" == "500" ]]; then
            record_test "Boot Disk Size" "PASS" "Correct boot disk size: ${BOOT_DISK_SIZE}GB"
          else
            record_test "Boot Disk Size" "FAIL" "Incorrect boot disk size: ${BOOT_DISK_SIZE}GB"
          fi
        else
          record_test "Config Details" "FAIL" "Could not get configuration details"
        fi
      else
        record_test "Workstation Configuration" "FAIL" "Hybrid IDE configuration does not exist"
      fi
    else
      record_test "Workstation Configurations" "FAIL" "Could not list workstation configurations"
    fi
    
    # Check workstation instances
    WORKSTATION_LIST=$(gcloud workstations list --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "Failed to list workstations")
    
    if [[ "$WORKSTATION_LIST" != "Failed to list workstations" ]]; then
      if [[ "$WORKSTATION_LIST" == *"hybrid-workstation"* ]]; then
        WORKSTATION_COUNT=$(echo "${WORKSTATION_LIST}" | wc -l)
        record_test "Workstation Instances" "PASS" "${WORKSTATION_COUNT} workstation instances exist"
      else
        record_test "Workstation Instances" "FAIL" "No hybrid workstation instances found"
      fi
    else
      record_test "Workstation Listing" "FAIL" "Could not list workstation instances"
    fi
  else
    record_test "Workstation Cluster" "FAIL" "Hybrid IDE cluster does not exist"
  fi
fi

###############################################
# STEP 5: Verify Redis/AlloyDB Setup
###############################################
log_message "${BLUE}" "STEP 5: Verifying Redis/AlloyDB Setup"

echo -e "${YELLOW}Checking Redis instance...${NC}"
REDIS_LIST=$(gcloud redis instances list --region=us-west4 --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "Failed to list Redis instances")

if [[ "$REDIS_LIST" == "Failed to list Redis instances" ]]; then
  record_test "Redis Listing" "FAIL" "Could not list Redis instances"
else
  if [[ "$REDIS_LIST" == *"agent-memory"* ]]; then
    record_test "Redis Instance" "PASS" "Redis instance 'agent-memory' exists"
    
    # Get details about the Redis instance
    REDIS_INFO=$(gcloud redis instances describe agent-memory --region=us-west4 --project=${GCP_PROJECT_ID} --format=json 2>/dev/null || echo '{"error":"Failed to get Redis info"}')
    
    if [[ "$REDIS_INFO" != *"error"* ]]; then
      REDIS_SIZE=$(echo "${REDIS_INFO}" | jq -r '.memorySizeGb')
      REDIS_VERSION=$(echo "${REDIS_INFO}" | jq -r '.redisVersion')
      REDIS_TIER=$(echo "${REDIS_INFO}" | jq -r '.tier')
      
      record_test "Redis Configuration" "PASS" "Size: ${REDIS_SIZE}GB, Version: ${REDIS_VERSION}, Tier: ${REDIS_TIER}"
    else
      record_test "Redis Details" "FAIL" "Could not get Redis instance details"
    fi
  else
    record_test "Redis Instance" "FAIL" "Redis instance 'agent-memory' does not exist"
  fi
fi

echo -e "${YELLOW}Checking AlloyDB instance...${NC}"
ALLOYDB_LIST=$(gcloud alloydb instances list --cluster=agi-baby-cluster --project=${GCP_PROJECT_ID} --format="value(name)" 2>/dev/null || echo "Failed to list AlloyDB instances")

if [[ "$ALLOYDB_LIST" == "Failed to list AlloyDB instances" ]]; then
  record_test "AlloyDB Listing" "FAIL" "Could not list AlloyDB instances"
else
  if [[ "$ALLOYDB_LIST" == *"alloydb-instance"* ]]; then
    record_test "AlloyDB Instance" "PASS" "AlloyDB instance 'alloydb-instance' exists"
    
    # Get details about the AlloyDB instance
    ALLOYDB_INFO=$(gcloud alloydb instances describe alloydb-instance --cluster=agi-baby-cluster --project=${GCP_PROJECT_ID} --format=json 2>/dev/null || echo '{"error":"Failed to get AlloyDB info"}')
    
    if [[ "$ALLOYDB_INFO" != *"error"* ]]; then
      ALLOYDB_TYPE=$(echo "${ALLOYDB_INFO}" | jq -r '.instanceType')
      ALLOYDB_CPU=$(echo "${ALLOYDB_INFO}" | jq -r '.cpuCount')
      ALLOYDB_MACHINE=$(echo "${ALLOYDB_INFO}" | jq -r '.machineConfig')
      
      record_test "AlloyDB Configuration" "PASS" "Type: ${ALLOYDB_TYPE}, CPUs: ${ALLOYDB_CPU}, Machine: ${ALLOYDB_MACHINE}"
    else
      record_test "AlloyDB Details" "FAIL" "Could not get AlloyDB instance details"
    fi
  else
    record_test "AlloyDB Instance" "FAIL" "AlloyDB instance 'alloydb-instance' does not exist"
  fi
fi

###############################################
# STEP 6: Verify Gemini Code Assist Integration
###############################################
log_message "${BLUE}" "STEP 6: Verifying Gemini Code Assist Integration"

echo -e "${YELLOW}Checking Gemini Code Assist setup...${NC}"

# Since we can't directly verify this on the workstation, we can check if the setup script exists
if [ -f "./setup_gemini_code_assist.sh" ]; then
  record_test "Gemini Code Assist Script" "PASS" "Gemini Code Assist setup script exists"
  
  # Check if the script contains the correct configuration
  if grep -q "tool_integrations:" "./setup_gemini_code_assist.sh" && 
     grep -q "vertex_ai:" "./setup_gemini_code_assist.sh" && 
     grep -q "redis:" "./setup_gemini_code_assist.sh" && 
     grep -q "database:" "./setup_gemini_code_assist.sh"; then
    record_test "Gemini Code Assist Config" "PASS" "Gemini Code Assist configuration includes required integrations"
  else
    record_test "Gemini Code Assist Config" "FAIL" "Gemini Code Assist configuration is missing required integrations"
  fi
else
  record_test "Gemini Code Assist Script" "FAIL" "Gemini Code Assist setup script does not exist"
fi

###############################################
# STEP 7: Verify Organization Policies
###############################################
log_message "${BLUE}" "STEP 7: Verifying Critical Organization Policies"

echo -e "${YELLOW}Checking allowed export destinations policy...${NC}"
EXPORT_POLICY=$(gcloud org-policies describe constraints/resourcemanager.allowedExportDestinations \
  --organization="${GCP_ORG_ID}" --format=json 2>/dev/null || echo '{"error":"Failed to get export policy"}')

if [[ "$EXPORT_POLICY" == *"error"* ]]; then
  record_test "Export Policy Check" "FAIL" "Could not retrieve allowed export destinations policy"
else
  record_test "Export Policy Check" "PASS" "Successfully retrieved allowed export destinations policy"
  
  # Log the policy for manual inspection
  echo -e "${YELLOW}Export destinations policy raw data:${NC}"
  gcloud org-policies describe constraints/resourcemanager.allowedExportDestinations \
    --organization="${GCP_ORG_ID}" 
    
  # Check if policy is enforced or has restrictions
  EXPORT_POLICY_ENFORCED=$(echo "${EXPORT_POLICY}" | jq -r '.enforced // false')
  EXPORT_HAS_ALLOWLIST=$(echo "${EXPORT_POLICY}" | jq -r '.listPolicy.allowedValues | length > 0')
  
  if [[ "$EXPORT_POLICY_ENFORCED" == "true" || "$EXPORT_HAS_ALLOWLIST" == "true" ]]; then
    record_test "Export Policy Restrictions" "FAIL" "Restrictive export policy may impact migration"
  else
    record_test "Export Policy Restrictions" "PASS" "No restrictive export policy detected"
  fi
fi

echo -e "${YELLOW}Checking allowed import sources policy...${NC}"
IMPORT_POLICY=$(gcloud org-policies describe constraints/resourcemanager.allowedImportSources \
  --organization="${GCP_ORG_ID}" --format=json 2>/dev/null || echo '{"error":"Failed to get import policy"}')

if [[ "$IMPORT_POLICY" == *"error"* ]]; then
  record_test "Import Policy Check" "FAIL" "Could not retrieve allowed import sources policy"
else
  record_test "Import Policy Check" "PASS" "Successfully retrieved allowed import sources policy"
  
  # Log the policy for manual inspection
  echo -e "${YELLOW}Import sources policy raw data:${NC}"
  gcloud org-policies describe constraints/resourcemanager.allowedImportSources \
    --organization="${GCP_ORG_ID}"
    
  # Check if policy is enforced or has restrictions
  IMPORT_POLICY_ENFORCED=$(echo "${IMPORT_POLICY}" | jq -r '.enforced // false')
  IMPORT_HAS_ALLOWLIST=$(echo "${IMPORT_POLICY}" | jq -r '.listPolicy.allowedValues | length > 0')
  
  if [[ "$IMPORT_POLICY_ENFORCED" == "true" || "$IMPORT_HAS_ALLOWLIST" == "true" ]]; then
    record_test "Import Policy Restrictions" "FAIL" "Restrictive import policy may impact migration"
  else
    record_test "Import Policy Restrictions" "PASS" "No restrictive import policy detected"
  fi
fi

###############################################
# STEP 8: Verify Vertex Agent Permissions
###############################################
log_message "${BLUE}" "STEP 8: Verifying Vertex Agent Service Account Permissions"

echo -e "${YELLOW}Checking vertex-agent service account roles at organization level...${NC}"

# Get organization IAM policy
ORG_IAM_POLICY=$(gcloud organizations get-iam-policy ${GCP_ORG_ID} --format=json 2>/dev/null || echo '{"error":"Failed to get organization IAM policy"}')

if [[ "$ORG_IAM_POLICY" == *"error"* ]]; then
  record_test "Organization IAM Policy" "FAIL" "Could not retrieve organization IAM policy"
else
  record_test "Organization IAM Policy" "PASS" "Successfully retrieved organization IAM policy"
  
  # Check if the vertex-agent service account has the projectMover role
  if echo "${ORG_IAM_POLICY}" | jq -e --arg sa "serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --arg role "roles/resourcemanager.projectMover" '.bindings[] | select(.role == $role) | .members[] | contains($sa)' > /dev/null 2>&1; then
    record_test "Vertex Agent Project Mover Role" "PASS" "Service account has the Project Mover role"
  else
    record_test "Vertex Agent Project Mover Role" "FAIL" "Service account does not have the Project Mover role"
  fi
  
  # Check if the vertex-agent service account has the projectCreator role
  if echo "${ORG_IAM_POLICY}" | jq -e --arg sa "serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --arg role "roles/resourcemanager.projectCreator" '.bindings[] | select(.role == $role) | .members[] | contains($sa)' > /dev/null 2>&1; then
    record_test "Vertex Agent Project Creator Role" "PASS" "Service account has the Project Creator role"
  else
    record_test "Vertex Agent Project Creator Role" "FAIL" "Service account does not have the Project Creator role"
  fi
fi

###############################################
# STEP 9: Verify IAM Permissions
###############################################
log_message "${BLUE}" "STEP 9: Verifying IAM Permissions"

echo -e "${YELLOW}Checking IAM permissions for service account...${NC}"
IAM_POLICY=$(gcloud projects get-iam-policy ${GCP_PROJECT_ID} --format=json 2>/dev/null || echo '{"error":"Failed to get IAM policy"}')

if [[ "$IAM_POLICY" == *"error"* ]]; then
  record_test "IAM Policy" "FAIL" "Could not retrieve IAM policy"
else
  # Check if the service account has the required roles
  REQUIRED_ROLES=(
    "roles/workstations.user"
    "roles/aiplatform.user"
    "roles/storage.objectViewer"
    "roles/compute.viewer"
    "roles/redis.viewer"
    "roles/alloydb.viewer"
  )
  
  for role in "${REQUIRED_ROLES[@]}"; do
    if echo "${IAM_POLICY}" | jq -e --arg sa "serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --arg role "${role}" '.bindings[] | select(.role == $role) | .members[] | contains($sa)' > /dev/null 2>&1; then
      record_test "IAM Role: ${role}" "PASS" "Service account has the required role"
    else
      record_test "IAM Role: ${role}" "FAIL" "Service account does not have the required role"
    fi
  done
fi

###############################################
# STEP 10: Test Connectivity (Optional - if a workstation is running)
###############################################
log_message "${BLUE}" "STEP 10: Testing Workstation Connectivity (Optional)"

echo -e "${YELLOW}Would you like to test connectivity to a running workstation? (y/n)${NC}"
read -r RUN_CONNECTIVITY_TEST

if [[ "${RUN_CONNECTIVITY_TEST}" =~ ^[Yy]$ ]]; then
  echo -e "${YELLOW}Enter the name of the workstation to test:${NC}"
  read -r WORKSTATION_NAME
  
  if [ -z "${WORKSTATION_NAME}" ]; then
    log_message "${YELLOW}" "No workstation name provided, skipping connectivity test"
  else
    echo -e "${YELLOW}Testing connectivity to workstation ${WORKSTATION_NAME}...${NC}"
    if gcloud workstations start ${WORKSTATION_NAME} --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} > /dev/null 2>&1; then
      record_test "Workstation Start" "PASS" "Successfully started workstation ${WORKSTATION_NAME}"
      
      # Test SSH connectivity
      if gcloud workstations ssh ${WORKSTATION_NAME} --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --command="echo 'Connection successful'" > /dev/null 2>&1; then
        record_test "Workstation SSH" "PASS" "Successfully connected to workstation via SSH"
        
        # Test environment setup
        echo -e "${YELLOW}Testing JupyterLab installation...${NC}"
        if gcloud workstations ssh ${WORKSTATION_NAME} --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --command="jupyter --version" > /dev/null 2>&1; then
          record_test "JupyterLab Installation" "PASS" "JupyterLab is installed on the workstation"
        else
          record_test "JupyterLab Installation" "FAIL" "JupyterLab is not installed or not in PATH"
        fi
        
        # Test Gemini Code Assist config
        echo -e "${YELLOW}Testing Gemini Code Assist config...${NC}"
        if gcloud workstations ssh ${WORKSTATION_NAME} --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} --command="cat ~/.gemini-code-assist.yaml" > /dev/null 2>&1; then
          record_test "Gemini Code Assist Config" "PASS" "Gemini Code Assist config is present on the workstation"
        else
          record_test "Gemini Code Assist Config" "FAIL" "Gemini Code Assist config is not present"
        fi
        
        # Stop the workstation
        echo -e "${YELLOW}Stopping workstation ${WORKSTATION_NAME}...${NC}"
        if gcloud workstations stop ${WORKSTATION_NAME} --cluster=hybrid-ide-cluster-prod --project=${GCP_PROJECT_ID} > /dev/null 2>&1; then
          record_test "Workstation Stop" "PASS" "Successfully stopped workstation ${WORKSTATION_NAME}"
        else
          record_test "Workstation Stop" "FAIL" "Failed to stop workstation ${WORKSTATION_NAME}"
        fi
      else
        record_test "Workstation SSH" "FAIL" "Failed to connect to workstation via SSH"
      fi
    else
      record_test "Workstation Start" "FAIL" "Failed to start workstation ${WORKSTATION_NAME}"
    fi
  fi
else
  log_message "${YELLOW}" "Skipping connectivity test"
fi

###############################################
# STEP 11: Summary of Test Results
###############################################
echo
echo -e "${BLUE}========================================================"
echo "Validation Test Summary"
echo -e "========================================================${NC}"
echo

echo -e "${GREEN}Passed Tests: ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed Tests: ${FAILED_TESTS}${NC}"
echo "Total Tests: $((PASSED_TESTS + FAILED_TESTS))"
echo

if [ ${FAILED_TESTS} -eq 0 ]; then
  echo -e "${GREEN}All tests passed! The migration and setup appear to be successful.${NC}"
else
  echo -e "${RED}Some tests failed. Please review the validation log for details:${NC}"
  echo "${VALIDATION_LOG}"
  echo
  echo -e "${YELLOW}Recommendations for failed tests:${NC}"
  echo "1. If organization tests failed: Verify you have organization admin permissions"
  echo "2. If API tests failed: Enable the missing APIs manually"
  echo "3. If workstation tests failed: Check the Terraform logs for errors"
  echo "4. If Redis/AlloyDB tests failed: Verify network configuration and service account permissions"
  echo "5. For connectivity issues: Check firewall rules and VPC configuration"
fi

echo
echo -e "${BLUE}Complete validation results saved to: ${VALIDATION_LOG}${NC}"

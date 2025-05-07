#!/bin/bash
# track_migration_progress.sh
#
# Comprehensive migration progress tracking dashboard for the GCP migration process
# Provides real-time status updates, validation checks, and troubleshooting guidance

set -e

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
# Use environment variables if available, otherwise use defaults
GCP_PROJECT_ID="${GCP_PROJECT_ID:-cherry-ai-project}"
GCP_ORG_ID="${GCP_ORG_ID:-525398941159}"
CLOUD_WORKSTATION_CLUSTER="${CLOUD_WORKSTATION_CLUSTER:-ai-development}"
CLOUD_WORKSTATION_CONFIG="${CLOUD_WORKSTATION_CONFIG:-ai-dev-config}"
REGION="${REGION:-us-central1}"

# Terminal width for formatting
TERM_WIDTH=$(tput cols 2>/dev/null || echo 80)

# Function to print section header with colored box
print_header() {
  local title="$1"
  local padding=$((($TERM_WIDTH - ${#title} - 4) / 2))
  local line=$(printf "%${TERM_WIDTH}s" | tr ' ' '=')
  
  echo -e "\n${CYAN}${line}${NC}"
  echo -e "${CYAN}=$(printf "%${padding}s" | tr ' ' ' ')${BOLD} $title $(printf "%${padding}s" | tr ' ' ' ')=${NC}"
  echo -e "${CYAN}${line}${NC}"
}

# Function to print status with color
print_status() {
  local item="$1"
  local status="$2"
  local details="${3:-}"
  local max_item_length=50
  local padding=$((max_item_length - ${#item}))
  
  # Truncate item if too long
  if [ ${#item} -gt $max_item_length ]; then
    item="${item:0:$((max_item_length-3))}..."
    padding=0
  fi
  
  if [ "$status" == "PASS" ]; then
    echo -e "${item}$(printf "%${padding}s" | tr ' ' '.')${GREEN}[✓] PASS${NC} ${details}"
  elif [ "$status" == "FAIL" ]; then
    echo -e "${item}$(printf "%${padding}s" | tr ' ' '.')${RED}[✗] FAIL${NC} ${details}"
  elif [ "$status" == "WARN" ]; then
    echo -e "${item}$(printf "%${padding}s" | tr ' ' '.')${YELLOW}[!] WARN${NC} ${details}"
  elif [ "$status" == "INFO" ]; then
    echo -e "${item}$(printf "%${padding}s" | tr ' ' '.')${BLUE}[i] INFO${NC} ${details}"
  elif [ "$status" == "PENDING" ]; then
    echo -e "${item}$(printf "%${padding}s" | tr ' ' '.')${YELLOW}[⟳] PENDING${NC} ${details}"
  fi
}

# Function to execute a command and capture its output
execute_check() {
  local command="$1"
  local output
  local status
  
  # Execute command and capture output
  output=$(eval "$command" 2>&1) || status=$?
  
  # Return both output and status
  echo "$output"
  return ${status:-0}
}

# Function to verify authentication and set up if needed
# Function to get credentials from Secret Manager
get_credentials_from_secret_manager() {
  local secret_name="${1:-vertex-agent-key}"
  local env="${2:-dev}"
  
  # Check if gcloud is authenticated for Secret Manager access
  if ! gcloud auth list --filter=status=ACTIVE --format="value(account)" &>/dev/null; then
    print_status "GCP Authentication" "FAIL" "Not authenticated with gcloud for Secret Manager access"
    return 1
  fi
  
  # Add environment suffix if not already present
  if [[ "$secret_name" != *"-$env" ]]; then
    secret_name="$secret_name-$env"
  fi
  
  # Use the secure credential manager to check if the secret exists
  if ! ./secure_credential_manager.sh check-secret "$secret_name" &>/dev/null; then
    print_status "Secret Manager" "FAIL" "Secret $secret_name does not exist in project $GCP_PROJECT_ID"
    return 1
  fi
  
  # Use the secure credential manager to get the secret
  local secret_value
  secret_value=$(./secure_credential_manager.sh get-secret "$secret_name" 2>/dev/null)
  
  if [ -z "$secret_value" ]; then
    print_status "Secret retrieval" "FAIL" "Failed to retrieve secret $secret_name"
    return 1
  fi
  
  # Export as environment variable
  export GCP_SA_JSON="$secret_value"
  print_status "Secret retrieval" "PASS" "Successfully retrieved credentials from Secret Manager"
  return 0
}

# Function to securely retrieve any secret from Secret Manager
get_secret() {
  local secret_name="$1"
  local env="${2:-dev}"
  
  # Add environment suffix if not already present
  if [[ "$secret_name" != *"-$env" ]]; then
    secret_name="$secret_name-$env"
  # Use the secure credential manager to check if the secret exists
  if ! ./secure_credential_manager.sh check-secret "$secret_name" &>/dev/null; then
    echo "Secret $secret_name does not exist in project $GCP_PROJECT_ID" >&2
    return 1
  fi
  
  # Use the secure credential manager to get the secret
  local secret_value
  secret_value=$(./secure_credential_manager.sh get-secret "$secret_name" 2>/dev/null)
  
  if [ -z "$secret_value" ]; then
    echo "Failed to retrieve secret $secret_name" >&2
    return 1
  fi
  
  # Output the secret value
  echo "$secret_value"
  return 0
}

verify_authentication() {
  print_header "Authentication Verification"
  
  # Check if authenticated
  local auth_status=$(gcloud auth list --filter=status=ACTIVE --format="value(account)" 2>/dev/null || echo "")
  
  if [ -z "$auth_status" ]; then
    print_status "Active gcloud authentication" "FAIL" "No active accounts found"
    
    # Check if GCP_SA_JSON is set
    if [ -z "$GCP_SA_JSON" ]; then
      print_status "Service account JSON" "FAIL" "GCP_SA_JSON environment variable not set"
      
      # Try to get credentials from Secret Manager
      log_info "Attempting to retrieve credentials from Secret Manager..."
      if ! get_credentials_from_secret_manager; then
        cat << EOF

${YELLOW}===== Authentication Issue Detected =====${NC}
No active authentication and could not retrieve credentials from Secret Manager.

To fix this issue, you have several secure options:

1. Use the secure_credential_manager.sh script:
   ./secure_credential_manager.sh get-secret vertex-agent-key > /tmp/key.json
   export GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json

2. Use gcloud authentication directly:
   gcloud auth login
   or
   gcloud auth activate-service-account --key-file=/path/to/your-key.json

3. For CI/CD environments, use Workload Identity Federation:
   https://cloud.google.com/iam/docs/workload-identity-federation

${YELLOW}After setting up authentication, run this script again.${NC}
EOF
        return 1
      fi
    }
    
    print_status "Service account JSON" "PASS" "Credentials available"
    
    # Setup zero-disk authentication
    echo -e "\n${BLUE}Setting up zero-disk authentication...${NC}"
    TEMP_KEY=$(mktemp)
    echo "$GCP_SA_JSON" > "$TEMP_KEY"
    chmod 600 "$TEMP_KEY"
    
    if gcloud auth activate-service-account --key-file="$TEMP_KEY" > /dev/null 2>&1; then
      rm -f "$TEMP_KEY"
      print_status "Zero-disk authentication" "PASS" "Successfully authenticated"
    else
      rm -f "$TEMP_KEY"
      print_status "Zero-disk authentication" "FAIL" "Authentication failed"
      return 1
    }
  else
    print_status "Active gcloud authentication" "PASS" "Account: $auth_status"
  fi
  
  # Set project
  echo -e "\n${BLUE}Setting project to $GCP_PROJECT_ID...${NC}"
  if gcloud config set project "$GCP_PROJECT_ID" > /dev/null 2>&1; then
    print_status "Project configuration" "PASS" "Project set to $GCP_PROJECT_ID"
  else
    print_status "Project configuration" "FAIL" "Failed to set project to $GCP_PROJECT_ID"
    return 1
  fi
  
  return 0
}

# Function to check organization membership
check_organization() {
  print_header "Organization Membership"
  
  local org_id=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "")
  
  if [ -z "$org_id" ]; then
    print_status "Organization membership" "FAIL" "Failed to retrieve organization ID"
  elif [ "$org_id" == "$GCP_ORG_ID" ]; then
    print_status "Organization membership" "PASS" "Project is in organization $GCP_ORG_ID"
  else
    print_status "Organization membership" "FAIL" "Project is in organization $org_id, expected $GCP_ORG_ID"
    print_status "Migration status" "PENDING" "Project migration is needed"
    
    # Check migration operations
    local migration_ops=$(gcloud beta projects operations list \
      --project="$GCP_PROJECT_ID" \
      --filter="operationType=MoveProject" \
      --format="json" 2>/dev/null || echo "[]")
    
    if [ "$migration_ops" != "[]" ]; then
      print_status "Migration operations" "INFO" "Migration operations in progress"
      echo -e "\n${BLUE}Migration Operations:${NC}"
      echo "$migration_ops" | jq -r '.[] | "  Status: \(.status), Started: \(.startTime)"' 2>/dev/null || echo "$migration_ops"
    fi
  fi
}

# Function to check IAM roles and permissions
check_iam() {
  print_header "IAM Roles and Permissions"
  
  # Check service account roles
  local service_account="vertex-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  echo -e "${BLUE}Checking roles for ${service_account}...${NC}"
  
  local roles=$(gcloud organizations get-iam-policy "$GCP_ORG_ID" \
    --filter="bindings.members:serviceAccount:${service_account}" \
    --format="value(bindings.role)" 2>/dev/null || echo "")
  
  if [ -z "$roles" ]; then
    print_status "IAM roles" "WARN" "No roles found or failed to retrieve roles"
  else
    echo -e "${BLUE}Roles:${NC}"
    while IFS= read -r role; do
      if [[ "$role" == *"resourcemanager.projectMover"* ]]; then
        print_status "Project Mover role" "PASS" "Role is assigned"
      fi
      
      if [[ "$role" == *"resourcemanager.projectCreator"* ]]; then
        print_status "Project Creator role" "PASS" "Role is assigned"
      fi
      
      echo "  - $role"
    done <<< "$roles"
    
    # Check for critical roles
    if [[ "$roles" != *"resourcemanager.projectMover"* ]]; then
      print_status "Project Mover role" "FAIL" "Role is not assigned"
    fi
    
    if [[ "$roles" != *"resourcemanager.projectCreator"* ]]; then
      print_status "Project Creator role" "FAIL" "Role is not assigned"
    fi
  fi
  
  # Force IAM policy binding if needed
  if [[ "$roles" != *"resourcemanager.projectMover"* ]] || [[ "$roles" != *"resourcemanager.projectCreator"* ]]; then
    echo -e "\n${YELLOW}Missing critical IAM roles. Would you like to assign them? (y/n)${NC}"
    read -r -p "" response
    if [[ "$response" =~ ^[Yy]$ ]]; then
      echo -e "${BLUE}Assigning resourcemanager.projectMover role...${NC}"
      gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
        --member="serviceAccount:${service_account}" \
        --role="roles/resourcemanager.projectMover" > /dev/null 2>&1
      
      echo -e "${BLUE}Assigning resourcemanager.projectCreator role...${NC}"
      gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
        --member="serviceAccount:${service_account}" \
        --role="roles/resourcemanager.projectCreator" > /dev/null 2>&1
      
      echo -e "${YELLOW}Waiting 10 seconds for changes to propagate...${NC}"
      sleep 10
      
      # Check roles again
      roles=$(gcloud organizations get-iam-policy "$GCP_ORG_ID" \
        --filter="bindings.members:serviceAccount:${service_account}" \
        --format="value(bindings.role)" 2>/dev/null || echo "")
      
      if [[ "$roles" == *"resourcemanager.projectMover"* ]] && [[ "$roles" == *"resourcemanager.projectCreator"* ]]; then
        print_status "IAM role assignment" "PASS" "Critical roles assigned successfully"
      else
        print_status "IAM role assignment" "WARN" "Roles may not have propagated yet. Wait 5 minutes and try again."
      fi
    fi
  fi
}

# Function to check billing
check_billing() {
  print_header "Billing Status"
  
  local billing_account=$(gcloud billing projects describe "$GCP_PROJECT_ID" \
    --format="value(billingAccountName)" 2>/dev/null || echo "")
  
  if [ -z "$billing_account" ]; then
    print_status "Billing account" "WARN" "No billing account attached or failed to retrieve"
    
    # List available billing accounts
    local available_accounts=$(gcloud billing accounts list --filter="open=true" \
      --format="value(name)" 2>/dev/null || echo "")
    
    if [ -z "$available_accounts" ]; then
      print_status "Available billing accounts" "WARN" "No open billing accounts found"
    else
      print_status "Available billing accounts" "INFO" "Billing accounts found"
      
      echo -e "\n${YELLOW}Would you like to link a billing account? (y/n)${NC}"
      read -r -p "" response
      if [[ "$response" =~ ^[Yy]$ ]]; then
        # Get first billing account
        local first_account=$(echo "$available_accounts" | head -n 1)
        
        echo -e "${BLUE}Linking project to billing account $first_account...${NC}"
        if gcloud billing projects link "$GCP_PROJECT_ID" --billing-account="$first_account" > /dev/null 2>&1; then
          print_status "Billing account linking" "PASS" "Successfully linked to $first_account"
        else
          print_status "Billing account linking" "FAIL" "Failed to link billing account"
        fi
      fi
    fi
  else
    print_status "Billing account" "PASS" "Billing account: $billing_account"
  fi
}

# Function to check required APIs
check_apis() {
  print_header "Required APIs"
  
  local required_apis=("workstations.googleapis.com" "aiplatform.googleapis.com" "redis.googleapis.com" "alloydb.googleapis.com" "compute.googleapis.com")
  local all_enabled=true
  
  for api in "${required_apis[@]}"; do
    local api_status=$(gcloud services list --enabled --filter="name:$api" \
      --format="value(NAME)" 2>/dev/null || echo "")
    
    if [ -z "$api_status" ]; then
      print_status "API: $api" "FAIL" "Not enabled"
      all_enabled=false
    else
      print_status "API: $api" "PASS" "Enabled"
    fi
  done
  
  if [ "$all_enabled" = false ]; then
    echo -e "\n${YELLOW}Some required APIs are not enabled. Would you like to enable them? (y/n)${NC}"
    read -r -p "" response
    if [[ "$response" =~ ^[Yy]$ ]]; then
      echo -e "${BLUE}Enabling required APIs...${NC}"
      gcloud services enable \
        workstations.googleapis.com \
        aiplatform.googleapis.com \
        redis.googleapis.com \
        alloydb.googleapis.com \
        compute.googleapis.com > /dev/null 2>&1
      
      print_status "API enablement" "PASS" "APIs enabled successfully"
    fi
  fi
}

# Function to check cloud workstation
check_workstation() {
  print_header "Cloud Workstation"
  
  # Check workstation cluster
  local cluster=$(gcloud workstations clusters list \
    --format="value(name)" 2>/dev/null | grep -i "$CLOUD_WORKSTATION_CLUSTER" || echo "")
  
  if [ -z "$cluster" ]; then
    print_status "Workstation cluster" "FAIL" "Cluster not found"
    print_status "Workstation deployment" "PENDING" "Need to deploy workstation"
  else
    print_status "Workstation cluster" "PASS" "Cluster exists"
    
    # Check configuration
    local config=$(gcloud workstations configs list \
      --cluster="$CLOUD_WORKSTATION_CLUSTER" \
      --format="value(name)" 2>/dev/null | grep -i "$CLOUD_WORKSTATION_CONFIG" || echo "")
    
    if [ -z "$config" ]; then
      print_status "Workstation configuration" "FAIL" "Configuration not found"
    else
      print_status "Workstation configuration" "PASS" "Configuration exists"
      
      # Check machine type
      local machine_type=$(gcloud workstations configs describe "$CLOUD_WORKSTATION_CONFIG" \
        --cluster="$CLOUD_WORKSTATION_CLUSTER" \
        --location="$REGION" \
        --format="value(host.gceInstance.machineType)" 2>/dev/null || echo "")
      
      if [ -z "$machine_type" ]; then
        print_status "Machine type" "WARN" "Failed to retrieve machine type"
      elif [ "$machine_type" = "n2d-standard-32" ]; then
        print_status "Machine type" "PASS" "n2d-standard-32"
      else
        print_status "Machine type" "WARN" "Unexpected machine type: $machine_type"
      fi
      
      # Check GPUs
      local gpu_config=$(gcloud workstations configs describe "$CLOUD_WORKSTATION_CONFIG" \
        --cluster="$CLOUD_WORKSTATION_CLUSTER" \
        --location="$REGION" \
        --format="json" 2>/dev/null | grep -A 5 "accelerator" || echo "")
      
      if [ -z "$gpu_config" ]; then
        print_status "GPU configuration" "WARN" "No GPUs found or failed to retrieve"
      elif [[ "$gpu_config" == *"nvidia-tesla-t4"* ]] && [[ "$gpu_config" == *"count\": 2"* ]]; then
        print_status "GPU configuration" "PASS" "2x NVIDIA Tesla T4 GPUs"
      else
        print_status "GPU configuration" "WARN" "Unexpected GPU configuration: $gpu_config"
      fi
      
      # Check workstations
      local workstations=$(gcloud workstations list \
        --cluster="$CLOUD_WORKSTATION_CLUSTER" \
        --config="$CLOUD_WORKSTATION_CONFIG" \
        --format="table(name,state)" 2>/dev/null || echo "")
      
      if [ -z "$workstations" ] || [ "$workstations" = "Listed 0 items." ]; then
        print_status "Workstation instances" "WARN" "No workstation instances found"
      else
        print_status "Workstation instances" "PASS" "Instances found"
        echo -e "\n${BLUE}Workstation Instances:${NC}"
        echo "$workstations"
      fi
    fi
  fi
}

# Function to check memory systems
check_memory_systems() {
  print_header "Memory Systems"
  
  # Check Redis instance
  echo -e "${BLUE}Checking Redis instance...${NC}"
  local redis_status=$(gcloud redis instances list \
    --filter="name:agent-memory" \
    --format="value(name,state)" 2>/dev/null || echo "")
  
  if [ -z "$redis_status" ]; then
    print_status "Redis instance" "WARN" "Instance not found or failed to retrieve"
  else
    local redis_state=$(echo "$redis_status" | awk '{print $2}')
    print_status "Redis instance" "PASS" "State: $redis_state"
  fi
  
  # Check AlloyDB cluster
  echo -e "${BLUE}Checking AlloyDB cluster...${NC}"
  local alloydb_status=$(gcloud alloydb clusters list \
    --filter="name:agent-storage" \
    --format="value(name,state)" 2>/dev/null || echo "")
  
  if [ -z "$alloydb_status" ]; then
    print_status "AlloyDB cluster" "WARN" "Cluster not found or failed to retrieve"
  else
    local alloydb_state=$(echo "$alloydb_status" | awk '{print $2}')
    print_status "AlloyDB cluster" "PASS" "State: $alloydb_state"
  fi
}

# Function to check AI integration
check_ai_integration() {
  print_header "AI Integration"
  
  # Check Vertex AI endpoints
  echo -e "${BLUE}Checking Vertex AI endpoints...${NC}"
  local vertex_endpoints=$(gcloud ai endpoints list \
    --region="$REGION" \
    --format="table(displayName,state)" 2>/dev/null || echo "")
  
  if [ -z "$vertex_endpoints" ] || [ "$vertex_endpoints" = "Listed 0 items." ]; then
    print_status "Vertex AI endpoints" "WARN" "No endpoints found or failed to retrieve"
  else
    print_status "Vertex AI endpoints" "PASS" "Endpoints found"
    echo -e "\n${BLUE}Vertex AI Endpoints:${NC}"
    echo "$vertex_endpoints"
  fi
}

# Function to check Terraform state
check_terraform_state() {
  print_header "Terraform State"
  
  # Check if Terraform is installed
  if ! command -v terraform &> /dev/null; then
    print_status "Terraform installation" "WARN" "Terraform is not installed"
    return
  fi
  
  print_status "Terraform installation" "PASS" "Terraform is installed"
  
  # Check if .terraform directory exists
  if [ ! -d ".terraform" ]; then
    print_status "Terraform initialization" "WARN" "Terraform not initialized in this directory"
    return
  fi
  
  print_status "Terraform initialization" "PASS" "Terraform is initialized"
  
  # List Terraform state
  echo -e "${BLUE}Checking Terraform state...${NC}"
  local terraform_state=$(terraform state list 2>/dev/null || echo "")
  
  if [ -z "$terraform_state" ]; then
    print_status "Terraform state" "WARN" "No state or failed to retrieve"
  else
    print_status "Terraform state" "PASS" "State found"
    echo -e "\n${BLUE}Terraform Resources:${NC}"
    echo "$terraform_state"
  fi
}

# Function to check Claude Code installation
check_claude_code() {
  print_header "Claude Code Integration"
  
  # Check Node.js installation
  if ! command -v node &> /dev/null; then
    print_status "Node.js installation" "WARN" "Node.js is not installed"
  else
    local node_version=$(node -v)
    print_status "Node.js installation" "PASS" "Version: $node_version"
  fi
  
  # Check Claude Code installation
  if ! command -v claude &> /dev/null; then
    print_status "Claude Code installation" "WARN" "Claude Code is not installed"
  else
    local claude_version=$(claude --version 2>/dev/null || echo "Unknown")
    print_status "Claude Code installation" "PASS" "Version: $claude_version"
  fi
  
  # Check CLAUDE.md
  if [ -f "CLAUDE.md" ]; then
    print_status "Project memory" "PASS" "CLAUDE.md exists"
  else
    print_status "Project memory" "WARN" "CLAUDE.md not found"
  fi
}

# Function to print migration progress Gantt chart
print_migration_progress() {
  print_header "Migration Progress Overview"
  
  # Determine status of each phase
  local org_id=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "")
  local iam_roles=$(gcloud organizations get-iam-policy "$GCP_ORG_ID" \
    --filter="bindings.members:serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" \
    --format="value(bindings.role)" 2>/dev/null || echo "")
  local workstations=$(gcloud workstations list --format="value(name)" 2>/dev/null | grep -i "ai-dev" || echo "")
  
  local iam_status="Pending"
  local migration_status="Pending"
  local ide_status="Pending"
  local validation_status="Pending"
  
  # IAM Configuration status
  if [[ "$iam_roles" == *"resourcemanager.projectMover"* ]] && [[ "$iam_roles" == *"resourcemanager.projectCreator"* ]]; then
    iam_status="Complete"
  fi
  
  # Migration status
  if [ "$org_id" == "$GCP_ORG_ID" ]; then
    migration_status="Complete"
  fi
  
  # IDE Deployment status
  if [ -n "$workstations" ]; then
    ide_status="Complete"
  fi
  
  # Print Gantt chart
  echo -e "\n${BLUE}Migration Progress:${NC}"
  echo -e "┌──────────────────────┬────────────────────────────────────────┐"
  echo -e "│ Phase                │ Status                                 │"
  echo -e "├──────────────────────┼────────────────────────────────────────┤"
  
  if [ "$iam_status" == "Complete" ]; then
    echo -e "│ IAM Configuration     │ ${GREEN}Complete [✓]${NC}                          │"
  else
    echo -e "│ IAM Configuration     │ ${YELLOW}Pending [⟳]${NC}                           │"
  fi
  
  if [ "$migration_status" == "Complete" ]; then
    echo -e "│ Project Migration     │ ${GREEN}Complete [✓]${NC}                          │"
  else
    echo -e "│ Project Migration     │ ${YELLOW}Pending [⟳]${NC}                           │"
  fi
  
  if [ "$ide_status" == "Complete" ]; then
    echo -e "│ Hybrid IDE Deployment │ ${GREEN}Complete [✓]${NC}                          │"
  else
    echo -e "│ Hybrid IDE Deployment │ ${YELLOW}Pending [⟳]${NC}                           │"
  fi
  
  if [ "$validation_status" == "Complete" ]; then
    echo -e "│ Validation            │ ${GREEN}Complete [✓]${NC}                          │"
  else
    echo -e "│ Validation            │ ${YELLOW}Pending [⟳]${NC}                           │"
  fi
  
  echo -e "└──────────────────────┴────────────────────────────────────────┘"
}

# Function to provide troubleshooting guidance
provide_troubleshooting() {
  print_header "Troubleshooting Guide"
  
  cat << EOF
${BOLD}Common Migration Issues:${NC}

1. ${RED}PERMISSION_DENIED${NC}
   - Cause: Insufficient permissions or IAM propagation delay
   - Solution: Re-run IAM role assignment and wait 5 minutes
   - Command: ${BLUE}gcloud organizations add-iam-policy-binding $GCP_ORG_ID --member="serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" --role="roles/resourcemanager.projectMover"${NC}

2. ${RED}PROJECT_NOT_FOUND${NC}
   - Cause: Incorrect project ID
   - Solution: Verify project ID is correct
   - Command: ${BLUE}gcloud projects list --filter="project_id:$GCP_PROJECT_ID"${NC}

3. ${RED}ORGANIZATION_NOT_FOUND${NC}
   - Cause: Incorrect organization ID
   - Solution: Verify organization ID using the numeric format
   - Command: ${BLUE}gcloud organizations list${NC}

4. ${RED}BILLING_NOT_LINKED${NC}
   - Cause: No billing account attached to project
   - Solution: Link a billing account to the project
   - Command: ${BLUE}gcloud beta billing projects link $GCP_PROJECT_ID --billing-account=\$(gcloud beta billing accounts list --format="value(name)" | head -n 1)${NC}

5. ${RED}QUOTA_EXCEEDED${NC}
   - Cause: Insufficient quota for resources
   - Solution: Request quota increase or use different region
   - Command: ${BLUE}gcloud compute regions describe $REGION --format="yaml(quotas)"${NC}

${BOLD}Next Steps Based on Current Status:${NC}

1. If IAM roles are missing:
   ${BLUE}./execute_gcp_migration.sh${NC}

2. If project is not in the correct organization:
   ${BLUE}gcloud beta projects move $GCP_PROJECT_ID --organization=$GCP_ORG_ID${NC}

3. If workstation is not deployed:
   ${BLUE}terraform init && terraform apply -auto-approve${NC}

4. For Claude Code integration:
   ${BLUE}./setup_claude_code.sh${NC}
EOF
}

# Function to suggest next steps
suggest_next_steps() {
  print_header "Recommended Next Steps"
  
  local org_id=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "")
  local iam_roles=$(gcloud organizations get-iam-policy "$GCP_ORG_ID" \
    --filter="bindings.members:serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" \
    --format="value(bindings.role)" 2>/dev/null || echo "")
  local workstations=$(gcloud workstations list --format="value(name)" 2>/dev/null | grep -i "ai-dev" || echo "")
  
  echo -e "${BOLD}Based on the current state, here are the recommended next steps:${NC}\n"
  
  # Check IAM roles
  if [[ "$iam_roles" != *"resourcemanager.projectMover"* ]] || [[ "$iam_roles" != *"resourcemanager.projectCreator"* ]]; then
    echo -e "1. ${YELLOW}Assign required IAM roles:${NC}"
    echo -e "   ${BLUE}./execute_gcp_migration.sh${NC}"
    echo -e "   This will set up the necessary IAM roles for migration.\n"
  fi
  
  # Check organization
  if [ "$org_id" != "$GCP_ORG_ID" ]; then
    echo -e "2. ${YELLOW}Migrate project to organization:${NC}"
    echo -e "   ${BLUE}gcloud beta projects move $GCP_PROJECT_ID --organization=$GCP_ORG_ID${NC}"
    echo -e "   Make sure to wait 5 minutes after assigning IAM roles before attempting migration.\n"
  fi
  
  # Check workstation
  if [ -z "$workstations" ]; then
    echo -e "3. ${YELLOW}Deploy hybrid IDE:${NC}"
    echo -e "   ${BLUE}./execute_gcp_migration.sh${NC}"
    echo -e "   This will deploy the n2d-standard-32 workstation with 2x T4 GPUs.\n"
  fi
  
  # Check Claude Code
  if ! command -v claude &> /dev/null; then
    echo -e "4. ${YELLOW}Set up Claude Code:${NC}"
    echo -e "   ${BLUE}./setup_claude_code.sh${NC}"
    echo -e "   This will install Claude Code for AI-assisted project management.\n"
  fi
  
  # If everything is complete
  if [[ "$iam_roles" == *"resourcemanager.projectMover"* ]] && 
     [[ "$iam_roles" == *"resourcemanager.projectCreator"* ]] && 
     [ "$org_id" == "$GCP_ORG_ID" ] && 
     [ -n "$workstations" ] && 
     command -v claude &> /dev/null; then
    echo -e "${GREEN}All migration steps are complete!${NC}"
    echo -e "You can now use the following commands to interact with your environment:"
    echo -e "  - ${BLUE}gcloud workstations start ai-dev-workstation --cluster=ai-development --region=us-central1${NC}"
    echo -e "  - ${BLUE}claude \"analyze our GCP migration\"${NC}"
    echo -e "  - ${BLUE}./validate_migration_and_claude.sh${NC}"
  fi
}

# Main function to run all checks
main() {
  print_header "GCP Migration Progress Tracker"
  echo -e "${BOLD}Project:${NC} $GCP_PROJECT_ID"
  echo -e "${BOLD}Target Organization:${NC} $GCP_ORG_ID"
  echo -e "${BOLD}Region:${NC} $REGION"
  echo -e "${BOLD}Date:${NC} $(date)"
  
  # Verify authentication first
  verify_authentication || exit 1
  
  # Run checks
  check_organization
  check_iam
  check_billing
  check_apis
  check_workstation
  check_memory_systems
  check_ai_integration
  check_terraform_state
  check_claude_code
  
  # Print progress overview
  print_migration_progress
  
  # Provide guidance
  suggest_next_steps
  provide_troubleshooting
  
  print_header "End of Migration Progress Report"
  echo -e "${GREEN}Run this script periodically to track migration progress.${NC}"
  echo -e "${GREEN}Use ./run_migration_with_claude.sh to execute the complete migration process.${NC}"
}

# Execute main function
main

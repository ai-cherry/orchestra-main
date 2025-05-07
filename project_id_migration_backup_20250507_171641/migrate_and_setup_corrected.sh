#!/bin/bash
# migrate_and_setup_corrected.sh
# 
# Corrected migration script with critical fixes:
# - Organization ID correction (numeric without hyphens)
# - Service account permissions for project migration
# - Billing account verification and reassignment
# - Organization policy checks
# - Robust Google Cloud SDK installation

set -e

# -----[ Command Line Arguments ]-----
FORCE_INSTALL=false

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --force-install)
      FORCE_INSTALL=true
      shift
      ;;
    *)
      # Unknown option
      ;;
  esac
done

# -----[ Configuration ]-----
export GCP_PROJECT_ID="agi-baby-cherry"
export GCP_ORG_ID="873291114285"  # Verified numeric ID without hyphens
export ADMIN_EMAIL="scoobyjava@cherry-ai.me"
export WORKSTATION_PASSWORD="Huskers15"

# -----[ Helper Functions ]-----
log_step() {
  echo -e "\n\033[1;32m===== $1 =====\033[0m"
}

log_error() {
  echo -e "\033[1;31mERROR: $1\033[0m"
  exit 1
}

log_warning() {
  echo -e "\033[1;33mWARNING: $1\033[0m"
}

log_info() {
  echo -e "\033[1;34m$1\033[0m"
}

# -----[ Cloud SDK Installation ]-----
install_gcloud() {
  log_step "Installing Google Cloud SDK"
  
  # Clean previous installation files if force-install is specified
  if [ "$FORCE_INSTALL" = true ]; then
    log_info "Cleaning previous installation files..."
    sudo rm -rf /etc/apt/sources.list.d/google-cloud-sdk.list
    sudo rm -f /usr/share/keyrings/cloud.google.gpg
  fi
  
  # Method 1: Official Repository (Debian 12)
  log_info "Trying installation via official repository..."
  if ! sudo apt-get install -y google-cloud-cli; then
    log_warning "Repository install failed, trying manual install..."
    
    # Method 2: Manual Tarball Installation
    log_info "Installing via manual tarball method..."
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-454.0.0-linux-x86_64.tar.gz
    tar -xf google-cloud-cli-*.tar.gz -C $HOME
    $HOME/google-cloud-sdk/install.sh --quiet --usage-reporting false
    export PATH=$PATH:$HOME/google-cloud-sdk/bin
    rm google-cloud-cli-*.tar.gz
    
    # Add to PATH for current session
    log_info "Adding gcloud to PATH..."
    export PATH=$PATH:$HOME/google-cloud-sdk/bin
    
    # Add to .bashrc for persistence
    if ! grep -q "google-cloud-sdk/bin" ~/.bashrc; then
      echo 'export PATH=$PATH:$HOME/google-cloud-sdk/bin' >> ~/.bashrc
    fi
  fi
  
  # Verify installation
  if ! command -v gcloud &> /dev/null; then
    log_error "❌ Critical Error: Cloud SDK installation failed"
    exit 1
  fi
  
  log_info "✅ Google Cloud SDK installed successfully"
}

# -----[ Prerequisite Checks ]-----
check_prerequisites() {
  log_step "Checking prerequisites"
  
  # Check for required tools
  command -v gcloud >/dev/null 2>&1 || { 
    log_info "gcloud not found. Installing..."
    install_gcloud
  }
  
  command -v terraform >/dev/null 2>&1 || { 
    log_info "terraform not found. Installing..."
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    sudo apt-get update && sudo apt-get install -y terraform || {
      log_error "Failed to install Terraform"
    }
  }
  
  command -v jq >/dev/null 2>&1 || { 
    log_info "jq not found. Installing..."
    sudo apt-get update && sudo apt-get install -y jq || {
      log_error "Failed to install jq"
    }
  }
  
  log_info "All required tools are installed"
}

# -----[ Authentication ]-----
authenticate_gcp() {
  log_step "Authenticating with GCP"
  
  # Check if GCP_SA_JSON environment variable is set
  if [ -z "$GCP_SA_JSON" ]; then
    log_warning "GCP_SA_JSON environment variable is not set."
    log_info "You can set it with: export GCP_SA_JSON='{...}'"
    
    # Check if we have a service account JSON file already
    if [ -f "vertex-agent-service-account.json" ]; then
      log_info "Found vertex-agent-service-account.json file, using it for authentication."
      export GCP_SA_JSON=$(cat vertex-agent-service-account.json)
    else
      log_error "No service account credentials found. Please set GCP_SA_JSON environment variable."
    fi
  fi
  
  # Create temporary key file
  TEMP_KEY_FILE=$(mktemp)
  log_info "Creating temporary key file: $TEMP_KEY_FILE"
  echo "$GCP_SA_JSON" > "$TEMP_KEY_FILE"
  chmod 600 "$TEMP_KEY_FILE"
  
  # Authenticate with service account
  log_info "Authenticating with service account..."
  if ! gcloud auth activate-service-account --key-file="$TEMP_KEY_FILE"; then
    log_error "Authentication failed"
    rm -f "$TEMP_KEY_FILE"
    exit 1
  fi
  
  # Cleanup temporary key file
  rm -f "$TEMP_KEY_FILE"
  log_info "Temporary key file removed"
  
  # Set project
  log_info "Setting project to $GCP_PROJECT_ID..."
  gcloud config set project "$GCP_PROJECT_ID" || {
    log_error "Failed to set project"
  }
  
  log_info "✅ Successfully authenticated with GCP"
  
  # Extract and store service account email for later use
  export SERVICE_ACCOUNT_EMAIL=$(echo "$GCP_SA_JSON" | jq -r '.client_email')
  log_info "Using service account: $SERVICE_ACCOUNT_EMAIL"
}

# -----[ Grant Migration Permissions ]-----
grant_migration_permissions() {
  log_step "Granting migration permissions"
  
  # SERVICE_ACCOUNT_EMAIL was already set in authenticate_gcp()
  if [ -z "$SERVICE_ACCOUNT_EMAIL" ]; then
    log_error "Service account email not found. Authentication may have failed."
  fi
  
  log_info "Granting essential roles to $SERVICE_ACCOUNT_EMAIL..."
  # Grant multiple roles in a single command (more efficient)
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/resourcemanager.projectMover" \
    --quiet || {
    log_warning "Failed to grant Project Mover role. This may already be granted or you may not have permission."
  }
  
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/resourcemanager.projectCreator" \
    --quiet || {
    log_warning "Failed to grant Project Creator role. This may already be granted or you may not have permission."
  }
  
  # This role is essential for organization policy checks
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/orgpolicy.policyViewer" \
    --quiet || {
    log_warning "Failed to grant Policy Viewer role. Organization policy checks may fail."
  }
  
  log_info "Successfully granted migration permissions"
}

# -----[ Grant Vertex Agent Permissions ]-----
grant_vertex_agent_permissions() {
  log_step "Granting essential roles to vertex-agent service account"
  
  VERTEX_AGENT_EMAIL="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
  
  log_info "Granting Project Mover and Project Creator roles to $VERTEX_AGENT_EMAIL..."
  # Grant roles in a single command
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$VERTEX_AGENT_EMAIL" \
    --role="roles/resourcemanager.projectMover" || {
    log_warning "Failed to grant Project Mover role to vertex-agent service account."
  }
  
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$VERTEX_AGENT_EMAIL" \
    --role="roles/resourcemanager.projectCreator" || {
    log_warning "Failed to grant Project Creator role to vertex-agent service account."
  }
  
  log_info "Successfully granted essential roles to vertex-agent service account"
}

# -----[ Check Organization Policies ]-----
check_org_policies() {
  log_step "Checking organization policies (CRITICAL)"
  
  log_info "Checking allowed export destinations..."
  log_info "Running raw command: gcloud org-policies describe constraints/resourcemanager.allowedExportDestinations --organization=$GCP_ORG_ID"
  
  # First run and display the raw command output as requested
  gcloud org-policies describe constraints/resourcemanager.allowedExportDestinations \
    --organization="$GCP_ORG_ID"
  
  # Then get JSON formatted output for processing
  EXPORT_POLICY_OUTPUT=$(gcloud org-policies describe constraints/resourcemanager.allowedExportDestinations \
    --organization="$GCP_ORG_ID" --format=json 2>/dev/null)
  
  # Save the policy output
  if [ $? -eq 0 ]; then
    echo "$EXPORT_POLICY_OUTPUT" > org-policies-export.json
    log_info "Export destinations policy (JSON format):"
    echo "$EXPORT_POLICY_OUTPUT" | jq .
  else
    log_warning "Failed to check export policies. This may be due to permission issues."
    log_warning "Ensure the service account has orgpolicy.policyViewer role."
    log_warning "Migration might fail if restrictive export policies are in place."
    
    # Ask for confirmation to continue
    read -p "Continue despite being unable to verify export policies? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_error "Migration aborted due to inability to verify critical organization policies."
    fi
  fi
  
  log_info "Checking allowed import sources..."
  log_info "Running raw command: gcloud org-policies describe constraints/resourcemanager.allowedImportSources --organization=$GCP_ORG_ID"
  
  # First run and display the raw command output as requested
  gcloud org-policies describe constraints/resourcemanager.allowedImportSources \
    --organization="$GCP_ORG_ID"
  
  # Then get JSON formatted output for processing
  IMPORT_POLICY_OUTPUT=$(gcloud org-policies describe constraints/resourcemanager.allowedImportSources \
    --organization="$GCP_ORG_ID" --format=json 2>/dev/null)
  
  # Save the policy output
  if [ $? -eq 0 ]; then
    echo "$IMPORT_POLICY_OUTPUT" > org-policies-import.json
    log_info "Import sources policy (JSON format):"
    echo "$IMPORT_POLICY_OUTPUT" | jq .
  else
    log_warning "Failed to check import policies. This may be due to permission issues."
    log_warning "Ensure the service account has orgpolicy.policyViewer role."
    log_warning "Migration might fail if restrictive import policies are in place."
    
    # Ask for confirmation to continue
    read -p "Continue despite being unable to verify import policies? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_error "Migration aborted due to inability to verify critical organization policies."
    fi
  fi
  
  # Check for restrictive policies
  if [ -f "org-policies-export.json" ] && [ -f "org-policies-import.json" ]; then
    # Check if policies are enforced
    EXPORT_POLICY_ENFORCED=$(jq -r '.enforced // false' org-policies-export.json 2>/dev/null)
    IMPORT_POLICY_ENFORCED=$(jq -r '.enforced // false' org-policies-import.json 2>/dev/null)
    
    # Check for allow lists (which restrict to specific values)
    EXPORT_HAS_ALLOWLIST=$(jq -r '.listPolicy.allowedValues | length > 0' org-policies-export.json 2>/dev/null)
    IMPORT_HAS_ALLOWLIST=$(jq -r '.listPolicy.allowedValues | length > 0' org-policies-import.json 2>/dev/null)
    
    if [ "$EXPORT_POLICY_ENFORCED" == "true" ] || [ "$IMPORT_POLICY_ENFORCED" == "true" ] || \
       [ "$EXPORT_HAS_ALLOWLIST" == "true" ] || [ "$IMPORT_HAS_ALLOWLIST" == "true" ]; then
      log_warning "CRITICAL: Restrictive organization policies detected that may block migration."
      log_warning "Please review the policy files and ensure the target organization is allowed."
      
      # Ask for confirmation to continue
      read -p "Continue despite potential policy restrictions? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Migration aborted due to restrictive organization policies."
      fi
    else
      log_info "No restrictive organization policies detected"
    fi
  fi
}

# -----[ Project Migration ]-----
migrate_project() {
  log_step "Migrating project to organization"
  
  # Verify current project parent
  log_info "Checking current project parent..."
  CURRENT_PARENT=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null)
  log_info "Current project parent: $CURRENT_PARENT"
  
  # Check if project is already in the target organization
  if [ "$CURRENT_PARENT" == "$GCP_ORG_ID" ]; then
    log_info "Project is already in the target organization. Skipping migration."
    return 0
  fi
  
  # Perform migration
  log_info "Moving project to organization $GCP_ORG_ID..."
  gcloud beta projects move "$GCP_PROJECT_ID" --organization="$GCP_ORG_ID" || {
    log_error "Failed to move project to organization"
  }
  
  # Confirm migration
  log_info "Verifying migration..."
  CURRENT_PARENT=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)")
  
  if [ "$CURRENT_PARENT" == "$GCP_ORG_ID" ]; then
    log_info "Migration successful! Project is now in organization $GCP_ORG_ID"
  else
    log_error "Migration failed. Project is still in $CURRENT_PARENT"
  fi
}

# -----[ Verify and Update Billing ]-----
verify_billing() {
  log_step "Verifying billing account"
  
  # Check current billing account
  log_info "Checking current billing account..."
  CURRENT_BILLING=$(gcloud billing projects describe "$GCP_PROJECT_ID" --format="value(billingAccountName)" 2>/dev/null) || {
    log_warning "Failed to get current billing account. Project may not have billing enabled."
  }
  
  log_info "Current billing account: $CURRENT_BILLING"
  
  # If no billing account is attached or user wants to change it
  if [ -z "$CURRENT_BILLING" ] || [ "$1" == "force" ]; then
    log_info "Listing available billing accounts..."
    gcloud beta billing accounts list
    
    log_info "Getting default billing account..."
    BILLING_ACCOUNT=$(gcloud beta billing accounts list --format="value(name)" | head -n 1)
    
    if [ -z "$BILLING_ACCOUNT" ]; then
      log_warning "No billing accounts found. Please enable billing manually."
      return 1
    fi
    
    log_info "Linking project to billing account $BILLING_ACCOUNT..."
    gcloud beta billing projects link "$GCP_PROJECT_ID" --billing-account="$BILLING_ACCOUNT" || {
      log_warning "Failed to link project to billing account"
    }
  else
    log_info "Project already has billing enabled. Skipping billing update."
  fi
}

# -----[ Infrastructure Setup ]-----
setup_infrastructure() {
  log_step "Setting up infrastructure"
  
  # Enable required APIs
  log_info "Enabling required APIs..."
  gcloud services enable \
    workstations.googleapis.com \
    redis.googleapis.com \
    alloydb.googleapis.com \
    aiplatform.googleapis.com \
    compute.googleapis.com \
    cloudresourcemanager.googleapis.com \
    serviceusage.googleapis.com || {
    log_error "Failed to enable required APIs"
  }
  
  # Create Redis instance
  log_info "Creating Redis instance..."
  gcloud redis instances create agent-memory \
    --region=us-central1 \
    --zone=us-central1-a \
    --tier=basic \
    --size=5 \
    --redis-version=redis_6_x || {
    log_warning "Failed to create Redis instance. It might already exist."
  }
  
  # Create AlloyDB cluster
  log_info "Creating AlloyDB cluster..."
  gcloud alloydb clusters create agent-storage \
    --region=us-central1 \
    --password="$WORKSTATION_PASSWORD" \
    --network=default || {
    log_warning "Failed to create AlloyDB cluster. It might already exist."
  }
  
  log_info "Infrastructure setup completed"
}

# Create a temporary file for the code blocks
create_terraform_config() {
  log_info "Creating Terraform configuration..."
  
  cat > hybrid_workstation_config.tf <<'EOF'
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.83.0"
    }
    google-beta = {
      source = "hashicorp/google-beta"
      version = "4.83.0"
    }
  }
}

provider "google" {
  project = "agi-baby-cherry"
  region  = "us-central1"
}

provider "google-beta" {
  project = "agi-baby-cherry"
  region  = "us-central1"
}

resource "google_workstations_workstation_cluster" "ai_cluster" {
  provider               = google-beta
  project                = "agi-baby-cherry"
  workstation_cluster_id = "ai-development"
  network                = "projects/agi-baby-cherry/global/networks/default"
  subnetwork             = "projects/agi-baby-cherry/regions/us-central1/subnetworks/default"
  location               = "us-central1"
}

resource "google_workstations_workstation_config" "ai_config" {
  provider               = google-beta
  workstation_config_id  = "ai-dev-config"
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
  location               = "us-central1"

  host {
    gce_instance {
      machine_type     = "n2d-standard-32"
      accelerator {
        type  = "nvidia-tesla-t4"
        count = 2
      }
      boot_disk_size_gb = 500
      
      # Enable secure boot and integrity monitoring
      shielded_instance_config {
        enable_secure_boot = true
        enable_integrity_monitoring = true
      }
    }
  }

  persistent_directories {
    mount_path = "/home/ai"
    gce_pd {
      size_gb        = 1000
      fs_type        = "ext4"
      disk_type      = "pd-ssd"
      reclaim_policy = "RETAIN"
    }
  }
  
  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest"
    
    # Environment variables for Gemini, Vertex AI, and Redis
    env = {
      "GEMINI_API_KEY"     = "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
      "VERTEX_ENDPOINT"    = "projects/agi-baby-cherry/locations/us-central1/endpoints/agent-core"
      "REDIS_CONNECTION"   = "redis://agent-memory.redis.us-central1.cherry-ai.cloud.goog:6379"
      "ALLOYDB_CONNECTION" = "postgresql://alloydb-user@agent-storage:5432/agi_baby_cherry"
    }
    
    # Custom startup script to install JupyterLab and other tools
    runtimes {
      name  = "install-jupyterlab"
      type  = "SCRIPT"
      content = <<-EOT
        #!/bin/bash
        set -e
        
        # Install JupyterLab and dependencies
        pip install jupyterlab numpy pandas scikit-learn tensorflow
        jupyter serverextension enable --py jupyterlab --sys-prefix
        
        # Create startup script
        cat > ~/start_jupyter.sh << 'JUPYTER_EOF'
#!/bin/bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
JUPYTER_EOF
        chmod +x ~/start_jupyter.sh
        
        # Set up Gemini Code Assist
        mkdir -p ~/.config
        cat > ~/.config/gemini-code-assist.yaml << 'GEMINI_EOF'
project_context:
  - path: /workspaces
    priority: 100
  - path: /home/ai
    priority: 50

tool_integrations:
  vertex_ai:
    endpoint: projects/agi-baby-cherry/locations/us-central1/endpoints/agent-core
    api_version: v1
  redis:
    connection_string: redis://agent-memory.redis.us-central1.cherry-ai.cloud.goog:6379
  database:
    connection_string: postgresql://alloydb-user@agent-storage:5432/agi_baby_cherry

model:
  name: gemini-2.5
  temperature: 0.3
  max_output_tokens: 8192
  top_p: 0.95
GEMINI_EOF
      EOT
    }
  }
}

resource "google_workstations_workstation" "ai_workstations" {
  provider               = google-beta
  count                  = 3
  workstation_id         = "ai-dev-workstation-${count.index + 1}"
  workstation_config_id  = google_workstations_workstation_config.ai_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
  location               = "us-central1"
}

output "workstation_urls" {
  value = [
    for ws in google_workstations_workstation.ai_workstations : 
    "https://us-central1.workstations.cloud.goog/agi-baby-cherry/us-central1/${ws.workstation_cluster_id}/${ws.workstation_config_id}/${ws.workstation_id}"
  ]
}
EOF

  # Replace placeholders with actual values
  sed -i "s/agi-baby-cherry/$GCP_PROJECT_ID/g" hybrid_workstation_config.tf
}

# -----[ Hybrid IDE Deployment ]-----
deploy_workstations() {
  log_step "Deploying Cloud Workstations"
  
  # Create Terraform configuration with proper escaping
  create_terraform_config
  
  # Initialize Terraform
  log_info "Initializing Terraform..."
  terraform init || {
    log_error "Failed to initialize Terraform"
  }
  
  # Apply Terraform configuration
  log_info "Applying Terraform configuration..."
  terraform apply -auto-approve || {
    log_error "Failed to apply Terraform configuration"
  }
  
  log_info "Cloud Workstations deployed successfully"
}

# -----[ Final Validation ]-----
final_validation() {
  log_step "Performing final validation"
  
  # Check project organization
  CURRENT_ORG=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)")
  log_info "Project organization: $CURRENT_ORG (Expected: $GCP_ORG_ID)"
  
  # Check Redis instance
  log_info "Checking Redis instance..."
  gcloud redis instances describe agent-memory --region=us-central1 --format="json" > redis-info.json 2>/dev/null
  if [ $? -eq 0 ]; then
    REDIS_STATE=$(jq -r '.state' redis-info.json)
    log_info "Redis instance state: $REDIS_STATE"
  else
    log_warning "Failed to check Redis instance"
  fi
  
  # Check AlloyDB cluster
  log_info "Checking AlloyDB cluster..."
  gcloud alloydb clusters describe agent-storage --region=us-central1 --format="json" > alloydb-info.json 2>/dev/null
  if [ $? -eq 0 ]; then
    ALLOYDB_STATE=$(jq -r '.state' alloydb-info.json)
    log_info "AlloyDB cluster state: $ALLOYDB_STATE"
  else
    log_warning "Failed to check AlloyDB cluster"
  fi
  
  # Check Cloud Workstations
  log_info "Checking Cloud Workstations..."
  gcloud workstations clusters list --format="json" > workstation-clusters.json 2>/dev/null
  if [ $? -eq 0 ]; then
    CLUSTER_COUNT=$(jq length workstation-clusters.json)
    log_info "Workstation clusters: $CLUSTER_COUNT"
  else
    log_warning "Failed to check workstation clusters"
  fi
  
  # Run validation script if available
  if [ -f "./validate_migration.sh" ]; then
    log_info "Running validation script..."
    chmod +x ./validate_migration.sh
    ./validate_migration.sh
  else
    log_warning "Validation script not found. Skipping detailed validation."
  fi
  
  log_info "Final validation completed"
}

# -----[ Main Execution ]-----
main() {
  log_step "Starting AGI Baby Cherry migration and setup"
  
  check_prerequisites
  authenticate_gcp
  grant_migration_permissions
  grant_vertex_agent_permissions
  check_org_policies
  migrate_project
  verify_billing
  setup_infrastructure
  deploy_workstations
  final_validation
  
  log_step "Migration and setup complete!"
  log_info "Your Cloud Workstations are ready. Access them through Google Cloud Console:"
  log_info "https://console.cloud.google.com/workstations"
}

# Execute the script
main

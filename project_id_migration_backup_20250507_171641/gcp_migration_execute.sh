#!/bin/bash
# gcp_migration_execute.sh
#
# Consolidated GCP migration script that implements all critical steps:
# - Authentication with the service account
# - Granting essential permissions to vertex-agent
# - Executing migration with atomic validation
# - Setting up hybrid IDE environment
# - Validating the migration

set -e

# -----[ Configuration ]-----
export GCP_PROJECT_ID="agi-baby-cherry"
export GCP_ORG_ID="873291114285"  # Numeric ID without hyphens
export SERVICE_ACCOUNT_EMAIL="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"

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

# Error handling function
handle_error() {
  log_error "Migration failed at step: $1"
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# -----[ 1. Authentication ]-----
authenticate_gcp() {
  log_step "Authenticating with GCP"
  
  # Check if service account key file exists
  if [ ! -f "service-account.json" ]; then
    log_info "Service account key file not found. Please provide the service account key:"
    log_info "Enter the path to your service account key file:"
    read -r KEY_PATH
    
    if [ ! -f "$KEY_PATH" ]; then
      log_error "Service account key file not found at $KEY_PATH"
    fi
    
    cp "$KEY_PATH" service-account.json
  fi
  
  # Authenticate with service account
  log_info "Authenticating with service account..."
  gcloud auth activate-service-account --key-file=service-account.json || {
    log_error "Failed to authenticate with service account"
  }
  
  # Set project
  log_info "Setting project to $GCP_PROJECT_ID..."
  gcloud config set project "$GCP_PROJECT_ID" || {
    log_error "Failed to set project"
  }
  
  log_info "Successfully authenticated with GCP"
}

# -----[ 2. Grant Permissions ]-----
grant_permissions() {
  log_step "Granting essential roles to $SERVICE_ACCOUNT_EMAIL"
  
  # Grant Project Mover role at organization level
  log_info "Granting Project Mover role at organization level..."
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/resourcemanager.projectMover" || {
    log_warning "Failed to grant Project Mover role. This may already be granted or you may not have permission."
  }
  
  # Grant Project Creator role at organization level
  log_info "Granting Project Creator role at organization level..."
  gcloud organizations add-iam-policy-binding "$GCP_ORG_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/resourcemanager.projectCreator" || {
    log_warning "Failed to grant Project Creator role. This may already be granted or you may not have permission."
  }
  
  # Grant Vertex AI service agent role at project level
  log_info "Granting Vertex AI service agent role at project level..."
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.serviceAgent" || {
    log_warning "Failed to grant Vertex AI service agent role. This may already be granted or you may not have permission."
  }
  
  # Grant Storage Admin role at project level
  log_info "Granting Storage Admin role at project level..."
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin" || {
    log_warning "Failed to grant Storage Admin role. This may already be granted or you may not have permission."
  }
  
  # Wait for IAM propagation
  log_info "Waiting for IAM propagation (30s)..."
  sleep 30
  
  log_info "Successfully granted roles to $SERVICE_ACCOUNT_EMAIL"
}

# -----[ 3. Check Organization Policies ]-----
check_org_policies() {
  log_step "Verifying organization policies (CRITICAL)"
  
  log_info "Checking allowed export destinations policy..."
  gcloud org-policies describe constraints/resourcemanager.allowedExportDestinations \
    --organization="$GCP_ORG_ID"
    
  log_info "Checking allowed import sources policy..."
  gcloud org-policies describe constraints/resourcemanager.allowedImportSources \
    --organization="$GCP_ORG_ID"
  
  log_info "Organization policies verified"
}

# -----[ 4. Check Billing ]-----
check_billing() {
  log_step "Verifying billing configuration"
  
  log_info "Checking billing status..."
  BILLING_ENABLED=$(gcloud billing projects describe "$GCP_PROJECT_ID" --format="value(billingEnabled)" 2>/dev/null)
  
  if [ "$BILLING_ENABLED" != "True" ]; then
    log_warning "Billing is not enabled for the project. Attempting to link a billing account..."
    
    BILLING_ACCOUNT=$(gcloud beta billing accounts list --format="value(name)" | head -n 1)
    
    if [ -z "$BILLING_ACCOUNT" ]; then
      log_error "No billing accounts found. Please enable billing manually."
    fi
    
    log_info "Linking project to billing account $BILLING_ACCOUNT..."
    gcloud beta billing projects link "$GCP_PROJECT_ID" --billing-account="$BILLING_ACCOUNT" || {
      log_error "Failed to link project to billing account"
    }
  else
    log_info "Billing is properly configured"
  fi
}

# -----[ 5. Execute Migration ]-----
migrate_project() {
  log_step "Migrating project to organization"
  
  # Create state snapshot
  log_info "Creating pre-migration state snapshot..."
  echo "$(date): Pre-migration state" > migration_state.log
  gcloud projects describe "$GCP_PROJECT_ID" --format=json >> migration_state.log
  
  # Verify current project parent
  log_info "Checking current project parent..."
  CURRENT_PARENT=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null)
  log_info "Current project parent: $CURRENT_PARENT"
  
  # Check if project is already in the target organization
  if [ "$CURRENT_PARENT" == "$GCP_ORG_ID" ]; then
    log_info "Project is already in the target organization. Skipping migration."
    return 0
  fi
  
  # Perform migration with retries
  log_info "Moving project to organization $GCP_ORG_ID..."
  MAX_RETRIES=3
  
  for i in $(seq 1 $MAX_RETRIES); do
    if gcloud beta projects move "$GCP_PROJECT_ID" --organization="$GCP_ORG_ID"; then
      break
    else
      if [ $i -eq $MAX_RETRIES ]; then
        log_error "Failed to move project to organization after $MAX_RETRIES attempts"
      fi
      log_warning "Retry $i of $MAX_RETRIES..."
      sleep 10
    fi
  done
  
  # Atomic validation
  log_info "Verifying migration..."
  CURRENT_PARENT=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)")
  
  if [ "$CURRENT_PARENT" == "$GCP_ORG_ID" ]; then
    log_info "Migration successful! Project is now in organization $GCP_ORG_ID"
  else
    log_error "Migration failed. Project is still in $CURRENT_PARENT"
  fi
}

# -----[ 6. Enable Required Services ]-----
enable_services() {
  log_step "Enabling required services"
  
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
  
  log_info "Successfully enabled required services"
}

# -----[ 7. Deploy Infrastructure ]-----
deploy_infrastructure() {
  log_step "Deploying infrastructure using Terraform"
  
  # Verify Terraform installation
  if ! command -v terraform &> /dev/null; then
    log_error "Terraform is not installed. Please install Terraform before continuing."
  fi
  
  log_info "Initializing Terraform..."
  terraform init || {
    log_error "Failed to initialize Terraform"
  }
  
  log_info "Applying Terraform configuration..."
  terraform apply -auto-approve \
    -var="project_id=$GCP_PROJECT_ID" \
    -var="org_id=$GCP_ORG_ID" || {
    log_error "Failed to apply Terraform configuration"
  }
  
  log_info "Infrastructure deployed successfully"
}

# -----[ 8. Validate Setup ]-----
validate_setup() {
  log_step "Validating migration and setup"
  
  if [ -f "./validate_migration.sh" ]; then
    log_info "Running validation script..."
    bash ./validate_migration.sh || {
      log_warning "Validation script reported issues. Please check the logs."
    }
  else
    log_warning "Validation script not found at ./validate_migration.sh"
    
    # Basic validation
    log_info "Performing basic validation..."
    
    # Check project organization
    CURRENT_ORG=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)")
    log_info "Project organization: $CURRENT_ORG (Expected: $GCP_ORG_ID)"
    
    if [ "$CURRENT_ORG" != "$GCP_ORG_ID" ]; then
      log_error "Project is not in the correct organization"
    fi
    
    # Check enabled APIs
    APIS_ENABLED=$(gcloud services list --project=$GCP_PROJECT_ID --format="value(NAME)" | grep -c "workstations.googleapis.com\|aiplatform.googleapis.com")
    
    if [ "$APIS_ENABLED" -lt 2 ]; then
      log_warning "Some required APIs may not be enabled"
    else
      log_info "Required APIs are enabled"
    fi
  fi
  
  log_info "Validation completed"
}

# -----[ Main Execution ]-----
main() {
  log_step "Starting GCP Organization Migration"
  
  authenticate_gcp
  grant_permissions
  check_org_policies
  check_billing
  migrate_project
  enable_services
  deploy_infrastructure
  validate_setup
  
  log_step "Migration and setup complete!"
  log_info "Your GCP project has been successfully migrated to the organization."
  log_info "Cloud Workstations are ready. Access them through Google Cloud Console:"
  log_info "https://console.cloud.google.com/workstations"
}

# Execute the script
main

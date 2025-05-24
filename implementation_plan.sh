#!/bin/bash
# implementation_plan.sh
#
# Implementation script for deploying the secure credential management system
# and syncing credentials between GitHub and Google Cloud environments.

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
GITHUB_ORG="ai-cherry"
GITHUB_REPO="orchestra-main"
ENV="dev"  # Change to "prod" for production deployment

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Functions
log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
  exit 1
}

log_warning() {
  echo -e "${YELLOW}⚠️ $1${NC}"
}

log_info() {
  echo -e "${BLUE}ℹ️ $1${NC}"
}

print_header() {
  echo -e "\n${BLUE}${BOLD}$1${NC}"
  echo -e "${BLUE}${BOLD}$(printf '=%.0s' $(seq 1 ${#1}))${NC}"
}

check_prerequisites() {
  print_header "Checking Prerequisites"

  # Check if gcloud is installed
  if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
  fi
  log_success "gcloud CLI is installed"

  # Check if terraform is installed
  if ! command -v terraform &> /dev/null; then
    log_error "Terraform is not installed. Please install it from https://www.terraform.io/downloads.html"
  fi
  log_success "Terraform is installed"

  # Check if GitHub CLI is installed
  if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI is not installed. Please install it from https://cli.github.com/manual/installation"
  fi
  log_success "GitHub CLI is installed"

  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    log_error "jq is not installed. Please install it using your package manager"
  fi
  log_success "jq is installed"

  # Check if authenticated with gcloud
  if ! gcloud auth list --filter=status=ACTIVE --format="value(account)" &> /dev/null; then
    log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
  fi
  log_success "Authenticated with gcloud"

  # Check if authenticated with GitHub CLI
  if ! gh auth status &> /dev/null; then
    log_error "Not authenticated with GitHub CLI. Please run 'gh auth login'"
  fi
  log_success "Authenticated with GitHub CLI"

  # Check if project exists
  if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
    log_error "Project $PROJECT_ID does not exist or you don't have access to it"
  fi
  log_success "Project $PROJECT_ID exists and is accessible"

  # Check if GitHub repository exists
  if ! gh repo view "$GITHUB_ORG/$GITHUB_REPO" &> /dev/null; then
    log_error "GitHub repository $GITHUB_ORG/$GITHUB_REPO does not exist or you don't have access to it"
  fi
  log_success "GitHub repository $GITHUB_ORG/$GITHUB_REPO exists and is accessible"
}

deploy_terraform_infrastructure() {
  print_header "Deploying Terraform Infrastructure"

  # Create terraform directory if it doesn't exist
  mkdir -p terraform/environments/$ENV

  # Create terraform variables file
  cat > terraform/environments/$ENV/terraform.tfvars << EOF
project_id  = "$PROJECT_ID"
region      = "$REGION"
env         = "$ENV"
github_org  = "$GITHUB_ORG"
github_repo = "$GITHUB_REPO"
EOF

  # Create terraform main file
  cat > terraform/environments/$ENV/main.tf << EOF
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

module "secure_credentials" {
  source      = "../../modules/secure-credentials"
  project_id  = var.project_id
  region      = var.region
  env         = var.env
  github_org  = var.github_org
  github_repo = var.github_repo
}

output "service_account_emails" {
  value = module.secure_credentials.service_account_emails
}

output "workload_identity_provider" {
  value = module.secure_credentials.workload_identity_provider
}

output "secret_names" {
  value = module.secure_credentials.secret_names
}

output "service_account_key_secrets" {
  value = module.secure_credentials.service_account_key_secrets
}
EOF

  # Create terraform variables file
  cat > terraform/environments/$ENV/variables.tf << EOF
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}
EOF

  # Initialize terraform
  log_info "Initializing Terraform..."
  (cd terraform/environments/$ENV && terraform init)

  # Plan terraform
  log_info "Planning Terraform deployment..."
  (cd terraform/environments/$ENV && terraform plan -out=tfplan)

  # Ask for confirmation
  echo -e "\n${YELLOW}Do you want to apply the Terraform plan? (y/n)${NC}"
  read -r -p "" response
  if [[ ! "$response" =~ ^[Yy]$ ]]; then
    log_info "Terraform apply cancelled"
    return
  fi

  # Apply terraform
  log_info "Applying Terraform plan..."
  (cd terraform/environments/$ENV && terraform apply tfplan)

  # Get outputs
  log_info "Getting Terraform outputs..."
  WORKLOAD_IDENTITY_PROVIDER=$(cd terraform/environments/$ENV && terraform output -raw workload_identity_provider)
  SERVICE_ACCOUNT_EMAILS=$(cd terraform/environments/$ENV && terraform output -json service_account_emails)

  # Save outputs to file
  log_info "Saving Terraform outputs to terraform_outputs.json..."
  (cd terraform/environments/$ENV && terraform output -json > terraform_outputs.json)

  log_success "Terraform infrastructure deployed successfully"
}

setup_workload_identity_federation() {
  print_header "Setting Up Workload Identity Federation"

  # Get the GitHub Actions service account email
  GITHUB_ACTIONS_SA=$(echo "$SERVICE_ACCOUNT_EMAILS" | jq -r '."github-actions"')

  if [ -z "$GITHUB_ACTIONS_SA" ]; then
    log_error "GitHub Actions service account email not found in Terraform outputs"
  fi

  log_info "GitHub Actions service account: $GITHUB_ACTIONS_SA"
  log_info "Workload Identity Provider: $WORKLOAD_IDENTITY_PROVIDER"

  # Update GitHub repository settings
  log_info "Updating GitHub repository settings..."

  # Get project number
  PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

  # Set GitHub Actions secrets
  log_info "Setting GitHub Actions secrets..."

  # Set Workload Identity Provider
  gh secret set WORKLOAD_IDENTITY_PROVIDER --repo="$GITHUB_ORG/$GITHUB_REPO" \
    --body="$WORKLOAD_IDENTITY_PROVIDER"

  # Set Service Account Email
  gh secret set SERVICE_ACCOUNT_EMAIL --repo="$GITHUB_ORG/$GITHUB_REPO" \
    --body="$GITHUB_ACTIONS_SA"

  # Set Project ID
  gh secret set GCP_PROJECT_ID --repo="$GITHUB_ORG/$GITHUB_REPO" \
    --body="$PROJECT_ID"

  # Set Project Number
  gh secret set GCP_PROJECT_NUMBER --repo="$GITHUB_ORG/$GITHUB_REPO" \
    --body="$PROJECT_NUMBER"

  # Set Region
  gh secret set GCP_REGION --repo="$GITHUB_ORG/$GITHUB_REPO" \
    --body="$REGION"

  log_success "Workload Identity Federation set up successfully"
}

migrate_existing_credentials() {
  print_header "Migrating Existing Credentials to Secret Manager"

  # Create a temporary directory for credentials
  TEMP_DIR=$(mktemp -d)
  log_info "Created temporary directory: $TEMP_DIR"

  # List existing GitHub secrets
  log_info "Listing existing GitHub secrets..."
  GITHUB_SECRETS=$(gh secret list --repo="$GITHUB_ORG/$GITHUB_REPO" --json name -q '.[].name')

  # Ask which secrets to migrate
  echo -e "\n${YELLOW}GitHub secrets:${NC}"
  echo "$GITHUB_SECRETS"
  echo -e "\n${YELLOW}Enter the names of the secrets to migrate (comma-separated):${NC}"
  read -r -p "" SECRETS_TO_MIGRATE

  # Convert to array
  IFS=',' read -ra SECRET_ARRAY <<< "$SECRETS_TO_MIGRATE"

  # Migrate each secret
  for SECRET_NAME in "${SECRET_ARRAY[@]}"; do
    SECRET_NAME=$(echo "$SECRET_NAME" | xargs)  # Trim whitespace

    log_info "Migrating secret: $SECRET_NAME"

    # Check if secret exists in GitHub
    if ! echo "$GITHUB_SECRETS" | grep -q "$SECRET_NAME"; then
      log_warning "Secret $SECRET_NAME does not exist in GitHub. Skipping."
      continue
    fi

    # Create a temporary file for the secret
    SECRET_FILE="$TEMP_DIR/$SECRET_NAME"

    # Get the secret value from GitHub
    log_warning "GitHub API doesn't allow direct access to secret values."
    echo -e "${YELLOW}Please enter the value for secret $SECRET_NAME:${NC}"
    read -r -s SECRET_VALUE

    # Write the secret value to the temporary file
    echo -n "$SECRET_VALUE" > "$SECRET_FILE"

    # Create the secret in Secret Manager
    log_info "Creating secret in Secret Manager..."
    if ! gcloud secrets create "$SECRET_NAME-$ENV" \
      --data-file="$SECRET_FILE" \
      --project="$PROJECT_ID" 2>/dev/null; then

      log_info "Secret already exists. Adding new version..."
      gcloud secrets versions add "$SECRET_NAME-$ENV" \
        --data-file="$SECRET_FILE" \
        --project="$PROJECT_ID"
    fi

    # Clean up
    rm -f "$SECRET_FILE"

    log_success "Secret $SECRET_NAME migrated successfully"
  done

  # Clean up
  rm -rf "$TEMP_DIR"

  log_success "Credentials migrated successfully"
}

update_application_code() {
  print_header "Updating Application Code"

  # Make scripts executable
  log_info "Making scripts executable..."
  chmod +x secure_credential_manager.sh

  # Create __init__.py files if they don't exist
  log_info "Creating __init__.py files..."
  mkdir -p core/security
  touch core/security/__init__.py
  mkdir -p core/orchestrator/src/api/dependencies
  touch core/orchestrator/src/api/dependencies/__init__.py

  # Update Poetry dependencies
  log_info "Updating Poetry dependencies..."
  if [ -f "pyproject.toml" ]; then
    log_info "Adding google-cloud-secret-manager to dependencies..."
    poetry add google-cloud-secret-manager
  else
    log_warning "pyproject.toml not found. Skipping Poetry dependency update."
  fi

  log_success "Application code updated successfully"
}

sync_github_gcp_secrets() {
  print_header "Syncing GitHub and GCP Secrets"

  # Create a script for syncing secrets
  cat > sync_github_gcp_secrets.sh << 'EOF'
#!/bin/bash
# sync_github_gcp_secrets.sh
#
# Script to sync secrets between GitHub and GCP Secret Manager

set -e

# Configuration
PROJECT_ID="${1:-cherry-ai-project}"
GITHUB_ORG="${2:-ai-cherry}"
GITHUB_REPO="${3:-orchestra-main}"
ENV="${4:-dev}"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() {
  echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
  exit 1
}

# Check prerequisites
if ! command -v gh &> /dev/null; then
  log_error "GitHub CLI is not installed"
fi

if ! command -v gcloud &> /dev/null; then
  log_error "gcloud CLI is not installed"
fi

# Sync GitHub to GCP
sync_github_to_gcp() {
  log_info "Syncing GitHub secrets to GCP Secret Manager..."

  # List GitHub secrets
  GITHUB_SECRETS=$(gh secret list --repo="$GITHUB_ORG/$GITHUB_REPO" --json name -q '.[].name')

  # Ask which secrets to sync
  echo -e "\n${YELLOW}GitHub secrets:${NC}"
  echo "$GITHUB_SECRETS"
  echo -e "\n${YELLOW}Enter the names of the secrets to sync (comma-separated, or 'all' for all):${NC}"
  read -r -p "" SECRETS_TO_SYNC

  if [ "$SECRETS_TO_SYNC" = "all" ]; then
    SECRETS_TO_SYNC=$(echo "$GITHUB_SECRETS" | tr '\n' ',' | sed 's/,$//')
  fi

  # Convert to array
  IFS=',' read -ra SECRET_ARRAY <<< "$SECRETS_TO_SYNC"

  # Create a temporary directory
  TEMP_DIR=$(mktemp -d)

  # Sync each secret
  for SECRET_NAME in "${SECRET_ARRAY[@]}"; do
    SECRET_NAME=$(echo "$SECRET_NAME" | xargs)  # Trim whitespace

    log_info "Syncing secret: $SECRET_NAME"

    # Check if secret exists in GitHub
    if ! echo "$GITHUB_SECRETS" | grep -q "$SECRET_NAME"; then
      log_warning "Secret $SECRET_NAME does not exist in GitHub. Skipping."
      continue
    fi

    # Create a temporary file for the secret
    SECRET_FILE="$TEMP_DIR/$SECRET_NAME"

    # Get the secret value from GitHub
    log_warning "GitHub API doesn't allow direct access to secret values."
    echo -e "${YELLOW}Please enter the value for secret $SECRET_NAME:${NC}"
    read -r -s SECRET_VALUE

    # Write the secret value to the temporary file
    echo -n "$SECRET_VALUE" > "$SECRET_FILE"

    # Create the secret in Secret Manager
    log_info "Creating secret in Secret Manager..."
    if ! gcloud secrets create "$SECRET_NAME-$ENV" \
      --data-file="$SECRET_FILE" \
      --project="$PROJECT_ID" 2>/dev/null; then

      log_info "Secret already exists. Adding new version..."
      gcloud secrets versions add "$SECRET_NAME-$ENV" \
        --data-file="$SECRET_FILE" \
        --project="$PROJECT_ID"
    fi

    # Clean up
    rm -f "$SECRET_FILE"

    log_success "Secret $SECRET_NAME synced to GCP"
  done

  # Clean up
  rm -rf "$TEMP_DIR"
}

# Sync GCP to GitHub
sync_gcp_to_github() {
  log_info "Syncing GCP Secret Manager secrets to GitHub..."

  # List GCP secrets
  GCP_SECRETS=$(gcloud secrets list --project="$PROJECT_ID" --format="value(name)")

  # Filter secrets by environment
  GCP_ENV_SECRETS=$(echo "$GCP_SECRETS" | grep -E ".*-$ENV$" || echo "")

  if [ -z "$GCP_ENV_SECRETS" ]; then
    log_warning "No secrets found for environment $ENV"
    return
  fi

  # Ask which secrets to sync
  echo -e "\n${YELLOW}GCP secrets for environment $ENV:${NC}"
  echo "$GCP_ENV_SECRETS"
  echo -e "\n${YELLOW}Enter the names of the secrets to sync (comma-separated, or 'all' for all):${NC}"
  read -r -p "" SECRETS_TO_SYNC

  if [ "$SECRETS_TO_SYNC" = "all" ]; then
    SECRETS_TO_SYNC=$(echo "$GCP_ENV_SECRETS" | tr '\n' ',' | sed 's/,$//')
  fi

  # Convert to array
  IFS=',' read -ra SECRET_ARRAY <<< "$SECRETS_TO_SYNC"

  # Create a temporary directory
  TEMP_DIR=$(mktemp -d)

  # Sync each secret
  for SECRET_NAME in "${SECRET_ARRAY[@]}"; do
    SECRET_NAME=$(echo "$SECRET_NAME" | xargs)  # Trim whitespace

    log_info "Syncing secret: $SECRET_NAME"

    # Check if secret exists in GCP
    if ! echo "$GCP_ENV_SECRETS" | grep -q "$SECRET_NAME"; then
      log_warning "Secret $SECRET_NAME does not exist in GCP. Skipping."
      continue
    fi

    # Get the GitHub secret name (remove environment suffix)
    GITHUB_SECRET_NAME=$(echo "$SECRET_NAME" | sed "s/-$ENV$//")

    # Get the secret value from GCP
    SECRET_VALUE=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID")

    # Set the secret in GitHub
    echo -n "$SECRET_VALUE" | gh secret set "$GITHUB_SECRET_NAME" --repo="$GITHUB_ORG/$GITHUB_REPO"

    log_success "Secret $SECRET_NAME synced to GitHub as $GITHUB_SECRET_NAME"
  done
}

# Main menu
echo -e "${YELLOW}Select an option:${NC}"
echo "1. Sync GitHub secrets to GCP Secret Manager"
echo "2. Sync GCP Secret Manager secrets to GitHub"
echo "3. Exit"
read -r -p "Option: " OPTION

case $OPTION in
  1)
    sync_github_to_gcp
    ;;
  2)
    sync_gcp_to_github
    ;;
  3)
    exit 0
    ;;
  *)
    log_error "Invalid option"
    ;;
esac

log_success "Sync completed successfully"
EOF

  # Make the script executable
  chmod +x sync_github_gcp_secrets.sh

  log_success "Created sync_github_gcp_secrets.sh script"

  # Run the script
  echo -e "\n${YELLOW}Do you want to run the sync script now? (y/n)${NC}"
  read -r -p "" response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    ./sync_github_gcp_secrets.sh "$PROJECT_ID" "$GITHUB_ORG" "$GITHUB_REPO" "$ENV"
  fi
}

create_cloud_scheduler_job() {
  print_header "Setting Up Automatic Credential Rotation"

  # Check if Cloud Scheduler API is enabled
  log_info "Checking if Cloud Scheduler API is enabled..."
  if ! gcloud services list --enabled --filter="name:cloudscheduler.googleapis.com" --project="$PROJECT_ID" | grep -q "cloudscheduler.googleapis.com"; then
    log_info "Enabling Cloud Scheduler API..."
    gcloud services enable cloudscheduler.googleapis.com --project="$PROJECT_ID"
  fi

  # Create a Cloud Function for rotating credentials
  log_info "Creating Cloud Function for credential rotation..."

  # Create a temporary directory for the Cloud Function
  TEMP_DIR=$(mktemp -d)

  # Create main.py
  cat > "$TEMP_DIR/main.py" << 'EOF'
import os
import json
import base64
import functions_framework
from google.cloud import secretmanager
from google.cloud import iam_v1

PROJECT_ID = os.environ.get('PROJECT_ID', 'cherry-ai-project')
ENV = os.environ.get('ENV', 'dev')

def rotate_service_account_key(service_account_email):
    """Rotate a service account key and store it in Secret Manager."""
    # Create IAM client
    iam_client = iam_v1.IAMCredentialsClient()

    # Create Secret Manager client
    secret_client = secretmanager.SecretManagerServiceClient()

    # Create a new key
    service_account_name = f"projects/{PROJECT_ID}/serviceAccounts/{service_account_email}"
    key_client = iam_v1.ServiceAccountsClient()
    key = key_client.create_key(request={"name": service_account_name})

    # Get the private key data
    private_key_data = json.loads(base64.b64decode(key.private_key_data).decode('utf-8'))

    # Store the key in Secret Manager
    sa_name = service_account_email.split('@')[0]
    secret_name = f"{sa_name}-key-{ENV}"

    # Check if secret exists
    secret_path = f"projects/{PROJECT_ID}/secrets/{secret_name}"
    try:
        secret_client.get_secret(request={"name": secret_path})
    except Exception:
        # Create the secret
        secret_client.create_secret(
            request={
                "parent": f"projects/{PROJECT_ID}",
                "secret_id": secret_name,
                "secret": {"replication": {"automatic": {}}},
            }
        )

    # Add the new version
    secret_client.add_secret_version(
        request={
            "parent": secret_path,
            "payload": {"data": json.dumps(private_key_data).encode('utf-8')},
        }
    )

    # List existing keys
    keys = key_client.list_service_account_keys(request={"name": service_account_name})

    # Delete old keys (except the one we just created)
    for old_key in keys.keys:
        if old_key.name != key.name and "user_managed" in old_key.name:
            key_client.delete_service_account_key(request={"name": old_key.name})

    return f"Rotated key for {service_account_email}"

@functions_framework.cloud_event
def rotate_credentials(cloud_event):
    """Cloud Function to rotate service account keys."""
    # Parse the Pub/Sub message
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    data = json.loads(pubsub_message)

    # Get the service account email
    service_account_email = data.get("service_account_email")

    if not service_account_email:
        raise ValueError("No service account email provided")

    # Rotate the key
    result = rotate_service_account_key(service_account_email)

    return result
EOF

  # Create requirements.txt
  cat > "$TEMP_DIR/requirements.txt" << 'EOF'
functions-framework==3.0.0
google-cloud-secret-manager==2.12.0
google-cloud-iam==2.9.0
EOF

  # Deploy the Cloud Function
  log_info "Deploying Cloud Function..."
  gcloud functions deploy rotate-credentials \
    --gen2 \
    --runtime=python39 \
    --region="$REGION" \
    --source="$TEMP_DIR" \
    --entry-point=rotate_credentials \
    --trigger-topic=credential-rotation \
    --set-env-vars=PROJECT_ID="$PROJECT_ID",ENV="$ENV" \
    --project="$PROJECT_ID"

  # Create a Pub/Sub topic
  log_info "Creating Pub/Sub topic..."
  gcloud pubsub topics create credential-rotation --project="$PROJECT_ID" || true

  # Create a Cloud Scheduler job
  log_info "Creating Cloud Scheduler job..."

  # Get service account emails from Terraform output
  SERVICE_ACCOUNT_EMAILS=$(cd terraform/environments/$ENV && terraform output -json service_account_emails)

  # Create a job for each service account
  for SA_NAME in $(echo "$SERVICE_ACCOUNT_EMAILS" | jq -r 'keys[]'); do
    if [ "$SA_NAME" != "github-actions" ]; then  # Skip GitHub Actions SA (uses WIF)
      SA_EMAIL=$(echo "$SERVICE_ACCOUNT_EMAILS" | jq -r ".[\"$SA_NAME\"]")

      # Create the job
      JOB_NAME="rotate-$SA_NAME-key"
      MESSAGE=$(echo "{\"service_account_email\":\"$SA_EMAIL\"}" | base64)

      gcloud scheduler jobs create pubsub "$JOB_NAME" \
        --schedule="0 0 1 */3 *" \  # Every 3 months on the 1st at midnight
        --topic=credential-rotation \
        --message-body="$MESSAGE" \
        --time-zone="UTC" \
        --project="$PROJECT_ID" \
        --location="$REGION" || true

      log_success "Created scheduler job for $SA_NAME"
    fi
  done

  # Clean up
  rm -rf "$TEMP_DIR"

  log_success "Automatic credential rotation set up successfully"
}

main() {
  print_header "AI Orchestra Secure Credential Management Implementation"

  # Check prerequisites
  check_prerequisites

  # Menu
  echo -e "\n${YELLOW}Select an option:${NC}"
  echo "1. Deploy Terraform infrastructure"
  echo "2. Set up Workload Identity Federation"
  echo "3. Migrate existing credentials to Secret Manager"
  echo "4. Update application code"
  echo "5. Sync GitHub and GCP secrets"
  echo "6. Set up automatic credential rotation"
  echo "7. Run all steps"
  echo "8. Exit"
  read -r -p "Option: " OPTION

  case $OPTION in
    1)
      deploy_terraform_infrastructure
      ;;
    2)
      setup_workload_identity_federation
      ;;
    3)
      migrate_existing_credentials
      ;;
    4)
      update_application_code
      ;;
    5)
      sync_github_gcp_secrets
      ;;
    6)
      create_cloud_scheduler_job
      ;;
    7)
      deploy_terraform_infrastructure
      setup_workload_identity_federation
      migrate_existing_credentials
      update_application_code
      sync_github_gcp_secrets
      create_cloud_scheduler_job
      ;;
    8)
      exit 0
      ;;
    *)
      log_error "Invalid option"
      ;;
  esac

  log_success "Implementation completed successfully"

  echo -e "\n${GREEN}${BOLD}Next Steps:${NC}"
  echo "1. Update your application code to use the new credential management system"
  echo "2. Test the credential rotation"
  echo "3. Monitor credential usage in Cloud Logging"
  echo "4. Set up alerts for credential access"
}

# Run the main function
main

#!/bin/bash
# REAL GCP MIGRATION STEPS
# This script contains the ACTUAL commands needed to migrate a GCP project
# to a new organization and set up the hybrid IDE environment.
#
# IMPORTANT: Run each section manually after verifying the previous step was successful

set -e

# Configuration - MODIFY THESE VALUES AS NEEDED
GCP_PROJECT_ID="agi-baby-cherry"
GCP_PROJECT_NUMBER="104944497835"
GCP_ORG_ID="8732-9111-4285"
GOOGLE_API_KEY="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
SERVICE_ACCOUNT_EMAIL="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
ADMIN_EMAIL="scoobyjava@cherry-ai.me"
REGION="us-central1"

echo "###############################################"
echo "# STEP 1: PREREQUISITES CHECK"
echo "###############################################"
echo "# The following tools MUST be installed:"
echo "# - Google Cloud SDK (gcloud)"
echo "# - Terraform"
echo "# - jq"
echo
echo "# Checking for required tools..."
command -v gcloud >/dev/null 2>&1 || { echo "ERROR: Google Cloud SDK (gcloud) is not installed. Install it from https://cloud.google.com/sdk/docs/install"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "ERROR: Terraform is not installed. Install it from https://developer.hashicorp.com/terraform/downloads"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is not installed. Install it using your package manager (apt, yum, etc.)"; exit 1; }

echo "###############################################"
echo "# STEP 2: AUTHENTICATION"
echo "###############################################"
echo "# You MUST authenticate with permissions to:"
echo "# - Access the source project as Owner/Editor"
echo "# - Access the target organization as Admin"
echo
echo "# Run one of these commands:"
echo "gcloud auth login  # Interactive login with a user account that has Organization Admin role"
echo "# OR"
echo "gcloud auth activate-service-account ${SERVICE_ACCOUNT_EMAIL} --key-file=PATH_TO_KEY_FILE"
echo
echo "# Then set the project:"
echo "gcloud config set project ${GCP_PROJECT_ID}"

echo "###############################################"
echo "# STEP 3: ENABLE REQUIRED APIS"
echo "###############################################"
echo "# The following command enables all required APIs:"
echo "gcloud services enable \\"
echo "  cloudresourcemanager.googleapis.com \\"
echo "  iam.googleapis.com \\"
echo "  workstations.googleapis.com \\"
echo "  compute.googleapis.com \\"
echo "  aiplatform.googleapis.com \\"
echo "  storage.googleapis.com \\"
echo "  redis.googleapis.com \\"
echo "  alloydb.googleapis.com \\"
echo "  serviceusage.googleapis.com \\"
echo "  bigquery.googleapis.com \\"
echo "  monitoring.googleapis.com"

echo "###############################################"
echo "# STEP 4: PROJECT MIGRATION"
echo "###############################################"
echo "# First, verify the current project details:"
echo "gcloud projects describe ${GCP_PROJECT_ID} --format=json"
echo
echo "# Then, move the project to the new organization:"
echo "gcloud projects move ${GCP_PROJECT_ID} --organization=${GCP_ORG_ID}"
echo
echo "# After migration, verify the project is in the correct organization:"
echo "gcloud projects describe ${GCP_PROJECT_ID} --format=json | grep -A 2 parent"

echo "###############################################"
echo "# STEP 5: SET UP REDIS/ALLOYDB MEMORY LAYER"
echo "###############################################"
echo "# Create Redis instance:"
echo "gcloud redis instances create agent-memory \\"
echo "  --size=10 \\"
echo "  --region=${REGION} \\"
echo "  --tier=standard \\"
echo "  --redis-version=redis_6_x \\"
echo "  --connect-mode=private-service-access \\"
echo "  --network=default"
echo
echo "# Create AlloyDB cluster:"
echo "gcloud alloydb clusters create agi-baby-cluster \\"
echo "  --password=STRONG_PASSWORD_HERE \\"
echo "  --region=${REGION} \\"
echo "  --network=default"
echo
echo "# Create AlloyDB instance:"
echo "gcloud alloydb instances create alloydb-instance \\"
echo "  --instance-type=PRIMARY \\"
echo "  --cpu-count=8 \\"
echo "  --region=${REGION} \\"
echo "  --cluster=agi-baby-cluster \\"
echo "  --machine-config=n2-standard-8 \\"
echo "  --database=agi_baby_cherry \\"
echo "  --user=alloydb-user"

echo "###############################################"
echo "# STEP 6: DEPLOY CLOUD WORKSTATIONS WITH TERRAFORM"
echo "###############################################"
echo "# First, create terraform.tfvars file with the following content:"
echo "cat > terraform.tfvars << EOF"
echo "project_id = \"${GCP_PROJECT_ID}\""
echo "project_number = \"${GCP_PROJECT_NUMBER}\""
echo "region = \"${REGION}\""
echo "zone = \"${REGION}-a\""
echo "env = \"prod\""
echo "service_account_email = \"${SERVICE_ACCOUNT_EMAIL}\""
echo "admin_email = \"${ADMIN_EMAIL}\""
echo "gemini_api_key = \"${GOOGLE_API_KEY}\""
echo "gcs_bucket = \"gs://${GCP_PROJECT_ID}-bucket/repos\""
echo "EOF"
echo
echo "# Initialize Terraform:"
echo "terraform init"
echo
echo "# Create execution plan:"
echo "terraform plan -var-file=terraform.tfvars"
echo
echo "# Apply the configuration:"
echo "terraform apply -var-file=terraform.tfvars"

echo "###############################################"
echo "# STEP 7: VERIFY MIGRATION SUCCESS"
echo "###############################################"
echo "# Verify project organization:"
echo "gcloud projects describe ${GCP_PROJECT_ID} --format=json | grep -A 2 parent"
echo
echo "# Verify Redis instance:"
echo "gcloud redis instances describe agent-memory --region=${REGION}"
echo
echo "# Verify AlloyDB instance:"
echo "gcloud alloydb instances list --cluster=agi-baby-cluster --region=${REGION}"
echo
echo "# Verify Cloud Workstations:"
echo "gcloud workstations clusters list"
echo "gcloud workstations list"
echo
echo "# Run the validation script (if available):"
echo "./validate_migration.sh"

echo "###############################################"
echo "# TROUBLESHOOTING"
echo "###############################################"
echo "# Common issues and solutions:"
echo
echo "# 1. Permission errors:"
echo "#    - Verify your authenticated account has the required roles"
echo "#    - Check if organizational policies are blocking operations"
echo
echo "# 2. API enablement failures:"
echo "#    - Enable APIs manually through Google Cloud Console"
echo "#    - Check for billing issues if applicable"
echo
echo "# 3. Resource creation failures:"
echo "#    - Check quota limits (especially for GPUs)"
echo "#    - Verify networking configuration for private services"
echo "#    - Check for naming conflicts with existing resources"
echo
echo "# 4. Terraform errors:"
echo "#    - Run terraform validate to check configuration"
echo "#    - Check terraform state for resource conflicts"

echo "###############################################"
echo "# REAL-WORLD REQUIREMENTS CHECKLIST"
echo "###############################################"
echo "□ Account with Organization Admin permissions for target organization"
echo "□ Account with Project Owner permissions for source project"
echo "□ Billing account activated and linked to the project"
echo "□ GPU quota sufficient for workstations in target region"
echo "□ Network configuration with Private Service Access"
echo "□ Security policies and firewall rules configured"
echo "□ IAM permissions for relevant service accounts"
echo "□ APIs enabled in the project"
echo "□ DNS records configured if needed"
echo "□ Backup of project IAM policies before migration"
echo "□ Rollback plan documented in case of issues"

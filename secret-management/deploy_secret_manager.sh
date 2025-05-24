#!/bin/bash
# deploy_secret_manager.sh - Deploy the Unified Secret Management System
#
# This script orchestrates the deployment of all components of the unified secret
# management system:
# - Secret Manager infrastructure with zero-trust IAM conditions
# - Secret rotation via Cloud Scheduler
# - Optional migration of GitHub secrets to GCP Secret Manager
#
# Usage:
#   ./deploy_secret_manager.sh --project-id=my-project [OPTIONS]

set -e  # Exit on error

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
REGION="us-central1"
ZONE="us-central1-a"
ROTATION_SCHEDULE="0 0 1 * *"  # At midnight on 1st of every month
REPLICATION="automatic"
ROTATION_ENABLED=true
SKIP_TERRAFORM=false
MIGRATE_GITHUB=false
GITHUB_REPO=""
GITHUB_ORG=""
LABELS=""
TIME_CONDITION=false
TERRAFORM_DIR="./terraform/deployment"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id=*)
      PROJECT_ID="${1#*=}"
      shift
      ;;
    --environment=*)
      ENVIRONMENT="${1#*=}"
      shift
      ;;
    --region=*)
      REGION="${1#*=}"
      shift
      ;;
    --zone=*)
      ZONE="${1#*=}"
      shift
      ;;
    --rotation-schedule=*)
      ROTATION_SCHEDULE="${1#*=}"
      shift
      ;;
    --replication=*)
      REPLICATION="${1#*=}"
      shift
      ;;
    --disable-rotation)
      ROTATION_ENABLED=false
      shift
      ;;
    --skip-terraform)
      SKIP_TERRAFORM=true
      shift
      ;;
    --migrate-github)
      MIGRATE_GITHUB=true
      shift
      ;;
    --github-repo=*)
      GITHUB_REPO="${1#*=}"
      shift
      ;;
    --github-org=*)
      GITHUB_ORG="${1#*=}"
      shift
      ;;
    --service-accounts=*)
      SERVICE_ACCOUNTS="${1#*=}"
      shift
      ;;
    --labels=*)
      LABELS="${1#*=}"
      shift
      ;;
    --time-condition)
      TIME_CONDITION=true
      shift
      ;;
    --help)
      echo "Usage: $0 --project-id=my-project [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --project-id=ID        GCP Project ID (required)"
      echo "  --environment=ENV      Environment (dev, staging, prod) (default: dev)"
      echo "  --region=REGION        GCP Region (default: us-central1)"
      echo "  --zone=ZONE            GCP Zone (default: us-central1-a)"
      echo "  --rotation-schedule=S  Cron schedule for rotation (default: 0 0 1 * *)"
      echo "  --replication=TYPE     Secret replication (automatic, user-managed) (default: automatic)"
      echo "  --disable-rotation     Disable automated secret rotation"
      echo "  --skip-terraform       Skip Terraform deployment (useful for migration only)"
      echo "  --migrate-github       Migrate GitHub secrets to GCP"
      echo "  --github-repo=REPO     GitHub repository (owner/repo) for migration"
      echo "  --github-org=ORG       GitHub organization for migration"
      echo "  --service-accounts=SAs Comma-separated list of service accounts"
      echo "  --labels=KEY=VAL,K=V   Labels to apply to secrets"
      echo "  --time-condition       Apply time-based IAM conditions"
      echo "  --help                 Show this help"
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [ -z "$PROJECT_ID" ]; then
  echo -e "${RED}Error: --project-id is required${NC}"
  echo "Use --help for usage information"
  exit 1
fi

if [ "$MIGRATE_GITHUB" = true ] && [ -z "$GITHUB_REPO" ] && [ -z "$GITHUB_ORG" ]; then
  echo -e "${RED}Error: --github-repo or --github-org is required with --migrate-github${NC}"
  echo "Use --help for usage information"
  exit 1
fi

# Function to check if a command exists
check_command() {
  if ! command -v $1 &> /dev/null; then
    echo -e "${RED}Error: $1 is not installed${NC}"
    echo "Please install $1 before continuing"
    exit 1
  fi
}

# Check required commands
check_command "gcloud"
check_command "terraform"

if [ "$MIGRATE_GITHUB" = true ]; then
  check_command "python3"
fi

# Set up the Terraform deployment directory
echo -e "${BLUE}Setting up Terraform deployment directory...${NC}"
mkdir -p "$TERRAFORM_DIR"

# Create main.tf
cat > "$TERRAFORM_DIR/main.tf" << EOF
/**
 * Unified Secret Management System - Terraform Configuration
 * Environment: ${ENVIRONMENT}
 */

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Secret Manager Module
module "secret_manager" {
  source = "../modules/secret-manager"

  project_id = var.project_id

  secrets = var.secrets
  labels  = var.labels

  replication_automatic        = var.replication_automatic
  replication_locations        = var.replication_locations
  customer_managed_encryption_key = var.customer_managed_encryption_key

  depends_on = [google_project_service.required_apis]
}

# Secret Rotation Module (conditional)
module "secret_rotation" {
  count  = var.enable_rotation ? 1 : 0
  source = "../modules/secret-rotation"

  project_id       = var.project_id
  region           = var.region
  environment      = var.environment

  rotation_schedule = var.rotation_schedule
  time_zone         = var.time_zone
  secrets_to_rotate = var.secrets_to_rotate

  depends_on = [
    google_project_service.required_apis,
    module.secret_manager
  ]
}
EOF

# Create variables.tf
cat > "$TERRAFORM_DIR/variables.tf" << EOF
/**
 * Variables for the Unified Secret Management System
 */

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "${REGION}"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "${ZONE}"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "${ENVIRONMENT}"
}

variable "secrets" {
  description = "Map of secrets to create with their configurations"
  type = map(object({
    labels          = optional(map(string), {})
    initial_value   = optional(string)
    rotation_period = optional(string)
    expiration      = optional(string)
    access = map(object({
      members = list(string)
      condition = optional(object({
        title       = string
        description = string
        expression  = string
      }))
    }))
  }))
  default = {}
}

variable "labels" {
  description = "A set of key/value label pairs to assign to all secrets"
  type        = map(string)
  default     = {
    managed-by = "terraform"
    env        = "${ENVIRONMENT}"
  }
}

variable "replication_automatic" {
  description = "Use automatic replication"
  type        = bool
  default     = ${REPLICATION == "automatic" ? "true" : "false"}
}

variable "replication_locations" {
  description = "Locations for user-managed replication"
  type        = list(string)
  default     = ["${REGION}"]
}

variable "customer_managed_encryption_key" {
  description = "KMS key for encryption (optional)"
  type        = string
  default     = ""
}

variable "enable_rotation" {
  description = "Enable automated secret rotation"
  type        = bool
  default     = ${ROTATION_ENABLED}
}

variable "rotation_schedule" {
  description = "Cron schedule for rotation"
  type        = string
  default     = "${ROTATION_SCHEDULE}"
}

variable "time_zone" {
  description = "Time zone for rotation schedule"
  type        = string
  default     = "Etc/UTC"
}

variable "secrets_to_rotate" {
  description = "List of secrets to include in rotation"
  type        = list(string)
  default     = []
}
EOF

# Create terraform.tfvars
cat > "$TERRAFORM_DIR/terraform.tfvars" << EOF
project_id = "${PROJECT_ID}"
region     = "${REGION}"
zone       = "${ZONE}"
environment = "${ENVIRONMENT}"

# Add your secrets here
# Example:
# secrets = {
#   "api-key" = {
#     labels = {
#       type = "api-key"
#     }
#     access = {
#       "roles/secretmanager.secretAccessor" = {
#         members = ["serviceAccount:my-sa@${PROJECT_ID}.iam.gserviceaccount.com"]
#       }
#     }
#   }
# }

enable_rotation = ${ROTATION_ENABLED}
rotation_schedule = "${ROTATION_SCHEDULE}"
secrets_to_rotate = []
EOF

# Create outputs.tf
cat > "$TERRAFORM_DIR/outputs.tf" << EOF
/**
 * Outputs for the Unified Secret Management System
 */

output "secret_ids" {
  description = "Map of secret IDs created by this configuration"
  value       = module.secret_manager.secret_ids
}

output "rotation_function_uri" {
  description = "URI of the rotation function (if enabled)"
  value       = var.enable_rotation ? module.secret_rotation[0].function_uri : null
}

output "rotation_schedule" {
  description = "Rotation schedule (if enabled)"
  value       = var.enable_rotation ? module.secret_rotation[0].scheduler_job_schedule : null
}
EOF

echo -e "${GREEN}Terraform configuration created in ${TERRAFORM_DIR}${NC}"

# If not skipping Terraform deployment
if [ "$SKIP_TERRAFORM" = false ]; then
  echo -e "${BLUE}Initializing Terraform...${NC}"
  (cd "$TERRAFORM_DIR" && terraform init)

  echo -e "${BLUE}Planning Terraform deployment...${NC}"
  (cd "$TERRAFORM_DIR" && terraform plan -out=tfplan)

  echo -e "${YELLOW}Ready to apply Terraform configuration.${NC}"
  read -p "Do you want to continue? (y/n): " confirm

  if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    echo -e "${BLUE}Applying Terraform configuration...${NC}"
    (cd "$TERRAFORM_DIR" && terraform apply tfplan)
    echo -e "${GREEN}Secret management infrastructure deployed successfully!${NC}"
  else
    echo -e "${YELLOW}Terraform apply canceled.${NC}"
    echo "You can apply the configuration later with:"
    echo "  cd $TERRAFORM_DIR && terraform apply tfplan"
  fi
fi

# If migrating GitHub secrets
if [ "$MIGRATE_GITHUB" = true ]; then
  echo -e "${BLUE}Migrating GitHub secrets to GCP Secret Manager...${NC}"

  # Build the migration command
  MIGRATE_CMD="python3 ../migrate_github_to_gcp.py --project-id=${PROJECT_ID}"

  if [ ! -z "$GITHUB_REPO" ]; then
    MIGRATE_CMD="$MIGRATE_CMD --repo=${GITHUB_REPO}"
  fi

  if [ ! -z "$GITHUB_ORG" ]; then
    MIGRATE_CMD="$MIGRATE_CMD --org=${GITHUB_ORG}"
  fi

  if [ ! -z "$SERVICE_ACCOUNTS" ]; then
    MIGRATE_CMD="$MIGRATE_CMD --service-accounts=${SERVICE_ACCOUNTS}"
  fi

  if [ ! -z "$LABELS" ]; then
    MIGRATE_CMD="$MIGRATE_CMD --labels=${LABELS}"
  fi

  if [ "$TIME_CONDITION" = true ]; then
    MIGRATE_CMD="$MIGRATE_CMD --time-condition"
  fi

  # Add output CSV report
  MIGRATE_CMD="$MIGRATE_CMD --output-csv=migration_report_${ENVIRONMENT}.csv"

  # Run the migration script
  (cd "$TERRAFORM_DIR" && $MIGRATE_CMD)

  echo -e "${GREEN}GitHub secrets migration completed!${NC}"
  echo -e "${YELLOW}Check migration_report_${ENVIRONMENT}.csv for details.${NC}"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Unified Secret Management System Deployment Complete${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Edit ${TERRAFORM_DIR}/terraform.tfvars to add your secrets"
echo "2. Run 'terraform apply' to create the configured secrets"
echo "3. Update your applications to use the Python client library"
echo "4. Use the Docker integration examples for container builds"
echo ""
echo -e "${YELLOW}Documentation and Examples:${NC}"
echo "- Python Client: ./python/gcp_secret_client/"
echo "- Docker Integration: ./examples/docker-build-integration/"
echo "- GitHub Migration: ./migrate_github_to_gcp.py"
echo ""
echo -e "${BLUE}======================================================${NC}"

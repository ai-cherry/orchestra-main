#!/bin/bash
# Bootstrap AI Orchestra Infrastructure
# This script sets up the necessary GCP infrastructure for the AI Orchestra project

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-west4"}
TERRAFORM_STATE_BUCKET="${PROJECT_ID}-terraform-state"
ENVIRONMENT=${ENVIRONMENT:-"staging"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${RED}Error: You are not logged in to gcloud. Please run 'gcloud auth login' or use a service account key.${NC}"
    exit 1
fi

# Print configuration
echo -e "${BLUE}=== Configuration ===${NC}"
echo -e "Project ID: ${GREEN}${PROJECT_ID}${NC}"
echo -e "Region: ${GREEN}${REGION}${NC}"
echo -e "Terraform State Bucket: ${GREEN}${TERRAFORM_STATE_BUCKET}${NC}"
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo ""

# Confirm with user
read -p "Do you want to proceed with this configuration? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Setup cancelled.${NC}"
    exit 0
fi

# Set the project
echo -e "${BLUE}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${BLUE}Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    redis.googleapis.com \
    cloudtasks.googleapis.com \
    pubsub.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com

# Create Terraform state bucket if it doesn't exist
echo -e "${BLUE}Creating Terraform state bucket...${NC}"
if ! gsutil ls -b gs://${TERRAFORM_STATE_BUCKET} &> /dev/null; then
    gsutil mb -l ${REGION} gs://${TERRAFORM_STATE_BUCKET}
    gsutil versioning set on gs://${TERRAFORM_STATE_BUCKET}
    echo -e "${GREEN}Created Terraform state bucket: ${TERRAFORM_STATE_BUCKET}${NC}"
else
    echo -e "${YELLOW}Terraform state bucket already exists: ${TERRAFORM_STATE_BUCKET}${NC}"
fi

# Create Firestore database if it doesn't exist
echo -e "${BLUE}Creating Firestore database...${NC}"
if ! gcloud firestore databases list --format="value(name)" | grep -q "(default)"; then
    gcloud firestore databases create --location=${REGION}
    echo -e "${GREEN}Created Firestore database${NC}"
else
    echo -e "${YELLOW}Firestore database already exists${NC}"
fi

# Create Redis instance if it doesn't exist
echo -e "${BLUE}Creating Redis instance...${NC}"
REDIS_NAME="orchestra-cache-${ENVIRONMENT}"
if ! gcloud redis instances list --region=${REGION} --format="value(name)" | grep -q ${REDIS_NAME}; then
    gcloud redis instances create ${REDIS_NAME} \
        --region=${REGION} \
        --size=1 \
        --redis-version=redis_6_x
    echo -e "${GREEN}Created Redis instance: ${REDIS_NAME}${NC}"
else
    echo -e "${YELLOW}Redis instance already exists: ${REDIS_NAME}${NC}"
fi

# Create storage bucket for artifacts
echo -e "${BLUE}Creating storage bucket for artifacts...${NC}"
BUCKET_NAME="${PROJECT_ID}-artifacts-${ENVIRONMENT}"
if ! gsutil ls -b gs://${BUCKET_NAME} &> /dev/null; then
    gsutil mb -l ${REGION} gs://${BUCKET_NAME}
    gsutil lifecycle set - gs://${BUCKET_NAME} << EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    }
  ]
}
EOF
    echo -e "${GREEN}Created storage bucket: ${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}Storage bucket already exists: ${BUCKET_NAME}${NC}"
fi

# Create Terraform configuration directory if it doesn't exist
echo -e "${BLUE}Creating Terraform configuration...${NC}"
mkdir -p terraform

# Create Terraform backend configuration
cat > terraform/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket = "${TERRAFORM_STATE_BUCKET}"
    prefix = "terraform/state"
  }
}
EOF

# Create Terraform variables
cat > terraform/variables.tf << EOF
variable "project_id" {
  description = "The GCP project ID."
  type        = string
  default     = "${PROJECT_ID}"
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "${REGION}"
}

variable "environment" {
  description = "Deployment environment (prod or staging)."
  type        = string
  default     = "${ENVIRONMENT}"
}
EOF

# Create Terraform main configuration
cat > terraform/main.tf << EOF
provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Run service
resource "google_cloud_run_v2_service" "orchestra_api" {
  name     = "orchestra-api-\${var.environment}"
  location = var.region
  
  template {
    containers {
      image = "gcr.io/\${var.project_id}/orchestra:\${var.environment}"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.orchestra_cache.host
      }
      
      env {
        name  = "REDIS_PORT"
        value = google_redis_instance.orchestra_cache.port
      }
    }
    
    service_account = google_service_account.orchestra_sa.email
  }
}

# Redis instance
resource "google_redis_instance" "orchestra_cache" {
  name           = "orchestra-cache-\${var.environment}"
  memory_size_gb = 1
  region         = var.region
  redis_version  = "REDIS_6_X"
  
  labels = {
    environment = var.environment
  }
}

# Service account
resource "google_service_account" "orchestra_sa" {
  account_id   = "orchestra-service-account"
  display_name = "Orchestra Service Account"
}

# IAM bindings
resource "google_project_iam_member" "orchestra_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/firestore.user",
    "roles/redis.editor",
    "roles/storage.objectUser",
    "roles/aiplatform.user"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:\${google_service_account.orchestra_sa.email}"
}

# Allow unauthenticated access to Cloud Run
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.orchestra_api.location
  service  = google_cloud_run_v2_service.orchestra_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "cloud_run_url" {
  value = google_cloud_run_v2_service.orchestra_api.uri
}

output "redis_host" {
  value = google_redis_instance.orchestra_cache.host
}

output "redis_port" {
  value = google_redis_instance.orchestra_cache.port
}
EOF

# Initialize Terraform
echo -e "${BLUE}Initializing Terraform...${NC}"
cd terraform
terraform init

# Create Terraform variables file
cat > terraform.tfvars << EOF
project_id = "${PROJECT_ID}"
region = "${REGION}"
environment = "${ENVIRONMENT}"
EOF

# Plan Terraform changes
echo -e "${BLUE}Planning Terraform changes...${NC}"
terraform plan -var-file=terraform.tfvars -out=tfplan

# Ask user if they want to apply the changes
read -p "Do you want to apply these changes? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Terraform apply cancelled.${NC}"
    exit 0
fi

# Apply Terraform changes
echo -e "${BLUE}Applying Terraform changes...${NC}"
terraform apply -auto-approve tfplan

# Print outputs
echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "${GREEN}Cloud Run URL:${NC} $(terraform output -raw cloud_run_url)"
echo -e "${GREEN}Redis Host:${NC} $(terraform output -raw redis_host)"
echo -e "${GREEN}Redis Port:${NC} $(terraform output -raw redis_port)"

echo -e "${GREEN}Infrastructure setup completed successfully!${NC}"
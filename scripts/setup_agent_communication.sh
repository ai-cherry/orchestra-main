#!/bin/bash
# Setup script for AI Orchestra agent communication infrastructure
# This script sets up the necessary GCP resources for agent communication

set -e  # Exit on error

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-west4"}
ENVIRONMENT=${ENVIRONMENT:-"dev"}
SERVICE_ACCOUNT_NAME="orchestra-agent-communication"
TERRAFORM_DIR="terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print section header
section() {
  echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Print success message
success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
error() {
  echo -e "${RED}✗ $1${NC}"
}

# Print warning message
warning() {
  echo -e "${YELLOW}! $1${NC}"
}

# Check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
section "Checking prerequisites"

# Check if gcloud is installed
if ! command_exists gcloud; then
  error "gcloud CLI is not installed. Please install it first."
  exit 1
fi
success "gcloud CLI is installed"

# Check if terraform is installed
if ! command_exists terraform; then
  error "Terraform is not installed. Please install it first."
  exit 1
fi
success "Terraform is installed"

# Check if jq is installed
if ! command_exists jq; then
  error "jq is not installed. Please install it first."
  exit 1
fi
success "jq is installed"

# Check if user is logged in to gcloud
GCLOUD_AUTH=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$GCLOUD_AUTH" ]; then
  error "Not logged in to gcloud. Please run 'gcloud auth login' first."
  exit 1
fi
success "Logged in to gcloud as $GCLOUD_AUTH"

# Check if project exists and user has access
PROJECT_CHECK=$(gcloud projects describe "$PROJECT_ID" --format="value(projectId)" 2>/dev/null || echo "")
if [ -z "$PROJECT_CHECK" ]; then
  error "Project $PROJECT_ID does not exist or you don't have access to it."
  exit 1
fi
success "Project $PROJECT_ID exists and is accessible"

# Set the project
section "Setting project"
gcloud config set project "$PROJECT_ID"
success "Project set to $PROJECT_ID"

# Enable necessary APIs
section "Enabling necessary APIs"
APIS=(
  "cloudresourcemanager.googleapis.com"
  "iam.googleapis.com"
  "secretmanager.googleapis.com"
  "redis.googleapis.com"
  "pubsub.googleapis.com"
  "firestore.googleapis.com"
  "aiplatform.googleapis.com"
  "storage.googleapis.com"
  "monitoring.googleapis.com"
  "logging.googleapis.com"
)

for api in "${APIS[@]}"; do
  echo "Enabling $api..."
  gcloud services enable "$api" --project="$PROJECT_ID"
done
success "All necessary APIs enabled"

# Create service account if it doesn't exist
section "Setting up service account"
SA_EXISTS=$(gcloud iam service-accounts list --project="$PROJECT_ID" --filter="email:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" --format="value(email)" 2>/dev/null || echo "")
if [ -z "$SA_EXISTS" ]; then
  echo "Creating service account..."
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --project="$PROJECT_ID" \
    --display-name="Orchestra Agent Communication Service Account"
  success "Created service account: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
else
  success "Service account already exists: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
fi

# Grant necessary roles to the service account
section "Granting IAM roles"
ROLES=(
  "roles/pubsub.editor"
  "roles/redis.editor"
  "roles/secretmanager.secretAccessor"
  "roles/firestore.user"
)

for role in "${ROLES[@]}"; do
  echo "Granting $role..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role"
done
success "All roles granted"

# Create Terraform backend bucket if it doesn't exist
section "Setting up Terraform backend"
TF_STATE_BUCKET="${PROJECT_ID}-terraform-state"
BUCKET_EXISTS=$(gcloud storage ls --project="$PROJECT_ID" "gs://${TF_STATE_BUCKET}" 2>/dev/null || echo "")
if [ -z "$BUCKET_EXISTS" ]; then
  echo "Creating Terraform state bucket..."
  gcloud storage buckets create "gs://${TF_STATE_BUCKET}" \
    --project="$PROJECT_ID" \
    --location="$REGION" \
    --uniform-bucket-level-access
  success "Created Terraform state bucket: $TF_STATE_BUCKET"
else
  success "Terraform state bucket already exists: $TF_STATE_BUCKET"
fi

# Create backend.tf file
cat > "$TERRAFORM_DIR/backend.tf" <<EOF
terraform {
  backend "gcs" {
    bucket = "${TF_STATE_BUCKET}"
    prefix = "agent-communication"
  }
}
EOF
success "Created backend.tf file"

# Create terraform.tfvars file
section "Creating Terraform variables"
cat > "$TERRAFORM_DIR/terraform.tfvars" <<EOF
project_id = "${PROJECT_ID}"
region     = "${REGION}"
environment = "${ENVIRONMENT}"

# Service account
service_account_email = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Redis configuration
redis_memory_size_gb = 1
redis_tier = "BASIC"

# PubSub configuration
pubsub_topics = {
  "agent-events" = {
    labels = {
      purpose = "agent-communication"
    }
  },
  "agent-tasks" = {
    labels = {
      purpose = "task-distribution"
    }
  },
  "agent-results" = {
    labels = {
      purpose = "task-results"
    }
  },
  "agent-memory" = {
    labels = {
      purpose = "memory-updates"
    }
  },
  "agent-workflow" = {
    labels = {
      purpose = "workflow-state-changes"
    }
  }
}

# Tags
tags = {
  application = "orchestra"
  environment = "${ENVIRONMENT}"
  managed_by  = "terraform"
}
EOF
success "Created terraform.tfvars file"

# Initialize Terraform
section "Initializing Terraform"
cd "$TERRAFORM_DIR"
terraform init
success "Terraform initialized"

# Validate Terraform configuration
section "Validating Terraform configuration"
terraform validate
success "Terraform configuration is valid"

# Plan Terraform changes
section "Planning Terraform changes"
terraform plan -target=module.redis -target=module.pubsub -out=tfplan

# Ask for confirmation before applying
echo -e "\n${YELLOW}Do you want to apply these changes? (y/N)${NC}"
read -r CONFIRM
if [[ $CONFIRM =~ ^[Yy]$ ]]; then
  # Apply Terraform changes
  section "Applying Terraform changes"
  terraform apply tfplan
  success "Terraform changes applied"
  
  # Get outputs
  section "Infrastructure outputs"
  terraform output
else
  warning "Terraform apply cancelled"
fi

# Create Python configuration
section "Creating Python configuration"
CONFIG_DIR="core/orchestrator/src/config"
mkdir -p "$CONFIG_DIR"

# Create or update config.py
cat > "$CONFIG_DIR/config.py" <<EOF
"""
Configuration for AI Orchestra.

This module provides configuration settings for the AI Orchestra system.
"""

import os
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Settings for the AI Orchestra system."""
    
    # Environment
    ENVIRONMENT: str = Field(default="dev")
    
    # GCP settings
    GCP_PROJECT_ID: str = Field(default="${PROJECT_ID}")
    GCP_REGION: str = Field(default="${REGION}")
    
    # Redis settings
    REDIS_HOST: Optional[str] = Field(default=None)
    REDIS_PORT: Optional[int] = Field(default=None)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_TTL: int = Field(default=3600)  # 1 hour
    
    # PubSub settings
    PUBSUB_ENABLED: bool = Field(default=True)
    
    # Agent settings
    AGENT_COMMUNICATION_TIMEOUT: int = Field(default=30)  # 30 seconds
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()
EOF
success "Created/updated config.py"

# Create a sample .env file
cat > ".env.example" <<EOF
# Environment
ENVIRONMENT=dev

# GCP settings
GCP_PROJECT_ID=${PROJECT_ID}
GCP_REGION=${REGION}

# Redis settings (will be populated by Terraform outputs)
REDIS_HOST=
REDIS_PORT=
REDIS_TTL=3600

# PubSub settings
PUBSUB_ENABLED=true

# Agent settings
AGENT_COMMUNICATION_TIMEOUT=30
EOF
success "Created .env.example file"

# Final instructions
section "Next steps"
echo "1. Update your .env file with the Redis host and port from the Terraform outputs"
echo "2. Install the required Python packages:"
echo "   - google-cloud-pubsub"
echo "   - google-cloud-redis"
echo "   - aioredis"
echo "3. Test the agent communication system with the example agents"
echo "4. Integrate the communication system with your existing agents"
echo ""
echo "For more information, see the documentation in docs/agent_communication_guide.md"

success "Setup complete!"
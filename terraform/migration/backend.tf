# backend.tf
# Configures the backend for Terraform state management
# This ensures proper state handling during the migration process

terraform {
  # The actual backend configuration values will be passed via CLI arguments
  # This allows for environment-specific configuration without modifying this file
  backend "gcs" {
    # Values provided via -backend-config CLI arguments:
    # bucket        - GCS bucket for state storage
    # prefix        - Path within the bucket for state file
    # encryption_key - Customer-managed encryption key (if used)
  }
}

# For reference, this backend will be used like this in scripts:
#
# terraform init \
#   -backend-config="bucket=${PROJECT_ID}-tfstate" \
#   -backend-config="prefix=${ENV}/terraform/state" \
#   -backend-config="encryption_key=${ENCRYPTION_KEY}"

# Local values for state management
locals {
  # Generate consistent environment tag based on workspace
  environment_tag = terraform.workspace == "default" ? "dev" : terraform.workspace
  
  # Common tags to apply to all resources
  common_tags = {
    project     = var.project_id
    environment = local.environment_tag
    managed-by  = "terraform"
    creator     = "ai-orchestra-migration"
  }
}

# Output state configuration info for reference
output "terraform_state_bucket" {
  value       = "${var.project_id}-tfstate"
  description = "GCS bucket used for Terraform state storage"
}

output "terraform_state_prefix" {
  value       = "${local.environment_tag}/terraform/state"
  description = "Path prefix for terraform state within bucket"
}
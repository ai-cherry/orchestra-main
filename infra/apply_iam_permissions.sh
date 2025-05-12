#!/bin/bash
# apply_iam_permissions.sh
# Script to apply IAM permissions for Secret Manager admin access

set -e

# Default to dev environment if not specified
ENV=${1:-dev}
EMAIL=${2:-scoobyjava@cherry-ai.me}

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
  echo "Error: Environment must be 'dev' or 'prod'"
  echo "Usage: $0 [env] [email]"
  exit 1
fi

# Directory containing Terraform configurations
TF_DIR="/workspaces/orchestra-main/infra/orchestra-terraform"

echo "===== Applying Secret Manager Admin permissions for $EMAIL in $ENV environment ====="

# Ensure Terraform is installed and available
if ! command -v terraform &> /dev/null; then
  echo "Error: Terraform not found. Please ensure Terraform is installed."
  exit 1
fi

# Navigate to the Terraform directory
cd "$TF_DIR"

# If not already initialized
if [ ! -d ".terraform" ]; then
  echo "Initializing Terraform..."
  terraform init
fi

# Checking if we need to update the tfvars file with a new email
if [ "$EMAIL" != "scoobyjava@cherry-ai.me" ]; then
  echo "Updating $ENV.tfvars with new email: $EMAIL"
  # Create backup
  cp "$ENV.tfvars" "$ENV.tfvars.bak"
  
  # Update the email in the tfvars file
  sed -i "s/scoobyjava@cherry-ai.me/$EMAIL/g" "$ENV.tfvars"
fi

# Select workspace
terraform workspace select "$ENV" || terraform workspace new "$ENV"

# Plan the changes
echo "Planning Terraform changes..."
terraform plan -var-file="$ENV.tfvars" -out=tfplan

# Confirm before applying
read -p "Do you want to apply these changes? (y/n): " confirm
if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
  echo "Applying changes..."
  terraform apply tfplan
  
  echo "===== Secret Manager Admin permissions applied successfully ====="
  echo "User $EMAIL now has Secret Manager Admin permissions in $ENV environment"
else
  echo "Operation cancelled"
fi

# Clean up plan file
rm -f tfplan
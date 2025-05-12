#!/bin/bash
# apply_terraform_standards.sh
# Script to apply Terraform standards to the codebase

echo "Applying Terraform standards to the codebase..."

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Error: terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check if tflint is installed
if ! command -v tflint &> /dev/null; then
    echo "Warning: tflint is not installed. Only formatting and validation will be applied."
    echo "To install tflint, visit: https://github.com/terraform-linters/tflint#installation"
    HAS_TFLINT=false
else
    HAS_TFLINT=true
fi

# Directories to process
TERRAFORM_DIRS=(
    "terraform-modules/cloud-workstation"
    "terraform-modules/vertex-ai-vector-search"
    "gcp_migration/terraform/workstations"
    "terraform-example"
)

# Format and validate each directory
for dir in "${TERRAFORM_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"
        
        # Format Terraform files
        echo "  - Running terraform fmt..."
        terraform fmt "$dir"
        
        # Initialize Terraform if needed
        if [ ! -d "$dir/.terraform" ]; then
            echo "  - Initializing Terraform..."
            (cd "$dir" && terraform init -backend=false)
        fi
        
        # Validate Terraform configurations
        echo "  - Running terraform validate..."
        (cd "$dir" && terraform validate)
        
        # Run tflint if available
        if [ "$HAS_TFLINT" = true ]; then
            echo "  - Running tflint..."
            (cd "$dir" && tflint --format=compact)
        fi
        
        echo "  - Done processing $dir"
        echo ""
    else
        echo "Warning: Directory $dir does not exist, skipping."
    fi
done

echo "Terraform standards applied successfully!"
echo "To apply all code standards, run: python apply_code_standards.py"

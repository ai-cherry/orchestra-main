#!/bin/bash
# terraform-github.sh - GitHub SDK integration helper script for Terraform

set -e

# Check if GH_PAT_TOKEN is set
if [ -z "${GH_PAT_TOKEN}" ]; then
  echo "⚠️  Warning: GH_PAT_TOKEN environment variable is not set."
  echo "    GitHub provider functionality will be limited."
  echo "    Set this variable with your GitHub Personal Access Token:"
  echo "    export GH_PAT_TOKEN=your_github_token"
  echo ""
else
  echo "✅ GH_PAT_TOKEN environment variable is set."
fi

# Export as GITHUB_TOKEN as well for compatibility with different contexts
export GITHUB_TOKEN="${GH_PAT_TOKEN}"
export TF_VAR_github_token="${GH_PAT_TOKEN}"

# Parse command-line arguments
ACTION="plan"
EXTRA_ARGS=""

if [ $# -gt 0 ]; then
  ACTION="$1"
  shift
  EXTRA_ARGS="$@"
fi

# Change to the terraform directory
cd "$(dirname "$0")/terraform"

# Execute the requested Terraform command
case "${ACTION}" in
  init)
    echo "🚀 Initializing Terraform with GitHub provider..."
    terraform init ${EXTRA_ARGS}
    ;;
    
  plan)
    echo "📊 Creating Terraform plan with GitHub resources..."
    terraform plan ${EXTRA_ARGS}
    ;;
    
  apply)
    echo "🛠️  Applying Terraform configuration with GitHub resources..."
    terraform apply ${EXTRA_ARGS}
    ;;
    
  destroy)
    echo "🧨 Destroying Terraform-managed GitHub resources..."
    terraform destroy ${EXTRA_ARGS}
    ;;
    
  validate)
    echo "✓ Validating Terraform configuration with GitHub provider..."
    terraform validate ${EXTRA_ARGS}
    ;;
    
  github-repos)
    echo "📚 Listing GitHub repositories managed by Terraform..."
    terraform state list | grep github_repository
    ;;
    
  github-secrets)
    echo "🔒 Listing GitHub secrets managed by Terraform..."
    terraform state list | grep github_actions_secret
    ;;
    
  *)
    echo "🔄 Running custom Terraform command: ${ACTION}"
    terraform ${ACTION} ${EXTRA_ARGS}
    ;;
esac
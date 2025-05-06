#!/bin/bash
# test_master_service_key.sh - Test GCP Master Service Account Key Integration

echo "===== Testing GCP Master Service Account Integration ====="

# Make script fail on error
set -e

# Function to check if a variable is set
check_var() {
  local var_name="$1"
  if [[ -n "${!var_name}" ]]; then
    echo "✅ $var_name is set"
    return 0
  else
    echo "❌ $var_name is not set"
    return 1
  fi
}

# Test environment variables
echo "Checking for master service key..."
check_var "GCP_MASTER_SERVICE_JSON" || echo "  This variable should be set at the GitHub organization level (ai-cherry)"

# Test authentication with GCP_MASTER_SERVICE_JSON
if check_var "GCP_MASTER_SERVICE_JSON"; then
  echo -e "\nTesting authentication with GCP_MASTER_SERVICE_JSON..."
  # Save to temporary file
  echo "${GCP_MASTER_SERVICE_JSON}" > /tmp/gcp-master-key.json
  chmod 600 /tmp/gcp-master-key.json
  
  echo "Authenticating to GCP with master service key..."
  gcloud auth activate-service-account --key-file=/tmp/gcp-master-key.json
  
  # Set project ID
  gcloud config set project cherry-ai.me
  
  echo "Testing project access..."
  gcloud projects describe cherry-ai.me
  
  echo "Testing IAM capabilities..."
  gcloud iam service-accounts list
  
  echo "Testing secrets access..."
  gcloud secrets list
  
  echo "Testing storage access..."
  gcloud storage ls
  
  echo "Testing Cloud Run access..."
  gcloud run services list
  
  # Test Terraform integration
  echo -e "\nTesting Terraform integration with master key..."
  export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-master-key.json"
  cd /workspaces/orchestra-main/terraform
  terraform init -reconfigure -backend=false
  terraform validate
  
  # Cleanup
  rm /tmp/gcp-master-key.json
  echo "✅ Successfully tested master service key (GCP_MASTER_SERVICE_JSON)"
else
  echo "⚠️ Master service key not available for testing"
fi

# Print summary and usage instructions
echo -e "\n===== Summary ====="
echo "The master service key integration has been configured in:"
echo "1. Codespace setup script (setup_codespace_env.sh)"
echo "2. Devcontainer configuration (.devcontainer/devcontainer.json)"
echo "3. GitHub Actions workflow (.github/workflows/gcp-terraform-deploy.yml)"
echo "4. Cloud Build configuration (cloudbuild_github_integration.yaml)"

echo -e "\n===== Usage ====="
echo "You can utilize the master service key in the following ways:"

echo -e "\n1. Running VS Code tasks:"
echo "   - GitHub-GCP: Initialize Workspace"
echo "   - Terraform Plan"
echo "   - Terraform Apply"

echo -e "\n2. Using CLI helper functions:"
echo "   - test_master_service  # Test master service account capabilities"
echo "   - tf plan              # Run Terraform plan using the master key"
echo "   - tf apply             # Run Terraform apply using the master key"

echo -e "\n3. CI/CD pipelines:"
echo "   - Push to main branch to trigger automatic deployment"
echo "   - Create a PR to get a Terraform plan review"

echo -e "\nThe master service key will be used automatically with fallbacks to other keys if needed."
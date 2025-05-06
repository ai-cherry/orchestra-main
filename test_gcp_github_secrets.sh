#!/bin/bash
# test_gcp_github_secrets.sh - Test GCP authentication using GitHub organization secrets

set -e
echo "===== Testing GCP Authentication with GitHub Organization Secrets ====="

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
echo "Checking for organization-level secrets..."
check_var "GCP_PROJECT_ADMIN_KEY" || echo "  This variable should be set at the GitHub organization level"
check_var "GCP_SECRET_MANAGEMENT_KEY" || echo "  This variable should be set at the GitHub organization level"

# Test authentication with GCP_PROJECT_ADMIN_KEY (for everything except secrets)
if check_var "GCP_PROJECT_ADMIN_KEY"; then
  echo -e "\nTesting authentication with GCP_PROJECT_ADMIN_KEY (admin key for general access)..."
  # Save to temporary file
  echo "${GCP_PROJECT_ADMIN_KEY}" > /tmp/gcp-admin-key.json
  chmod 600 /tmp/gcp-admin-key.json
  
  echo "Authenticating to GCP with admin key..."
  gcloud auth activate-service-account --key-file=/tmp/gcp-admin-key.json
  
  echo "Listing GCP projects accessible with admin key..."
  gcloud projects list
  
  echo "Testing access to compute services..."
  gcloud compute instances list || echo "  Note: May fail if no instances exist or insufficient permissions"
  
  echo "Testing access to Cloud Run services..."
  gcloud run services list || echo "  Note: May fail if no services exist or insufficient permissions"
  
  echo "Testing access to storage buckets..."
  gcloud storage ls || echo "  Note: May fail if no buckets exist or insufficient permissions"
  
  echo "Testing Terraform functionality with admin key..."
  (cd terraform && terraform init -backend=false) || echo "  Note: Terraform init may fail if backend configuration is required"
  
  # Cleanup
  rm /tmp/gcp-admin-key.json
  echo "✅ Successfully tested GCP_PROJECT_ADMIN_KEY (for general admin access)"
fi

# Test authentication with GCP_SECRET_MANAGEMENT_KEY (specifically for secrets)
if check_var "GCP_SECRET_MANAGEMENT_KEY"; then
  echo -e "\nTesting authentication with GCP_SECRET_MANAGEMENT_KEY (specifically for secrets)..."
  # Save to temporary file
  echo "${GCP_SECRET_MANAGEMENT_KEY}" > /tmp/gcp-secret-key.json
  chmod 600 /tmp/gcp-secret-key.json
  
  echo "Authenticating to GCP with secret management key..."
  gcloud auth activate-service-account --key-file=/tmp/gcp-secret-key.json
  
  echo "Listing available secrets in the current project..."
  gcloud secrets list || echo "  Note: May fail if no secrets exist or insufficient permissions"
  
  echo "Testing ability to access a secret (will only show success/failure, not content)..."
  SECRET_NAME=$(gcloud secrets list --format="value(name)" 2>/dev/null | head -1)
  if [[ -n "$SECRET_NAME" ]]; then
    gcloud secrets versions access latest --secret="$SECRET_NAME" >/dev/null && echo "  ✅ Successfully accessed secret: $SECRET_NAME" || echo "  ❌ Failed to access secret: $SECRET_NAME"
  else 
    echo "  No secrets found to test access"
  fi
  
  # Cleanup
  rm /tmp/gcp-secret-key.json
  echo "✅ Successfully tested GCP_SECRET_MANAGEMENT_KEY (for secrets management)"
fi

# Test the keys together as they would be used in production
echo -e "\n===== Testing Full Integration Scenario ====="
echo "This test simulates how your CI/CD would use both keys together"

# First use admin key for general infrastructure
if check_var "GCP_PROJECT_ADMIN_KEY"; then
  echo "1. Using admin key for infrastructure deployment..."
  echo "${GCP_PROJECT_ADMIN_KEY}" > /tmp/gcp-admin-key.json
  chmod 600 /tmp/gcp-admin-key.json
  export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-admin-key.json"
  
  gcloud auth activate-service-account --key-file=/tmp/gcp-admin-key.json
  
  echo "2. Testing Terraform initialization (infrastructure preparation)..."
  (cd terraform && terraform init -backend=false)
  
  # Now switch to secret key for secrets management
  if check_var "GCP_SECRET_MANAGEMENT_KEY"; then
    echo "3. Switching to secrets management key for handling secrets..."
    echo "${GCP_SECRET_MANAGEMENT_KEY}" > /tmp/gcp-secret-key.json
    chmod 600 /tmp/gcp-secret-key.json
    export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-secret-key.json"
    
    gcloud auth activate-service-account --key-file=/tmp/gcp-secret-key.json
    
    echo "4. Verifying secret access capabilities..."
    gcloud secrets list --limit=5
    
    echo "5. Switching back to admin key for final deployment..."
    export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-admin-key.json"
    gcloud auth activate-service-account --key-file=/tmp/gcp-admin-key.json
  fi
  
  # Clean up
  rm -f /tmp/gcp-admin-key.json /tmp/gcp-secret-key.json
fi

echo "===== GCP Authentication Test Complete ====="

# Print summary information about the configured environment
echo -e "\n===== Environment Summary ====="
echo "Current GCP account: $(gcloud config get-value account)"
echo "Current GCP project: $(gcloud config get-value project)"
echo "Terraform version: $(terraform --version | head -1)"
echo "GCloud SDK version: $(gcloud --version | head -1)"
echo "GitHub CLI version: $(gh --version 2>/dev/null | head -1)" || echo "GitHub CLI not installed or not authenticated"
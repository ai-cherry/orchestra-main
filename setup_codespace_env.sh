#!/bin/bash
# setup_codespace_env.sh - Configure Codespace environment for GCP and GitHub integration

# Setup logging and error handling
LOG_FILE="/tmp/codespace_setup.log"
ERROR_FILE="/tmp/codespace_setup_error.log"

  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# Function to handle errors
handle_error() {
  local exit_code=$?
  local line_number=$1
  log_message "❌ ERROR: Command failed at line $line_number with exit code $exit_code" | tee -a "$ERROR_FILE"
  log_message "Check $ERROR_FILE and $LOG_FILE for details"
  exit $exit_code
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Enable command logging
exec > >(tee -a "$LOG_FILE") 2>&1

log_message "🚀 Setting up Codespace environment for Orchestra project..."
log_message "💾 Current directory: $(pwd)"

# Make script fail on error
set -e

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  log_message "⚠️ requirements.txt not found, creating a basic version..."
  cat > requirements.txt << EOF
# Core dependencies for AI Orchestra
fastapi>=0.95.0
pydantic>=2.0.0
uvicorn>=0.22.0
google-cloud-firestore>=2.11.0
google-cloud-secret-manager>=2.16.0
python-dotenv>=1.0.0
EOF
  log_message "✅ Created basic requirements.txt file"
fi

# Create a workspace for Terraform state
log_message "Creating Terraform workspace directory..."
mkdir -p ~/.terraform.d

# Configure GitHub CLI
if [[ -n "${GITHUB_TOKEN}" ]]; then
  log_message "🔑 Setting up GitHub CLI authentication..."
  if ! (echo "${GITHUB_TOKEN}" | gh auth login --with-token); then
    log_message "⚠️ GitHub CLI authentication failed. Continuing without GitHub authentication."
  else
    gh auth status
    log_message "✅ GitHub CLI authentication successful"
  fi
else
  log_message "⚠️ GITHUB_TOKEN not found. Please set GH_PAT_TOKEN in your Codespaces secrets."
fi

# Configure Terraform credentials for GitHub
if [[ -n "${TF_VAR_github_token}" ]]; then
  log_message "🔧 Configuring Terraform for GitHub provider..."
  
  # Create directory if it doesn't exist
  mkdir -p ~/.terraform.d
  
  # Create credentials file
  cat > ~/.terraform.d/credentials.tfrc.json <<EOF
{
  "credentials": {
    "app.terraform.io": {
      "token": null
    },
    "github.com": {
      "token": "${TF_VAR_github_token}"
    }
  }
}
EOF
  chmod 600 ~/.terraform.d/credentials.tfrc.json
  log_message "✅ Terraform credentials configured"
else
  log_message "⚠️ TF_VAR_github_token not found. Terraform GitHub provider will not be configured."
fi

# Configure GCP authentication with organization secrets - prioritize master service key
if [[ -n "${GCP_MASTER_SERVICE_JSON}" ]]; then
  log_message "🔐 Setting up GCP authentication with GCP_MASTER_SERVICE_JSON (master service account)..."
  gcloud projects list
  echo "Testing IAM access:"
  gcloud iam service-accounts list
  echo "Testing Secret Manager access:"
  gcloud secrets list
  echo "Testing Cloud Run access:"
  gcloud run services list
}
EOF

# Add helpers to bash profile
echo "source ~/.bash_helpers" >> ~/.bashrc

# Install additional Python dependencies if needed
if [[ -f "/workspaces/orchestra-main/requirements-dev.txt" ]]; then
  echo "📦 Installing Python dependencies..."
  pip install -r /workspaces/orchestra-main/requirements-dev.txt
fi

echo "✅ Codespace environment setup complete!"
echo "You can now use Terraform with GCP and GitHub integration."
echo "🌎 Project ID set to: cherry-ai.me"
#!/bin/bash

# Cleanup script for GCP authentication and hybrid IDE setup
# This script ensures no conflicting configurations exist with the new setup

echo "Starting GCP configuration cleanup..."

# 1. Revoke all existing gcloud credentials
echo "Revoking all existing gcloud credentials..."
gcloud auth revoke --all || echo "No credentials to revoke or command failed"

# 2. Remove old gcloud configuration directories
echo "Removing old gcloud configuration directories..."
rm -rf ~/.config/gcloud

# Ensure our target directory exists but clean any files other than service-account.json
echo "Preserving only the service account JSON file in ~/.gcp..."
mkdir -p ~/.gcp
find ~/.gcp -type f -not -name 'service-account.json' -delete 2>/dev/null || true

# 3. Clean up environment variables in ~/.bashrc and ~/.bash_profile
echo "Cleaning up environment variables in shell config files..."
for file in ~/.bashrc ~/.bash_profile ~/.profile; do
  if [ -f "$file" ]; then
    # Remove any existing GOOGLE_APPLICATION_CREDENTIALS lines
    sed -i '/GOOGLE_APPLICATION_CREDENTIALS/d' "$file"
    
    # Remove any GCP_PROJECT or GCLOUD_PROJECT variables
    sed -i '/GCP_PROJECT=/d' "$file"
    sed -i '/GCLOUD_PROJECT=/d' "$file"
    
    # Remove CLOUDSDK environment variables that could conflict
    sed -i '/CLOUDSDK_CORE_PROJECT=/d' "$file"
    sed -i '/CLOUDSDK_CORE_ACCOUNT=/d' "$file"
    sed -i '/CLOUDSDK_CORE_REGION=/d' "$file"
    sed -i '/CLOUDSDK_CORE_ZONE=/d' "$file"
    sed -i '/CLOUDSDK_COMPUTE_REGION=/d' "$file"
    sed -i '/CLOUDSDK_COMPUTE_ZONE=/d' "$file"
    
    echo "Cleaned up $file"
  fi
done

# Add our correct GOOGLE_APPLICATION_CREDENTIALS line to ~/.bashrc
if ! grep -q "export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp/service-account.json" ~/.bashrc; then
  echo "Adding correct GOOGLE_APPLICATION_CREDENTIALS to ~/.bashrc..."
  echo 'export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp/service-account.json' >> ~/.bashrc
fi

# 4. Remove any old post-create scripts that might conflict
echo "Removing any conflicting scripts in .devcontainer directory..."
if [ -d ".devcontainer" ]; then
  find .devcontainer -name "post-create.sh" -delete 2>/dev/null || true
  find .devcontainer -name "post-attach.sh" -delete 2>/dev/null || true
  find .devcontainer -name "post-start.sh" -delete 2>/dev/null || true
fi

# Check for any conflicting GCP auth scripts in the repo
echo "Looking for and handling specific conflicting scripts..."

# Specific scripts to disable (not delete)
CONFLICT_SCRIPTS=(
  "gcloud_config.sh"
  "hardcode_gcp_config.sh"
  "check_gcloud.sh"
  "ensure_gcp_env.sh"
  "source_env_and_ensure_gcp.sh"
  "verify_gcp_config.sh"
  "authenticate_codespaces.sh"
  "setup_and_verify_gcp.sh"
)

for script in "${CONFLICT_SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    echo "Disabling conflicting script: $script"
    mv "$script" "$script.bak"
    echo "#!/bin/bash
# This script has been disabled by cleanup_gcp_config.sh
# The original content is saved as $script.bak
echo \"This script has been disabled to prevent conflicts with the new GCP authentication setup.\"
echo \"If you need the original functionality, rename $script.bak back to $script\"
exit 0" > "$script"
    chmod +x "$script"
  fi
done

# Look for any other potential conflicting scripts
echo "Looking for other potentially conflicting scripts..."
find . -name "*gcloud*auth*.sh" -not -path "./setup-gcp-ides.sh" -not -path "./cleanup_gcp_config.sh" -exec echo "Found potentially conflicting script: {}" \; 2>/dev/null || true

# 5. Verify the cleanup
echo -e "\nVerifying cleanup..."
echo "Current auth accounts:"
gcloud auth list 2>/dev/null || echo "No authenticated accounts found"

echo -e "\nCurrent gcloud configuration:"
gcloud config list 2>/dev/null || echo "No gcloud configuration found"

# 6. Ensure service account credentials file exists (if GitHub secret is available)
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
  echo -e "\nRecreating service account credentials file..."
  mkdir -p ~/.gcp
  echo "$GCP_MASTER_SERVICE_JSON" > ~/.gcp/service-account.json
  echo "Service account credentials file recreated at ~/.gcp/service-account.json"
else
  echo -e "\nWARNING: GCP_MASTER_SERVICE_JSON environment variable not found."
  echo "You will need to set this GitHub secret for automatic authentication."
fi

# 7. Activate service account if credentials file exists
if [ -f ~/.gcp/service-account.json ]; then
  echo -e "\nActivating service account..."
  gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=~/.gcp/service-account.json
  gcloud config set project cherry-ai-project
  echo "Service account activated and project set to cherry-ai-project"
else
  echo -e "\nWARNING: Service account credentials file not found at ~/.gcp/service-account.json"
  echo "Authentication may not work properly until this is set up."
fi

echo -e "\nCleanup completed! Your environment is now prepared for the new GCP hybrid IDE setup."
echo "Next steps:"
echo "1. Ensure the GCP_MASTER_SERVICE_JSON GitHub secret is set"
echo "2. Run ./setup-gcp-ides.sh to provision your Cloud Workstation and Vertex AI Workbench"

#!/bin/bash
# populate_pulumi_secrets.sh - A script to assist in setting Pulumi Cloud secrets for the 'dev' stack
# This script guides the user through setting secrets for Pulumi Cloud configuration.
# It ensures that secrets are set securely without being stored in plaintext in version control.

echo "Pulumi Cloud Secret Population Script for Orchestra AI"
echo "=============================================="
echo "This script will help you set secrets for your Pulumi 'dev' stack in Pulumi Cloud."
echo "You will be prompted to enter each secret value manually or provide a source (if applicable)."
echo "These values are NOT stored in this script or in version control."
echo "Ensure you have Pulumi CLI authenticated with Pulumi Cloud."
echo "=============================================="

# Check if Pulumi is logged in to Cloud
if ! pulumi whoami &> /dev/null; then
  echo "ERROR: Pulumi CLI is not authenticated with Pulumi Cloud."
  echo "Please run 'pulumi login' to authenticate."
  exit 1
fi

# Check if 'dev' stack is selected
CURRENT_STACK=$(pulumi stack --show-name)
if [[ "$CURRENT_STACK" != "dev" ]]; then
  echo "WARNING: 'dev' stack is not selected. Attempting to select 'dev' stack..."
  pulumi stack select dev
  if [[ $? -ne 0 ]]; then
    echo "ERROR: Failed to select 'dev' stack. Please initialize it with 'pulumi stack init dev'."
    exit 1
  fi
fi

echo "Current Pulumi stack: $(pulumi stack --show-name)"
echo "Proceeding to set secrets for Pulumi Cloud configuration..."

# List of secret keys to set for Pulumi configuration
SECRET_KEYS=(
  "digitalocean:token"
  "orchestra-infra:dragonfly_uri"
  "orchestra-infra:mongo_uri"
  "orchestra-infra:weaviate_url"
  "orchestra-infra:weaviate_api_key"
  "orchestra-infra:openai_api_key"
  "orchestra-infra:anthropic_api_key"
  "orchestra-infra:openrouter_api_key"
  "orchestra-infra:portkey_api_key"
  "orchestra-infra:pulumi_access_token"
  "orchestra-infra:perplexity_api_key"
  "orchestra-infra:mongodb_org_id"
  "orchestra-infra:mongodb_api_public_key"
  "orchestra-infra:mongodb_api_private_key"
  "orchestra-infra:mongodb_service_client_id"
  "orchestra-infra:mongodb_service_client_secret"
  "orchestra-infra:ssh_private_key_path"
)

# Counter for tracking progress
TOTAL_SECRETS=${#SECRET_KEYS[@]}
SET_SECRETS=0

# Loop through each secret key and prompt user for input
for KEY in "${SECRET_KEYS[@]}"; do
  echo "----------------------------------------------"
  echo "Setting secret for: $KEY"
  echo "Please enter the value for $KEY (input will be hidden for security):"
  read -s SECRET_VALUE
  echo ""

  if [[ -n "$SECRET_VALUE" ]]; then
    # Set the secret in Pulumi Cloud configuration
    echo "Setting secret in Pulumi Cloud..."
    echo "$SECRET_VALUE" | pulumi config set --secret "$KEY"
    if [[ $? -eq 0 ]]; then
      echo "Successfully set secret for $KEY in Pulumi Cloud."
      ((SET_SECRETS++))
    else
      echo "ERROR: Failed to set secret for $KEY. Please check your input or Pulumi authentication."
    fi
  else
    echo "WARNING: Empty value provided for $KEY. Skipping..."
  fi
done

echo "=============================================="
echo "Secret Setting Summary:"
echo "Total secrets to set: $TOTAL_SECRETS"
echo "Secrets successfully set: $SET_SECRETS"
echo "=============================================="

if [[ $SET_SECRETS -eq $TOTAL_SECRETS ]]; then
  echo "All secrets have been set successfully!"
  echo "You can now proceed with deployment or other Pulumi operations without passphrase prompts."
  echo "Please inform your AI assistant by typing 'SECRETS SET' to continue with cleanup and deployment."
else
  echo "WARNING: Not all secrets were set. You may need to rerun this script or manually set the remaining secrets."
  echo "To set a specific secret manually, use: pulumi config set --secret <key> <value>"
fi

echo "Script execution complete."

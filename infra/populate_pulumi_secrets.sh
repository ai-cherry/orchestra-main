#!/bin/bash
# populate_pulumi_secrets.sh - Script to configure Pulumi secrets using GitHub org secrets
# Supports both manual entry (backward compat) and GitHub secrets via env vars

echo "Pulumi Secret Configuration Script for Orchestra AI"
echo "=============================================="
echo "This script configures Pulumi secrets using GitHub organization secrets"
echo "Secrets are read from environment variables when available"
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
echo "Proceeding to configure secrets..."

# List of secret keys to configure
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

# Configure Pulumi passphrase from env var if available
if [[ -n "$PULUMI_CONFIGURE_PASSPHRASE" ]]; then
  echo "Configuring Pulumi passphrase from environment variable..."
  export PULUMI_CONFIG_PASSPHRASE="$PULUMI_CONFIGURE_PASSPHRASE"
  echo "Pulumi passphrase configured from environment variable"
fi

# Loop through each secret key
for KEY in "${SECRET_KEYS[@]}"; do
  echo "----------------------------------------------"
  echo "Configuring secret for: $KEY"

  # Generate env var name (convert : to _ and uppercase)
  ENV_VAR_NAME="ORG_${KEY//:/_}"
  ENV_VAR_NAME="${ENV_VAR_NAME^^}"

  # Check if env var is set
  if [[ -n "${!ENV_VAR_NAME}" ]]; then
    echo "Using value from environment variable $ENV_VAR_NAME"
    echo "${!ENV_VAR_NAME}" | pulumi config set --secret "$KEY"
    if [[ $? -eq 0 ]]; then
      echo "Successfully set secret for $KEY from environment variable"
      ((SET_SECRETS++))
    else
      echo "ERROR: Failed to set secret for $KEY from environment variable"
    fi
  else
    # Fallback to manual entry
    echo "Environment variable $ENV_VAR_NAME not set"
    echo "Please enter the value for $KEY (input will be hidden for security):"
    read -s SECRET_VALUE
    echo ""

    if [[ -n "$SECRET_VALUE" ]]; then
      echo "$SECRET_VALUE" | pulumi config set --secret "$KEY"
      if [[ $? -eq 0 ]]; then
        echo "Successfully set secret for $KEY manually"
        ((SET_SECRETS++))
      else
        echo "ERROR: Failed to set secret for $KEY"
      fi
    else
      echo "WARNING: Empty value provided for $KEY. Skipping..."
    fi
  fi
done

echo "=============================================="
echo "Secret Configuration Summary:"
echo "Total secrets to configure: $TOTAL_SECRETS"
echo "Secrets successfully configured: $SET_SECRETS"
echo "=============================================="

if [[ $SET_SECRETS -eq $TOTAL_SECRETS ]]; then
  echo "All secrets have been configured successfully!"
  echo "You can now proceed with deployment or other Pulumi operations."
else
  echo "WARNING: Not all secrets were configured. You may need to rerun this script."
  echo "To set a specific secret manually, use: pulumi config set --secret <key> <value>"
fi

echo "Script execution complete."

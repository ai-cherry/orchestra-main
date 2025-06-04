#!/bin/bash
# Cherry AI Automated Local Setup Script
set -euo pipefail

# Set Pulumi passphrase for non-interactive secret management
export PULUMI_CONFIG_PASSPHRASE="cherry_ai-dev-123"

# Install Python dependencies for infra
pip install -r infra/requirements.txt

# Set Pulumi secrets from environment variables (if available)
cd infra
if [ -n "${OPENAI_API_KEY:-}" ]; then
  pulumi config set --secret openai_api_key "$OPENAI_API_KEY"
fi
if [ -n "${WEAVIATE_API_KEY:-}" ]; then
  pulumi config set --secret weaviate_api_key "$WEAVIATE_API_KEY"
fi
if [ -n "${MONGODB_CONNECTION_STRING:-}" ]; then
  pulumi config set --secret mongodb_connection_string "$MONGODB_CONNECTION_STRING"
fi
if [ -n "${MONGODB_SERVICE_CLIENT_ID:-}" ]; then
  pulumi config set --secret mongodb_service_client_id "$MONGODB_SERVICE_CLIENT_ID"
fi
if [ -n "${MONGODB_SERVICE_CLIENT_SECRET:-}" ]; then
  pulumi config set --secret mongodb_service_client_secret "$MONGODB_SERVICE_CLIENT_SECRET"
fi
if [ -n "${GRAFANA_ADMIN_PASSWORD:-}" ]; then
  pulumi config set --secret grafana_admin_password "$GRAFANA_ADMIN_PASSWORD"
fi
if [ -n "${DIGITALOCEAN_TOKEN:-}" ]; then
  pulumi config set --secret digitalocean:token "$DIGITALOCEAN_TOKEN"
fi
if [ -n "${DRAGONFLY_URI:-}" ]; then
  pulumi config set --secret dragonfly_uri "$DRAGONFLY_URI"
fi
if [ -n "${MONGO_URI:-}" ]; then
  pulumi config set --secret mongo_uri "$MONGO_URI"
fi
if [ -n "${WEAVIATE_URL:-}" ]; then
  pulumi config set --secret weaviate_url "$WEAVIATE_URL"
fi
if [ -n "${DO_ROOT_PASSWORD:-}" ]; then
  pulumi config set --secret root_password "$DO_ROOT_PASSWORD"
fi
cd ..

echo "Local environment setup complete. Pulumi passphrase and secrets are set."

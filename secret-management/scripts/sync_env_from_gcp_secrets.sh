#!/bin/bash
# sync_env_from_gcp_secrets.sh
# Fetches secrets from Google Secret Manager and updates .env for local/dev use.
# Designed for single-developer, high-performance projects. Idempotent and safe.

set -euo pipefail

# --- CONFIGURATION ---

# List your required secret names here (these must exist in GCP Secret Manager)
SECRETS=(
  "API_KEY"
  "DB_PASSWORD"
  "SLACK_TOKEN"
  "GONG_IO_TOKEN"
  "ESTUARY_API_KEY"
  # Add more as needed
)

# Set your GCP project ID (override with env var if needed)
GCP_PROJECT="${GCP_PROJECT:-your-gcp-project-id}"

# Path to .env file (default: project root)
ENV_FILE="${ENV_FILE:-.env}"

# --- LOGIC ---

if ! command -v gcloud &>/dev/null; then
  echo "ERROR: gcloud CLI is not installed or not in PATH."
  exit 1
fi

if [ -z "$GCP_PROJECT" ] || [ "$GCP_PROJECT" = "your-gcp-project-id" ]; then
  echo "ERROR: GCP_PROJECT is not set. Edit this script or set the GCP_PROJECT env var."
  exit 1
fi

touch "$ENV_FILE"

for SECRET in "${SECRETS[@]}"; do
  VALUE=$(gcloud secrets versions access latest --secret="$SECRET" --project="$GCP_PROJECT" 2>/dev/null || true)
  if [ -n "$VALUE" ]; then
    # Remove any existing entry for this secret in .env
    sed -i "/^$SECRET=/d" "$ENV_FILE"
    # Append new value (quoted for safety)
    echo "$SECRET=\"$VALUE\"" >> "$ENV_FILE"
    echo "Synced $SECRET from Google Secret Manager."
  else
    echo "WARNING: Secret $SECRET not found in project $GCP_PROJECT. Skipping."
  fi
done

echo "All secrets synced to $ENV_FILE."

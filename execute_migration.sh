#!/bin/bash
# Execute the migration using environment variables

set -e

echo "Setting up environment variables..."
export GCP_PROJECT_ID="agi-baby-cherry"
export GCP_ORG_ID="873291114285"

# Load service account JSON from file
if [ -f "vertex-agent-service-account.json" ]; then
  echo "Using service account credentials from vertex-agent-service-account.json"
  export GCP_SA_JSON=$(cat vertex-agent-service-account.json)
else
  echo "Error: Service account file not found!"
  exit 1
fi

echo "Environment variables set successfully"
echo "Executing migration script with --force-install flag..."

# Execute the migration script
./migrate_and_setup_corrected.sh --force-install

echo "Migration completed!"

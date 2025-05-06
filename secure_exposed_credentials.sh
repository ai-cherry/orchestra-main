#!/bin/bash
# secure_exposed_credentials.sh
#
# This script securely stores the exposed credentials in Secret Manager
# and removes any plaintext copies.

set -e

echo "Securing exposed credentials..."

# Create a temporary file for the service account key
TEMP_KEY_FILE=$(mktemp)
echo '{
  "type": "service_account",
  "project_id": "PROJECT_ID_PLACEHOLDER",
  "private_key_id": "PRIVATE_KEY_ID_PLACEHOLDER",
  "private_key": "REDACTED",
  "client_email": "EMAIL_PLACEHOLDER@PROJECT_ID_PLACEHOLDER.iam.gserviceaccount.com",
  "client_id": "CLIENT_ID_PLACEHOLDER",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/EMAIL_PLACEHOLDER%40PROJECT_ID_PLACEHOLDER.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}' > "$TEMP_KEY_FILE"

# Set up authentication with the service account
export GOOGLE_APPLICATION_CREDENTIALS="$TEMP_KEY_FILE"

# Store project information in Secret Manager
echo "Storing project information in Secret Manager..."
echo "PROJECT_ID_PLACEHOLDER" | gcloud secrets create project-id --data-file=- --project=PROJECT_ID_PLACEHOLDER || \
  echo "PROJECT_ID_PLACEHOLDER" | gcloud secrets versions add project-id --data-file=- --project=PROJECT_ID_PLACEHOLDER

echo "PROJECT_NUMBER_PLACEHOLDER" | gcloud secrets create project-number --data-file=- --project=PROJECT_ID_PLACEHOLDER || \
  echo "PROJECT_NUMBER_PLACEHOLDER" | gcloud secrets versions add project-number --data-file=- --project=PROJECT_ID_PLACEHOLDER

# Store the service account key in Secret Manager
echo "Storing service account key in Secret Manager..."
gcloud secrets create secret-management-key --data-file="$TEMP_KEY_FILE" --project=PROJECT_ID_PLACEHOLDER || \
  gcloud secrets versions add secret-management-key --data-file="$TEMP_KEY_FILE" --project=PROJECT_ID_PLACEHOLDER

# Clean up
echo "Cleaning up temporary files..."
rm -f "$TEMP_KEY_FILE"

echo "Credentials secured in Secret Manager."
echo "IMPORTANT: Make sure to remove any plaintext copies of these credentials from:"
echo "- Chat history"
echo "- Local files"
echo "- Environment variables"
echo "- Any other locations where they might be stored"

echo "Done."
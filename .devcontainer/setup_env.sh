#!/bin/bash
# This script fetches secrets, prepares environment variable export commands,
# and attempts Docker login.
# It's intended to be called by postStartCommand in devcontainer.json.

set -e # Exit immediately if a command exits with a non-zero status.

OUTPUT_ENV_FILE="/tmp/devcontainer_exports.sh"
KEY_FILE_PATH="/tmp/platform-admin-key.json" # Fixed path for the main SA key

# Ensure the directory for the env file exists and clear previous content
mkdir -p "$(dirname "$OUTPUT_ENV_FILE")"
> "$OUTPUT_ENV_FILE"

echo "Devcontainer Setup: Initializing environment configuration..."

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud command not found. Please ensure Google Cloud SDK is installed in the dev container (e.g., via features in devcontainer.json)." >&2
    exit 1 # Critical dependency missing
fi

# Check gcloud authentication status (basic check)
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q '.'; then
  echo "Warning: gcloud may not be authenticated. Secret fetching might fail or be incomplete." >&2
  echo "If issues arise, please run 'gcloud auth login --update-adc' or 'gcloud auth application-default login' in the container's terminal and rebuild the container." >&2
fi

# Fetch platform-admin-key (for GOOGLE_APPLICATION_CREDENTIALS)
# This uses the gcloud CLI's currently configured default project, matching previous behavior.
echo "Fetching platform-admin-key (uses default gcloud project)..."
mkdir -p "$(dirname "$KEY_FILE_PATH")" # Ensure directory for SA key exists
if gcloud secrets versions access latest --secret=platform-admin-key > "$KEY_FILE_PATH"; then
  chmod 600 "$KEY_FILE_PATH" # Secure the key file
  echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_FILE_PATH\"" >> "$OUTPUT_ENV_FILE"
  echo "GOOGLE_APPLICATION_CREDENTIALS successfully configured to use $KEY_FILE_PATH."
else
  echo "Warning: Failed to fetch 'platform-admin-key'. GOOGLE_APPLICATION_CREDENTIALS will not be set. Check secret name and permissions in your default gcloud project." >&2
  # Clean up if file was created but empty or partial
  rm -f "$KEY_FILE_PATH"
fi

# Define other secrets to fetch and the project they reside in
# Based on previous configuration, these are in 'cherry-ai-project'
GCLOUD_PROJECT_FOR_OTHERS="cherry-ai-project"
SECRETS_TO_FETCH=(
  "OPENROUTER_API_KEY"
  "PORTKEY_API_KEY"
  "PULUMI_ACCESS_TOKEN"
  "GH_FINE_PAT"
  "GH_CLASSIC_PAT"
  # Add other secrets here. Ensure they exist in Secret Manager under the specified project.
)

echo "Fetching other API keys from project '$GCLOUD_PROJECT_FOR_OTHERS'..."
for SECRET_NAME in "${SECRETS_TO_FETCH[@]}"; do
  SECRET_VALUE=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$GCLOUD_PROJECT_FOR_OTHERS" 2>/dev/null)
  if [ $? -eq 0 ] && [ -n "$SECRET_VALUE" ]; then
    # Escape single quotes in the secret value for safe export
    ESCAPED_SECRET_VALUE=$(echo "$SECRET_VALUE" | sed "s/'/'\\''/g")
    echo "export $SECRET_NAME='$ESCAPED_SECRET_VALUE'" >> "$OUTPUT_ENV_FILE"
    echo "$SECRET_NAME fetched from '$GCLOUD_PROJECT_FOR_OTHERS' and prepared for export."
  else
    echo "Warning: Secret '$SECRET_NAME' not found in project '$GCLOUD_PROJECT_FOR_OTHERS' or permission denied. It will not be exported." >&2
  fi
done

# Attempt Docker Hub login using secrets
# Assumes DOCKERHUB_USER and DOCKERHUB_PAT secrets exist in GCLOUD_PROJECT_FOR_OTHERS
echo "Attempting Docker Hub login using 'DOCKERHUB_USER' and 'DOCKERHUB_PAT' secrets from project '$GCLOUD_PROJECT_FOR_OTHERS'..."
DOCKERHUB_USER_VAL=$(gcloud secrets versions access latest --secret="DOCKERHUB_USER" --project="$GCLOUD_PROJECT_FOR_OTHERS" 2>/dev/null)
DOCKERHUB_PAT_VAL=$(gcloud secrets versions access latest --secret="DOCKERHUB_PAT" --project="$GCLOUD_PROJECT_FOR_OTHERS" 2>/dev/null)

if [ -n "$DOCKERHUB_USER_VAL" ] && [ -n "$DOCKERHUB_PAT_VAL" ]; then
  if command -v docker &> /dev/null; then
    echo "$DOCKERHUB_PAT_VAL" | docker login --username "$DOCKERHUB_USER_VAL" --password-stdin
    if [ $? -eq 0 ]; then
      echo "Docker Hub login successful for user '$DOCKERHUB_USER_VAL'."
    else
      echo "Warning: Docker Hub login failed for user '$DOCKERHUB_USER_VAL'. Check credentials and Docker setup." >&2
    fi
  else
    echo "Warning: Docker command not found. Skipping Docker Hub login." >&2
  fi
else
  echo "DOCKERHUB_USER or DOCKERHUB_PAT secret not found in '$GCLOUD_PROJECT_FOR_OTHERS'. Skipping Docker Hub login."
  echo "To enable automated Docker login, ensure these secrets are available."
fi

echo "Devcontainer Setup: Environment export definitions generated at $OUTPUT_ENV_FILE."
echo "The postStartCommand will source this file to apply settings for your session and append to shell profiles for future sessions."
echo "Devcontainer Setup: Configuration script finished." 
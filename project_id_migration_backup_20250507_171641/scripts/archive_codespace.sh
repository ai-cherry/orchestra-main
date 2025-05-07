i#!/bin/bash
# archive_codespace.sh - Script to archive Codespaces workspace, upload to GCS, and provide restoration instructions.

# Exit on any error
set -e

# Define variables
GCS_BUCKET="gs://agi-baby-cherry-bucket"
WORKSPACE_DIR="/workspaces/orchestra-main"
EXCLUDE_DIRS=(".tmp" "dist" ".git" "node_modules" ".cache")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_FILENAME="codespace_archive_${CODESPACE_NAME:-unknown}_${TIMESTAMP}.tar.gz"
METADATA_FILENAME="codespace_archive_${CODESPACE_NAME:-unknown}_${TIMESTAMP}_metadata.json"
TEMP_DIR="/tmp/codespace_archive"
ARCHIVE_PATH="${TEMP_DIR}/${ARCHIVE_FILENAME}"
METADATA_PATH="${TEMP_DIR}/${METADATA_FILENAME}"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Ensure temporary directory exists
mkdir -p "${TEMP_DIR}"

# Build tar exclusion parameters
EXCLUDE_PARAMS=()
for dir in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_PARAMS+=("--exclude=${WORKSPACE_DIR}/${dir}")
done

log "Creating archive of workspace at ${WORKSPACE_DIR}..."
# Create tarball with preserved permissions and symlinks, excluding specified directories
tar -czvf "${ARCHIVE_PATH}" -C "${WORKSPACE_DIR}" "${EXCLUDE_PARAMS[@]}" .

log "Uploading archive to ${GCS_BUCKET}/${ARCHIVE_FILENAME}..."
# Upload the archive to GCS
gsutil cp "${ARCHIVE_PATH}" "${GCS_BUCKET}/${ARCHIVE_FILENAME}"

log "Generating metadata file..."
# Generate metadata in JSON format
cat << EOF > "${METADATA_PATH}"
{
  "archive_name": "${ARCHIVE_FILENAME}",
  "workspace": "${WORKSPACE_DIR}",
  "codespace_name": "${CODESPACE_NAME:-unknown}",
  "timestamp": "${TIMESTAMP}",
  "creation_date": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "excluded_directories": $(printf '%s\n' "${EXCLUDE_DIRS[@]}" | jq -R . | jq -s .),
  "gcs_bucket": "${GCS_BUCKET}",
  "archive_size": "$(du -h "${ARCHIVE_PATH}" | cut -f1)",
  "restoration_instructions": {
    "google_cloud_workstation": {
      "step1": "Ensure you have the Google Cloud SDK installed and authenticated with 'gcloud auth login'.",
      "step2": "Download the archive using: gsutil cp ${GCS_BUCKET}/${ARCHIVE_FILENAME} /tmp/${ARCHIVE_FILENAME}",
      "step3": "Extract the archive to your desired location with: tar -xzvf /tmp/${ARCHIVE_FILENAME} -C /path/to/restore",
      "step4": "Navigate to the restored directory and proceed with any necessary setup or configuration."
    },
    "vertex_ai_workbench": {
      "step1": "Access your Vertex AI Workbench instance via the Google Cloud Console.",
      "step2": "Open a terminal in the Workbench environment.",
      "step3": "Download the archive using: gsutil cp ${GCS_BUCKET}/${ARCHIVE_FILENAME} /tmp/${ARCHIVE_FILENAME}",
      "step4": "Extract the archive with: tar -xzvf /tmp/${ARCHIVE_FILENAME} -C /home/jupyter/workspace",
      "step5": "Refresh the Workbench file browser to see the restored files and proceed with setup."
    }
  }
}
EOF

log "Uploading metadata to ${GCS_BUCKET}/${METADATA_FILENAME}..."
# Upload the metadata file to GCS
gsutil cp "${METADATA_PATH}" "${GCS_BUCKET}/${METADATA_FILENAME}"

log "Cleaning up temporary files..."
# Clean up temporary files
rm -rf "${TEMP_DIR}"

log "Archive and metadata upload completed successfully."
log "Archive uploaded to: ${GCS_BUCKET}/${ARCHIVE_FILENAME}"
log "Metadata uploaded to: ${GCS_BUCKET}/${METADATA_FILENAME}"
log "Restoration instructions are included in the metadata file. You can view them with:"
log "  gsutil cat ${GCS_BUCKET}/${METADATA_FILENAME} | jq '.restoration_instructions'"
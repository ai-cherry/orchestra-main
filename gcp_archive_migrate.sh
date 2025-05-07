#!/bin/bash
# gcp_archive_migrate.sh - Archive and migrate codebase to Google Cloud Storage
# 
# This script archives all source code, notebooks, and configuration files
# and uploads them to a GCS bucket for migration to a new environment.

set -e

# Configuration variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="orchestra_migration_${TIMESTAMP}.tar.gz"
GCS_BUCKET="gs://cherry-ai-project-migration"
WORKSPACE_DIR="$(pwd)"
LOG_FILE="${WORKSPACE_DIR}/migration_${TIMESTAMP}.log"

# Files/directories to exclude from the archive
EXCLUDE_PATTERNS=(
  "--exclude=.git"
  "--exclude=__pycache__"
  "--exclude=*.pyc"
  "--exclude=venv"
  "--exclude=.venv"
  "--exclude=node_modules"
  "--exclude=.env"
  "--exclude=*.log"
  "--exclude=*.tar.gz"
)

# Print colored output
print_color() {
  local color_code="$1"
  local message="$2"
  echo -e "\033[${color_code}m${message}\033[0m"
}

log_message() {
  local message="$1"
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  echo "[${timestamp}] ${message}" | tee -a "${LOG_FILE}"
}

print_header() {
  print_color "1;34" "\n========================================================"
  print_color "1;34" "  $1"
  print_color "1;34" "========================================================\n"
  log_message "$1"
}

check_gcloud() {
  if ! command -v gcloud &> /dev/null; then
    print_color "1;31" "ERROR: gcloud CLI not found. Please install the Google Cloud SDK."
    exit 1
  fi
  
  log_message "Checking gcloud authentication..."
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_color "1;31" "ERROR: Not authenticated with gcloud. Please run 'gcloud auth login'."
    exit 1
  fi
}

create_archive() {
  print_header "Creating archive: ${ARCHIVE_NAME}"
  
  log_message "Starting archive creation from: ${WORKSPACE_DIR}"
  
  # Create the archive
  tar -czf "${ARCHIVE_NAME}" \
    "${EXCLUDE_PATTERNS[@]}" \
    --exclude="${ARCHIVE_NAME}" \
    -C "${WORKSPACE_DIR}" .
  
  ARCHIVE_SIZE=$(du -h "${ARCHIVE_NAME}" | cut -f1)
  log_message "Archive created successfully: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})"
  print_color "1;32" "✓ Archive created successfully: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})"
}

upload_to_gcs() {
  print_header "Uploading archive to Google Cloud Storage"
  
  log_message "Uploading to bucket: ${GCS_BUCKET}"
  
  # Upload to GCS with parallel composite uploads and checksumming
  gsutil -o GSUtil:parallel_composite_upload_threshold=150M \
    cp "${ARCHIVE_NAME}" "${GCS_BUCKET}/"
  
  # Verify the upload was successful
  if gsutil stat "${GCS_BUCKET}/${ARCHIVE_NAME}" &> /dev/null; then
    GCS_URL="${GCS_BUCKET}/${ARCHIVE_NAME}"
    log_message "Upload successful: ${GCS_URL}"
    print_color "1;32" "✓ Upload successful: ${GCS_URL}"
  else
    log_message "ERROR: Upload failed or file not found in bucket"
    print_color "1;31" "ERROR: Upload failed or file not found in bucket"
    exit 1
  fi
}

create_metadata() {
  print_header "Creating migration metadata"
  
  local METADATA_FILE="migration_metadata_${TIMESTAMP}.json"
  
  # Get file listing for the metadata
  find "${WORKSPACE_DIR}" -type f -not -path "*/\.*" -not -path "*/venv/*" \
    -not -path "*/__pycache__/*" -not -path "*/node_modules/*" | sort > file_listing.txt
  
  # Create metadata JSON
  cat > "${METADATA_FILE}" << EOF
{
  "archive_name": "${ARCHIVE_NAME}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "archive_size_bytes": $(stat -c%s "${ARCHIVE_NAME}"),
  "storage_location": "${GCS_BUCKET}/${ARCHIVE_NAME}",
  "file_count": $(wc -l < file_listing.txt),
  "workspace_directory": "${WORKSPACE_DIR}",
  "excluded_patterns": [
    ".git",
    "__pycache__",
    "*.pyc",
    "venv",
    ".venv",
    "node_modules",
    ".env",
    "*.log",
    "*.tar.gz"
  ]
}
EOF

  # Upload metadata to GCS
  gsutil cp "${METADATA_FILE}" "${GCS_BUCKET}/"
  
  log_message "Metadata file created and uploaded: ${METADATA_FILE}"
  print_color "1;32" "✓ Metadata file created and uploaded: ${GCS_BUCKET}/${METADATA_FILE}"
  
  # Clean up
  rm file_listing.txt
}

print_restoration_instructions() {
  print_header "Restoration Instructions"
  
  cat << EOF
=== GCP WORKSPACE MIGRATION RESTORATION GUIDE ===

Your workspace has been archived to: ${GCS_BUCKET}/${ARCHIVE_NAME}

To restore in a new Vertex AI Workbench instance or Google Cloud Workstation, follow these steps:

1) Download the archive:
   gsutil cp ${GCS_BUCKET}/${ARCHIVE_NAME} .

2) Extract the archive:
   tar -xzf ${ARCHIVE_NAME}

3) Set permissions (if needed):
   find . -type f -name "*.sh" -exec chmod +x {} \;

4) Download the metadata file for reference:
   gsutil cp ${GCS_BUCKET}/migration_metadata_${TIMESTAMP}.json .

Additional Information:
- Archive Size: ${ARCHIVE_SIZE}
- Creation Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- Log File: ${LOG_FILE}

EOF

  log_message "Printed restoration instructions"
}

# Main execution
main() {
  print_color "1;35" "=== GCP WORKSPACE MIGRATION UTILITY ==="
  
  # Check for gcloud
  check_gcloud
  
  # Create the archive
  create_archive
  
  # Upload to GCS
  upload_to_gcs
  
  # Create and upload metadata
  create_metadata
  
  # Print restoration instructions
  print_restoration_instructions
  
  print_color "1;35" "Migration completed successfully!"
}

# Run the script
main

#!/bin/bash
# gcp_archive_restore.sh - Restore archived workspace from Google Cloud Storage
# 
# This script downloads and extracts an archived workspace from a GCS bucket
# to a new Vertex AI Workbench instance or Google Cloud Workstation.

set -e

# Print colored output
print_color() {
  local color_code="$1"
  local message="$2"
  echo -e "\033[${color_code}m${message}\033[0m"
}

print_header() {
  print_color "1;34" "\n========================================================"
  print_color "1;34" "  $1"
  print_color "1;34" "========================================================\n"
}

# Function to show usage instructions
show_usage() {
  cat << EOF
Usage: $0 [options]

Options:
  -b, --bucket       GCS bucket URL (required, e.g. gs://agi-baby-cherry-migration)
  -a, --archive      Archive filename (required, e.g. orchestra_migration_20250501_123456.tar.gz)
  -d, --directory    Destination directory (optional, defaults to current directory)
  -h, --help         Show this help message

Example:
  $0 --bucket gs://agi-baby-cherry-migration --archive orchestra_migration_20250501_123456.tar.gz
EOF
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -b|--bucket)
        GCS_BUCKET="$2"
        shift 2
        ;;
      -a|--archive)
        ARCHIVE_NAME="$2"
        shift 2
        ;;
      -d|--directory)
        DEST_DIR="$2"
        shift 2
        ;;
      -h|--help)
        show_usage
        exit 0
        ;;
      *)
        print_color "1;31" "Error: Unknown option $1"
        show_usage
        exit 1
        ;;
    esac
  done

  # Check required arguments
  if [[ -z "${GCS_BUCKET}" ]]; then
    print_color "1;31" "Error: GCS bucket URL is required"
    show_usage
    exit 1
  fi

  if [[ -z "${ARCHIVE_NAME}" ]]; then
    print_color "1;31" "Error: Archive filename is required"
    show_usage
    exit 1
  fi

  # Set destination directory to current directory if not specified
  if [[ -z "${DEST_DIR}" ]]; then
    DEST_DIR="$(pwd)"
  fi
}

check_gcloud() {
  if ! command -v gcloud &> /dev/null; then
    print_color "1;31" "ERROR: gcloud CLI not found. Please install the Google Cloud SDK."
    exit 1
  fi
  
  print_color "1;36" "Checking gcloud authentication..."
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_color "1;31" "ERROR: Not authenticated with gcloud. Please run 'gcloud auth login'."
    exit 1
  fi
}

download_archive() {
  print_header "Downloading archive from GCS"
  
  # Check if archive exists in the bucket
  if ! gsutil -q stat "${GCS_BUCKET}/${ARCHIVE_NAME}" &> /dev/null; then
    print_color "1;31" "ERROR: Archive not found in bucket: ${GCS_BUCKET}/${ARCHIVE_NAME}"
    exit 1
  fi
  
  print_color "1;36" "Downloading: ${GCS_BUCKET}/${ARCHIVE_NAME}"
  
  # Download the archive with progress indication
  gsutil -m cp "${GCS_BUCKET}/${ARCHIVE_NAME}" "${DEST_DIR}/"
  
  if [[ -f "${DEST_DIR}/${ARCHIVE_NAME}" ]]; then
    ARCHIVE_SIZE=$(du -h "${DEST_DIR}/${ARCHIVE_NAME}" | cut -f1)
    print_color "1;32" "✓ Download successful: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})"
  else
    print_color "1;31" "ERROR: Download failed"
    exit 1
  fi
}

download_metadata() {
  print_header "Downloading metadata"
  
  # Extract timestamp from archive name
  local TIMESTAMP=$(echo "${ARCHIVE_NAME}" | grep -o "[0-9]\{8\}_[0-9]\{6\}")
  
  if [[ -n "${TIMESTAMP}" ]]; then
    local METADATA_FILE="migration_metadata_${TIMESTAMP}.json"
    
    if gsutil -q stat "${GCS_BUCKET}/${METADATA_FILE}" &> /dev/null; then
      print_color "1;36" "Downloading metadata: ${METADATA_FILE}"
      gsutil cp "${GCS_BUCKET}/${METADATA_FILE}" "${DEST_DIR}/"
      print_color "1;32" "✓ Metadata downloaded successfully"
    else
      print_color "1;33" "Warning: Metadata file not found (${METADATA_FILE})"
    fi
  else
    print_color "1;33" "Warning: Could not determine metadata filename from archive name"
  fi
}

extract_archive() {
  print_header "Extracting archive"
  
  cd "${DEST_DIR}"
  
  print_color "1;36" "Extracting: ${ARCHIVE_NAME}"
  tar -xzf "${ARCHIVE_NAME}"
  
  if [[ $? -eq 0 ]]; then
    print_color "1;32" "✓ Archive extracted successfully"
  else
    print_color "1;31" "ERROR: Archive extraction failed"
    exit 1
  fi
}

set_permissions() {
  print_header "Setting file permissions"
  
  print_color "1;36" "Making shell scripts executable..."
  find "${DEST_DIR}" -type f -name "*.sh" -exec chmod +x {} \;
  
  print_color "1;32" "✓ Permissions set successfully"
}

verify_restoration() {
  print_header "Verifying restoration"
  
  local TOTAL_FILES=$(find "${DEST_DIR}" -type f -not -path "*/\.*" -not -path "${DEST_DIR}/${ARCHIVE_NAME}" | wc -l)
  
  print_color "1;36" "Total files restored: ${TOTAL_FILES}"
  
  # Check for essential directories and files
  local ESSENTIAL_DIRS=("agent" "core" "scripts" "docs" "packages")
  local MISSING_DIRS=()
  
  for dir in "${ESSENTIAL_DIRS[@]}"; do
    if [[ ! -d "${DEST_DIR}/${dir}" ]]; then
      MISSING_DIRS+=("${dir}")
    fi
  done
  
  if [[ ${#MISSING_DIRS[@]} -eq 0 ]]; then
    print_color "1;32" "✓ All essential directories present"
  else
    print_color "1;33" "Warning: Some expected directories are missing:"
    for dir in "${MISSING_DIRS[@]}"; do
      print_color "1;33" "  - ${dir}"
    done
  fi
}

# Main execution
main() {
  print_color "1;35" "=== GCP WORKSPACE RESTORATION UTILITY ==="
  
  # Parse command line arguments
  parse_args "$@"
  
  # Check for gcloud
  check_gcloud
  
  # Download the archive
  download_archive
  
  # Download metadata if available
  download_metadata
  
  # Extract the archive
  extract_archive
  
  # Set file permissions
  set_permissions
  
  # Verify the restoration
  verify_restoration
  
  print_color "1;35" "Restoration completed successfully!"
  print_color "1;32" "Your workspace has been restored to: ${DEST_DIR}"
}

# Run the script with all provided arguments
main "$@"

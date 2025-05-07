#!/bin/bash
# vertex_data_sync.sh - Automated bidirectional sync between Jupyter and GCS
#
# This script provides automated data transfer between Vertex Workbench
# and Google Cloud Storage with incremental sync and data integrity validation.
#
# Usage:
#   ./vertex_data_sync.sh [--push|--pull] [--bucket BUCKET_NAME] [--verify-only]
#
# Examples:
#   ./vertex_data_sync.sh --push                  # Push to GCS
#   ./vertex_data_sync.sh --pull                  # Pull from GCS
#   ./vertex_data_sync.sh --verify-only           # Only verify data integrity
#   ./vertex_data_sync.sh --push --bucket my-bucket  # Specify bucket

set -e

# Default configuration
BUCKET="${BUCKET:-cherry-ai-project-migration}"
LOCAL_DIR="/home/jupyter"
REMOTE_DIR="migrations/$(date +%Y%m%d)"
LATEST_SYMLINK="migrations/latest"
LOG_DIR="${LOCAL_DIR}/logs"
CHECKSUM_FILE="transfer_checksums.md5"
EXCLUDE_PATTERNS=(".git" "__pycache__" "*.pyc" "venv" ".venv" "node_modules" ".env" "*.log" "*.tar.gz")
OPERATION=""
VERIFY_ONLY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
print_color() {
  local color_code="$1"
  local message="$2"
  echo -e "${color_code}${message}${NC}"
}

print_header() {
  print_color "${BLUE}" "\n========================================================"
  print_color "${BLUE}" "  $1"
  print_color "${BLUE}" "========================================================\n"
}

log_message() {
  local message="$1"
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  
  # Create log directory if it doesn't exist
  mkdir -p "${LOG_DIR}"
  
  echo "[${timestamp}] ${message}" | tee -a "${LOG_DIR}/sync_$(date +%Y%m%d).log"
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --push)
        OPERATION="push"
        shift
        ;;
      --pull)
        OPERATION="pull"
        shift
        ;;
      --bucket)
        BUCKET="$2"
        shift 2
        ;;
      --verify-only)
        VERIFY_ONLY=true
        shift
        ;;
      --help)
        show_usage
        exit 0
        ;;
      *)
        print_color "${RED}" "Error: Unknown option $1"
        show_usage
        exit 1
        ;;
    esac
  done

  # If no operation specified and not verify-only, show usage
  if [[ -z "${OPERATION}" && "${VERIFY_ONLY}" == "false" ]]; then
    print_color "${RED}" "Error: No operation specified (--push or --pull)"
    show_usage
    exit 1
  fi
}

# Function to show usage instructions
show_usage() {
  cat << EOF
Usage: $0 [options]

Options:
  --push            Push local Jupyter files to GCS bucket
  --pull            Pull files from GCS bucket to local Jupyter
  --bucket NAME     Specify the GCS bucket name (default: ${BUCKET})
  --verify-only     Only verify data integrity without transferring files
  --help            Show this help message

Examples:
  $0 --push                      # Push changes to GCS
  $0 --pull                      # Pull changes from GCS
  $0 --push --bucket my-bucket   # Use specific bucket
  $0 --verify-only               # Verify data integrity only
EOF
}

# Check if gsutil is installed and authenticated
check_gsutil() {
  log_message "Checking gsutil installation and authentication"
  
  if ! command -v gsutil &> /dev/null; then
    log_message "ERROR: gsutil not found"
    print_color "${RED}" "ERROR: gsutil not found. Please install the Google Cloud SDK."
    exit 1
  fi
  
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    log_message "ERROR: Not authenticated with gcloud"
    print_color "${RED}" "ERROR: Not authenticated with gcloud. Please run 'gcloud auth login'."
    exit 1
  fi
  
  # Check if bucket exists
  if ! gsutil ls -b "gs://${BUCKET}" &> /dev/null; then
    log_message "ERROR: Bucket gs://${BUCKET} does not exist or is not accessible"
    print_color "${RED}" "ERROR: Bucket gs://${BUCKET} does not exist or is not accessible."
    exit 1
  fi
  
  log_message "gsutil checks passed"
}

# Build exclude arguments for rsync
build_exclude_args() {
  local exclude_args=""
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    exclude_args="${exclude_args} -x '${pattern}'"
  done
  echo "${exclude_args}"
}

# Generate checksums for local files
generate_local_checksums() {
  print_header "Generating checksums for local files"
  log_message "Generating checksums for local files"
  
  # Create temporary directory for checksums
  mkdir -p "${LOCAL_DIR}/.checksums"
  
  # Find all files excluding patterns and generate md5 checksums
  find "${LOCAL_DIR}" -type f \
    $(printf "! -path \"${LOCAL_DIR}/*%s*\" " "${EXCLUDE_PATTERNS[@]}") \
    -not -path "${LOCAL_DIR}/.checksums/*" \
    | sort | xargs md5sum > "${LOCAL_DIR}/.checksums/${CHECKSUM_FILE}"
  
  log_message "Checksums generated: ${LOCAL_DIR}/.checksums/${CHECKSUM_FILE}"
  print_color "${GREEN}" "✓ Local checksums generated successfully"
}

# Push data to GCS
sync_to_gcs() {
  print_header "Pushing data to Google Cloud Storage"
  log_message "Starting push to gs://${BUCKET}/${REMOTE_DIR}/"
  
  # Generate checksums before transfer
  generate_local_checksums
  
  # Build exclude arguments
  local exclude_args=$(build_exclude_args)
  
  # Create rsync command
  local rsync_cmd="gsutil -m rsync -r ${exclude_args} \"${LOCAL_DIR}\" \"gs://${BUCKET}/${REMOTE_DIR}/\""
  
  # Execute rsync command
  log_message "Executing: ${rsync_cmd}"
  eval ${rsync_cmd}
  
  # Upload checksum file
  gsutil cp "${LOCAL_DIR}/.checksums/${CHECKSUM_FILE}" "gs://${BUCKET}/${REMOTE_DIR}/.checksums/"
  
  log_message "Push completed successfully"
  print_color "${GREEN}" "✓ Data pushed to gs://${BUCKET}/${REMOTE_DIR}/"
  
  # Update latest symlink
  create_latest_symlink
}

# Pull data from GCS
sync_from_gcs() {
  print_header "Pulling data from Google Cloud Storage"
  log_message "Starting pull from gs://${BUCKET}/${LATEST_SYMLINK}/"
  
  # Check if remote directory exists
  if ! gsutil ls "gs://${BUCKET}/${LATEST_SYMLINK}/" &> /dev/null; then
    log_message "ERROR: Remote directory gs://${BUCKET}/${LATEST_SYMLINK}/ does not exist"
    print_color "${RED}" "ERROR: Remote directory gs://${BUCKET}/${LATEST_SYMLINK}/ does not exist."
    exit 1
  fi
  
  # Build exclude arguments
  local exclude_args=$(build_exclude_args)
  
  # Create rsync command
  local rsync_cmd="gsutil -m rsync -r ${exclude_args} \"gs://${BUCKET}/${LATEST_SYMLINK}/\" \"${LOCAL_DIR}\""
  
  # Execute rsync command
  log_message "Executing: ${rsync_cmd}"
  eval ${rsync_cmd}
  
  # Download checksum file
  mkdir -p "${LOCAL_DIR}/.checksums"
  gsutil cp "gs://${BUCKET}/${LATEST_SYMLINK}/.checksums/${CHECKSUM_FILE}" "${LOCAL_DIR}/.checksums/remote_${CHECKSUM_FILE}"
  
  log_message "Pull completed successfully"
  print_color "${GREEN}" "✓ Data pulled from gs://${BUCKET}/${LATEST_SYMLINK}/"
}

# Create/update the "latest" symlink
create_latest_symlink() {
  print_header "Updating latest symlink"
  log_message "Updating latest symlink to point to ${REMOTE_DIR}"
  
  # Copy all files from current remote dir to latest
  gsutil -m rsync -r "gs://${BUCKET}/${REMOTE_DIR}/" "gs://${BUCKET}/${LATEST_SYMLINK}/"
  
  log_message "Latest symlink updated successfully"
  print_color "${GREEN}" "✓ Latest symlink updated to point to ${REMOTE_DIR}"
}

# Verify data integrity using checksums
verify_integrity() {
  print_header "Verifying data integrity"
  log_message "Starting data integrity verification"
  
  local remote_checksum_file="${LOCAL_DIR}/.checksums/remote_${CHECKSUM_FILE}"
  local local_checksum_file="${LOCAL_DIR}/.checksums/${CHECKSUM_FILE}"
  local diff_file="${LOCAL_DIR}/.checksums/diff_$(date +%Y%m%d_%H%M%S).txt"
  
  # Download remote checksums if they don't exist locally
  if [[ ! -f "${remote_checksum_file}" ]]; then
    mkdir -p "${LOCAL_DIR}/.checksums"
    if gsutil ls "gs://${BUCKET}/${LATEST_SYMLINK}/.checksums/${CHECKSUM_FILE}" &> /dev/null; then
      log_message "Downloading remote checksums"
      gsutil cp "gs://${BUCKET}/${LATEST_SYMLINK}/.checksums/${CHECKSUM_FILE}" "${remote_checksum_file}"
    else
      log_message "ERROR: Remote checksum file not found"
      print_color "${RED}" "ERROR: Remote checksum file not found. Cannot verify integrity."
      return 1
    fi
  fi
  
  # Generate local checksums if they don't exist
  if [[ ! -f "${local_checksum_file}" ]]; then
    generate_local_checksums
  fi
  
  # Compare checksums
  log_message "Comparing checksums"
  diff "${remote_checksum_file}" "${local_checksum_file}" > "${diff_file}" || true
  
  if [[ -s "${diff_file}" ]]; then
    log_message "WARNING: Data integrity issues detected. See ${diff_file}"
    print_color "${YELLOW}" "⚠ WARNING: Data integrity issues detected."
    print_color "${YELLOW}" "  Differences found. See ${diff_file} for details."
    
    # Count number of differences
    local diff_count=$(grep -c "^[<>]" "${diff_file}")
    print_color "${YELLOW}" "  ${diff_count} differences found."
    
    # Display sample of differences
    print_color "${YELLOW}" "  Sample of differences:"
    head -n 10 "${diff_file}" | grep "^[<>]" | while read -r line; do
      print_color "${YELLOW}" "    ${line}"
    done
    
    return 1
  else
    log_message "Data integrity verified successfully"
    print_color "${GREEN}" "✓ Data integrity verified successfully. No differences found."
    return 0
  fi
}

# Main execution
main() {
  print_color "${PURPLE}" "=== VERTEX WORKBENCH DATA SYNC UTILITY ==="
  
  # Parse command line arguments
  parse_args "$@"
  
  # Check gsutil is installed and authenticated
  check_gsutil
  
  # Perform the requested operation
  if [[ "${VERIFY_ONLY}" == "true" ]]; then
    verify_integrity
  else
    case "${OPERATION}" in
      "push")
        sync_to_gcs
        verify_integrity
        ;;
      "pull")
        sync_from_gcs
        verify_integrity
        ;;
    esac
  fi
  
  print_color "${PURPLE}" "=== OPERATION COMPLETED SUCCESSFULLY ==="
}

# Run the script with all provided arguments
main "$@"

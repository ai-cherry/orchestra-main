#!/bin/bash
#
# GCP Resource Snapshot Script
# This script captures a comprehensive inventory of GCP resources and enabled services
# in a project, which can be compared against local code implementations.

set -e  # Exit on error

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default output directory
OUTPUT_DIR="./gcp_snapshots"
DATE_STR=$(date +"%Y-%m-%d-%H%M%S")
PROJECT_ID=""
SNAPSHOT_ALL=false
COMPARE_WITH_CODE=false
CODE_DIR="."

# Helper functions
print_header() {
  echo -e "\n${BLUE}====== $1 ======${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project-id PROJECT_ID    GCP Project ID (required)"
  echo "  -o, --output-dir DIR           Output directory for snapshots (default: ./gcp_snapshots)"
  echo "  -a, --all                      Capture all resources (more comprehensive but slower)"
  echo "  -c, --compare                  Compare snapshot with code in specified directory"
  echo "  -d, --code-dir DIR             Directory containing code to compare (default: .)"
  echo "  -h, --help                     Show this help message"
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    -o|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -a|--all)
      SNAPSHOT_ALL=true
      shift
      ;;
    -c|--compare)
      COMPARE_WITH_CODE=true
      shift
      ;;
    -d|--code-dir)
      CODE_DIR="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      ;;
    *)
      print_error "Unknown option: $1"
      show_usage
      ;;
  esac
done

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
  print_error "Project ID is required. Use -p or --project-id to specify."
  show_usage
fi

# Create output directory structure
SNAPSHOT_DIR="${OUTPUT_DIR}/${PROJECT_ID}_${DATE_STR}"
mkdir -p "${SNAPSHOT_DIR}/services"
mkdir -p "${SNAPSHOT_DIR}/resources"
mkdir -p "${SNAPSHOT_DIR}/iam"
mkdir -p "${SNAPSHOT_DIR}/compute"
mkdir -p "${SNAPSHOT_DIR}/storage"
mkdir -p "${SNAPSHOT_DIR}/databases"
mkdir -p "${SNAPSHOT_DIR}/ai"
mkdir -p "${SNAPSHOT_DIR}/networking"

print_header "GCP Resource Snapshot Tool"
print_info "Creating snapshot for project: ${PROJECT_ID}"
print_info "Output directory: ${SNAPSHOT_DIR}"

# Verify gcloud installation and authentication
print_header "Verifying gcloud setup"
if ! command -v gcloud &> /dev/null; then
  print_error "gcloud CLI not found. Please install Google Cloud SDK."
  exit 1
fi

# Check current authentication
print_info "Checking authentication..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$CURRENT_ACCOUNT" ]; then
  print_error "Not authenticated with gcloud. Please run 'gcloud auth login' or set up service account credentials."
  exit 1
else
  print_success "Authenticated as: $CURRENT_ACCOUNT"
fi

# Verify project exists and is accessible
print_info "Verifying project access..."
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
  print_error "Project $PROJECT_ID not found or not accessible with current credentials."
  exit 1
fi
print_success "Project $PROJECT_ID is accessible"

# Set the current project
gcloud config set project "$PROJECT_ID"
print_info "Set active project to: $PROJECT_ID"

# Create a metadata file
cat > "${SNAPSHOT_DIR}/metadata.json" << EOF
{
  "project_id": "${PROJECT_ID}",
  "snapshot_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "created_by": "${CURRENT_ACCOUNT}",
  "snapshot_type": "$(if $SNAPSHOT_ALL; then echo "comprehensive"; else echo "standard"; fi)"
}
EOF

# Snapshot enabled services
print_header "Capturing enabled API services"
gcloud services list --format=json > "${SNAPSHOT_DIR}/services/enabled_apis.json"
print_success "Captured $(jq length "${SNAPSHOT_DIR}/services/enabled_apis.json") enabled API services"

# Extract just the service names for easier reference
jq -r '.[].config.name' "${SNAPSHOT_DIR}/services/enabled_apis.json" > "${SNAPSHOT_DIR}/services/enabled_apis_list.txt"

# Snapshot IAM policies and service accounts
print_header "Capturing IAM configuration"
gcloud projects get-iam-policy "$PROJECT_ID" --format=json > "${SNAPSHOT_DIR}/iam/project_iam_policy.json"
gcloud iam service-accounts list --format=json > "${SNAPSHOT_DIR}/iam/service_accounts.json"
print_success "Captured IAM policies and service accounts"

# Snapshot Compute Engine resources
print_header "Capturing Compute Engine resources"
gcloud compute instances list --format=json > "${SNAPSHOT_DIR}/compute/instances.json"
gcloud compute instance-groups list --format=json > "${SNAPSHOT_DIR}/compute/instance_groups.json"
gcloud compute machine-types list --format=json > "${SNAPSHOT_DIR}/compute/machine_types.json"
print_success "Captured Compute Engine resources"

# Snapshot Cloud Run services
print_header "Capturing Cloud Run services"
gcloud run services list --format=json > "${SNAPSHOT_DIR}/compute/cloud_run_services.json"
print_success "Captured Cloud Run services"

# Snapshot Storage resources
print_header "Capturing Storage resources"
gcloud storage ls --format=json > "${SNAPSHOT_DIR}/storage/buckets.json"
print_success "Captured Storage resources"

# Snapshot database resources
print_header "Capturing Database resources"
gcloud sql instances list --format=json > "${SNAPSHOT_DIR}/databases/cloud_sql.json"
gcloud firestore indexes list --format=json > "${SNAPSHOT_DIR}/databases/firestore_indexes.json"
print_success "Captured Database resources"

# Snapshot AI resources
print_header "Capturing AI resources"
gcloud ai models list --region=global --format=json > "${SNAPSHOT_DIR}/ai/vertex_ai_models.json"
gcloud ai endpoints list --region=global --format=json > "${SNAPSHOT_DIR}/ai/vertex_ai_endpoints.json"
print_success "Captured AI resources"

# Snapshot networking resources
print_header "Capturing Networking resources"
gcloud compute networks list --format=json > "${SNAPSHOT_DIR}/networking/networks.json"
gcloud compute firewall-rules list --format=json > "${SNAPSHOT_DIR}/networking/firewall_rules.json"
print_success "Captured Networking resources"

# If comprehensive snapshot requested, get more detailed information
if $SNAPSHOT_ALL; then
  print_header "Capturing comprehensive resource details (this may take some time)"

  # Get detailed information about each Cloud Run service
  mkdir -p "${SNAPSHOT_DIR}/compute/cloud_run_details"
  if [ -s "${SNAPSHOT_DIR}/compute/cloud_run_services.json" ]; then
    SERVICES=$(jq -r '.[].metadata.name' "${SNAPSHOT_DIR}/compute/cloud_run_services.json" 2>/dev/null || echo "")
    for SERVICE in $SERVICES; do
      print_info "Getting details for Cloud Run service: $SERVICE"
      gcloud run services describe "$SERVICE" --format=json > "${SNAPSHOT_DIR}/compute/cloud_run_details/${SERVICE}.json"
    done
  fi

  # Get detailed IAM policies for each service account
  mkdir -p "${SNAPSHOT_DIR}/iam/service_account_details"
  if [ -s "${SNAPSHOT_DIR}/iam/service_accounts.json" ]; then
    SA_EMAILS=$(jq -r '.[].email' "${SNAPSHOT_DIR}/iam/service_accounts.json" 2>/dev/null || echo "")
    for SA_EMAIL in $SA_EMAILS; do
      print_info "Getting IAM policy for service account: $SA_EMAIL"
      gcloud iam service-accounts get-iam-policy "$SA_EMAIL" --format=json > "${SNAPSHOT_DIR}/iam/service_account_details/${SA_EMAIL//[@.]/_}.json"
    done
  fi

  print_success "Captured comprehensive resource details"
fi

# Create a summary file
print_header "Generating resource summary"
SUMMARY_FILE="${SNAPSHOT_DIR}/resource_summary.md"

cat > "$SUMMARY_FILE" << EOF
# Google Cloud Resource Snapshot Summary
**Project:** ${PROJECT_ID}  
**Snapshot Date:** $(date)  
**Created By:** ${CURRENT_ACCOUNT}  

## Enabled Services
$(if [ -s "${SNAPSHOT_DIR}/services/enabled_apis_list.txt" ]; then
  echo "Total: $(wc -l < "${SNAPSHOT_DIR}/services/enabled_apis_list.txt") enabled APIs"
  echo "\`\`\`"
  cat "${SNAPSHOT_DIR}/services/enabled_apis_list.txt"
  echo "\`\`\`"
else
  echo "No enabled services found."
fi)

## Compute Resources
- **VM Instances:** $(jq 'length' "${SNAPSHOT_DIR}/compute/instances.json" 2>/dev/null || echo "0")
- **Instance Groups:** $(jq 'length' "${SNAPSHOT_DIR}/compute/instance_groups.json" 2>/dev/null || echo "0")
- **Cloud Run Services:** $(jq 'length' "${SNAPSHOT_DIR}/compute/cloud_run_services.json" 2>/dev/null || echo "0")

## Storage Resources
- **Cloud Storage Buckets:** $(jq 'length' "${SNAPSHOT_DIR}/storage/buckets.json" 2>/dev/null || echo "0")

## Database Resources
- **Cloud SQL Instances:** $(jq 'length' "${SNAPSHOT_DIR}/databases/cloud_sql.json" 2>/dev/null || echo "0")
- **Firestore Indexes:** $(jq 'length' "${SNAPSHOT_DIR}/databases/firestore_indexes.json" 2>/dev/null || echo "0")

## AI Resources
- **Vertex AI Models:** $(jq 'length' "${SNAPSHOT_DIR}/ai/vertex_ai_models.json" 2>/dev/null || echo "0")
- **Vertex AI Endpoints:** $(jq 'length' "${SNAPSHOT_DIR}/ai/vertex_ai_endpoints.json" 2>/dev/null || echo "0")

## IAM Resources
- **Service Accounts:** $(jq 'length' "${SNAPSHOT_DIR}/iam/service_accounts.json" 2>/dev/null || echo "0")

## Networking Resources
- **VPC Networks:** $(jq 'length' "${SNAPSHOT_DIR}/networking/networks.json" 2>/dev/null || echo "0")
- **Firewall Rules:** $(jq 'length' "${SNAPSHOT_DIR}/networking/firewall_rules.json" 2>/dev/null || echo "0")
EOF

print_success "Generated resource summary at ${SUMMARY_FILE}"

# If code comparison requested, do simple analysis
if $COMPARE_WITH_CODE; then
  print_header "Comparing with code in ${CODE_DIR}"
  COMPARISON_FILE="${SNAPSHOT_DIR}/code_comparison.md"
  
  cat > "$COMPARISON_FILE" << EOF
# Code vs. GCP Resources Comparison
**Project:** ${PROJECT_ID}  
**Code Directory:** ${CODE_DIR}  
**Comparison Date:** $(date)  

## API Services Check
Checking whether services enabled in GCP are referenced in code:

| Service | Found in Code | Files |
|---------|---------------|-------|
EOF

  # Compare API services with code references
  if [ -s "${SNAPSHOT_DIR}/services/enabled_apis_list.txt" ]; then
    while read -r SERVICE; do
      # Get the service name without googleapis.com
      SERVICE_NAME=$(echo "$SERVICE" | sed 's/\.googleapis\.com$//')
      
      # Search for this service in the code files
      FILES=$(grep -l "$SERVICE_NAME" "${CODE_DIR}" --include="*.{js,py,ts,tsx,jsx,java,go,html,yml,yaml,tf,json}" 2>/dev/null | head -5)
      
      if [ -n "$FILES" ]; then
        echo "| $SERVICE | ✅ | $(echo "$FILES" | tr '\n' ', ' | sed 's/,$//')" >> "$COMPARISON_FILE"
      else
        echo "| $SERVICE | ❌ | " >> "$COMPARISON_FILE"
      fi
    done < "${SNAPSHOT_DIR}/services/enabled_apis_list.txt"
  fi

  # Compare Cloud Run services with code references
  cat >> "$COMPARISON_FILE" << EOF

## Cloud Run Services Check
Checking whether Cloud Run services defined in GCP are referenced in code:

| Service | Found in Code | Files |
|---------|---------------|-------|
EOF

  if [ -s "${SNAPSHOT_DIR}/compute/cloud_run_services.json" ]; then
    SERVICES=$(jq -r '.[].metadata.name' "${SNAPSHOT_DIR}/compute/cloud_run_services.json" 2>/dev/null || echo "")
    for SERVICE in $SERVICES; do
      # Search for this service name in the code files
      FILES=$(grep -l "$SERVICE" "${CODE_DIR}" --include="*.{js,py,ts,tsx,jsx,java,go,html,yml,yaml,tf,json}" 2>/dev/null | head -5)
      
      if [ -n "$FILES" ]; then
        echo "| $SERVICE | ✅ | $(echo "$FILES" | tr '\n' ', ' | sed 's/,$//')" >> "$COMPARISON_FILE"
      else
        echo "| $SERVICE | ❌ | " >> "$COMPARISON_FILE"
      fi
    done
  fi

  # Compare Storage buckets with code references
  cat >> "$COMPARISON_FILE" << EOF

## Storage Buckets Check
Checking whether Storage buckets defined in GCP are referenced in code:

| Bucket | Found in Code | Files |
|--------|---------------|-------|
EOF

  if [ -s "${SNAPSHOT_DIR}/storage/buckets.json" ]; then
    BUCKETS=$(jq -r '.[].url' "${SNAPSHOT_DIR}/storage/buckets.json" 2>/dev/null | sed 's|gs://||' || echo "")
    for BUCKET in $BUCKETS; do
      # Search for this bucket name in the code files
      FILES=$(grep -l "$BUCKET" "${CODE_DIR}" --include="*.{js,py,ts,tsx,jsx,java,go,html,yml,yaml,tf,json}" 2>/dev/null | head -5)
      
      if [ -n "$FILES" ]; then
        echo "| $BUCKET | ✅ | $(echo "$FILES" | tr '\n' ', ' | sed 's/,$//')" >> "$COMPARISON_FILE"
      else
        echo "| $BUCKET | ❌ | " >> "$COMPARISON_FILE"
      fi
    done
  fi

  # Add summary and recommendations
  cat >> "$COMPARISON_FILE" << EOF

## Summary and Recommendations

### Potentially Unused Services
The following services are enabled in GCP but were not found referenced in the code:
$(if [ -s "${SNAPSHOT_DIR}/services/enabled_apis_list.txt" ]; then
  while read -r SERVICE; do
    SERVICE_NAME=$(echo "$SERVICE" | sed 's/\.googleapis\.com$//')
    if ! grep -q "$SERVICE_NAME" "${CODE_DIR}" --include="*.{js,py,ts,tsx,jsx,java,go,html,yml,yaml,tf,json}" 2>/dev/null; then
      echo "- $SERVICE"
    fi
  done < "${SNAPSHOT_DIR}/services/enabled_apis_list.txt"
else
  echo "No services to analyze."
fi)

### Potential Infrastructure as Code Updates Needed
The following resources exist in GCP but may not be properly defined in your infrastructure code:
EOF

  # Check for Cloud Run services not in Terraform files
  if [ -s "${SNAPSHOT_DIR}/compute/cloud_run_services.json" ]; then
    SERVICES=$(jq -r '.[].metadata.name' "${SNAPSHOT_DIR}/compute/cloud_run_services.json" 2>/dev/null || echo "")
    for SERVICE in $SERVICES; do
      if ! grep -q "$SERVICE" "${CODE_DIR}" --include="*.tf" 2>/dev/null; then
        echo "- Cloud Run service '$SERVICE' may not be defined in Terraform" >> "$COMPARISON_FILE"
      fi
    done
  fi

  print_success "Generated code comparison at ${COMPARISON_FILE}"
fi

# Create an archive of all snapshots
print_header "Creating snapshot archive"
ARCHIVE_FILE="${OUTPUT_DIR}/${PROJECT_ID}_${DATE_STR}.tar.gz"
tar -czf "$ARCHIVE_FILE" -C "$OUTPUT_DIR" "${PROJECT_ID}_${DATE_STR}"
print_success "Created snapshot archive at ${ARCHIVE_FILE}"

print_header "GCP Resource Snapshot Complete"
print_info "Snapshot directory: ${SNAPSHOT_DIR}"
print_info "Snapshot archive: ${ARCHIVE_FILE}"
print_info "Summary file: ${SUMMARY_FILE}"
if $COMPARE_WITH_CODE; then
  print_info "Code comparison file: ${COMPARISON_FILE}"
fi
print_success "All done!"

# Usage directions
echo
print_info "To use this snapshot with Gemini Code Assist:"
echo "1. Open the summary file for a quick overview: ${SUMMARY_FILE}"
echo "2. Place the snapshot directory in a location indexed by Gemini Code Assist"
echo "3. When asking Gemini questions, refer to the snapshot files for current GCP configuration"
echo
print_info "Example Gemini prompts:"
echo "- \"Generate Terraform for a new Cloud Run service based on our existing services in ${SNAPSHOT_DIR}/compute/cloud_run_services.json\""
echo "- \"Compare our current firewall rules in ${SNAPSHOT_DIR}/networking/firewall_rules.json with best practices\""
echo "- \"Help me optimize our IAM roles based on ${SNAPSHOT_DIR}/iam/project_iam_policy.json\""

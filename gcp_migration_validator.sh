#!/bin/bash
# gcp_migration_validator.sh - Master validation script for GCP environment

echo "=== GCP Environment Validation ==="
echo "Running comprehensive validation of GCP Workstation/Vertex IDE environment..."

# Configuration
PROJECT_ID="agi-baby-cherry"  # Default project from cloudbuild.yaml
LOCATION="us-central1"        # Default region from cloudbuild.yaml
REPORT_FILE="gcp_validation_report.md"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --location)
      LOCATION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--project PROJECT_ID] [--location LOCATION]"
      echo ""
      echo "Options:"
      echo "  --project   GCP Project ID (default: agi-baby-cherry)"
      echo "  --location  GCP Location (default: us-central1)"
      echo "  --help      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Using Project: $PROJECT_ID, Location: $LOCATION"
echo ""

# Setup report file
echo "# GCP Environment Validation Report" > $REPORT_FILE
echo "" >> $REPORT_FILE
echo "## Environment Details" >> $REPORT_FILE
echo "* **Timestamp:** $(date)" >> $REPORT_FILE
echo "* **Project:** $PROJECT_ID" >> $REPORT_FILE
echo "* **Location:** $LOCATION" >> $REPORT_FILE
echo "* **Hostname:** $(hostname)" >> $REPORT_FILE
echo "* **OS Info:** $(uname -a)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check prerequisites
echo "Checking prerequisites..."
echo "## Prerequisites Check" >> $REPORT_FILE

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python found: $PYTHON_VERSION"
    echo "* ✅ Python found: $PYTHON_VERSION" >> $REPORT_FILE
else
    echo "❌ Python not found"
    echo "* ❌ Python not found" >> $REPORT_FILE
    exit 1
fi

# Check gcloud
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud --version | head -n 1)
    echo "✅ gcloud found: $GCLOUD_VERSION"
    echo "* ✅ gcloud found: $GCLOUD_VERSION" >> $REPORT_FILE
else
    echo "❌ gcloud not found"
    echo "* ❌ gcloud not found" >> $REPORT_FILE
    exit 1
fi

# Verify gcloud auth
GCLOUD_AUTH=$(gcloud auth list --format="value(account)")
if [[ -z "$GCLOUD_AUTH" ]]; then
    echo "❌ No gcloud authentication found. Please run 'gcloud auth login' first."
    echo "* ❌ No gcloud authentication found." >> $REPORT_FILE
    exit 1
else
    echo "✅ gcloud authenticated as: $GCLOUD_AUTH"
    echo "* ✅ gcloud authenticated as: $GCLOUD_AUTH" >> $REPORT_FILE
fi

echo "" >> $REPORT_FILE

# Ensure scripts directory exists
mkdir -p scripts/validation

# Run the individual validation scripts
echo "Running validation scripts..."

# Source code validation
echo "## Source Code Validation" >> $REPORT_FILE
if [[ -f scripts/validation/validate_source.py ]]; then
    python3 scripts/validation/validate_source.py --project="$PROJECT_ID" --location="$LOCATION" | tee -a $REPORT_FILE
else
    echo "❌ Source code validation script not found" | tee -a $REPORT_FILE
fi

echo "" >> $REPORT_FILE

# Secrets validation
echo "## Secret Manager Validation" >> $REPORT_FILE
if [[ -f scripts/validation/validate_secrets.py ]]; then
    python3 scripts/validation/validate_secrets.py --project="$PROJECT_ID" --location="$LOCATION" | tee -a $REPORT_FILE
else
    echo "❌ Secret Manager validation script not found" | tee -a $REPORT_FILE
fi

echo "" >> $REPORT_FILE

# Cloud Build/Deploy validation
echo "## Cloud Build & Deploy Validation" >> $REPORT_FILE
if [[ -f scripts/validation/validate_build_deploy.py ]]; then
    python3 scripts/validation/validate_build_deploy.py --project="$PROJECT_ID" --location="$LOCATION" | tee -a $REPORT_FILE
else
    echo "❌ Cloud Build validation script not found" | tee -a $REPORT_FILE
fi

echo "" >> $REPORT_FILE

# Vertex AI validation
echo "## Vertex AI Validation" >> $REPORT_FILE
if [[ -f scripts/validation/validate_vertex.py ]]; then
    python3 scripts/validation/validate_vertex.py --project="$PROJECT_ID" --location="$LOCATION" | tee -a $REPORT_FILE
else
    echo "❌ Vertex AI validation script not found" | tee -a $REPORT_FILE
fi

echo "" >> $REPORT_FILE

# Gemini validation
echo "## Gemini Code Assist Validation" >> $REPORT_FILE
if [[ -f scripts/validation/validate_gemini.py ]]; then
    python3 scripts/validation/validate_gemini.py --project="$PROJECT_ID" --location="$LOCATION" | tee -a $REPORT_FILE
else
    echo "❌ Gemini validation script not found" | tee -a $REPORT_FILE
fi

echo "" >> $REPORT_FILE

# Best practices validation
echo "## GCP Best Practices" >> $REPORT_FILE
if [[ -f scripts/validation/validate_best_practices.py ]]; then
    python3 scripts/validation/validate_best_practices.py --project="$PROJECT_ID" --location="$LOCATION" | tee -a $REPORT_FILE
else
    echo "❌ Best practices validation script not found" | tee -a $REPORT_FILE
fi

echo ""
echo "Validation complete! Report saved to $REPORT_FILE"
echo "Check the generated report for details and follow the GCP_MIGRATION_VALIDATION_CHECKLIST.md for manual verification steps."

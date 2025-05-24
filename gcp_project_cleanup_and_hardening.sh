#!/bin/bash
# gcp_project_cleanup_and_hardening.sh
# Cleans up project-level org-policy constraints, checks APIs, IAM, and legacy settings for solo-dev GCP stability.

set -e

PROJECT_ID=$(gcloud config get-value project)
echo "=============================="
echo "GCP Project Cleanup & Hardening for $PROJECT_ID"
echo "=============================="

# 1. List and delete all project-level org-policy constraints
echo
echo "1. Listing project-level org-policy constraints..."
CONSTRAINTS=$(gcloud org-policies list --project="$PROJECT_ID" --format="value(constraint)")
if [[ -z "$CONSTRAINTS" ]]; then
  echo "No project-level constraints found."
else
  echo "Deleting all project-level org-policy constraints..."
  for CONSTRAINT in $CONSTRAINTS; do
    echo "Deleting $CONSTRAINT ..."
    gcloud org-policies delete "$CONSTRAINT" --project="$PROJECT_ID"
  done
fi

# 2. List enabled and disabled APIs
echo
echo "2. Listing enabled and disabled APIs..."
echo "Enabled APIs:"
gcloud services list --enabled --format="table(config.name)"
echo
echo "Disabled APIs:"
gcloud services list --available --filter="state:DISABLED" --format="table(config.name)"

# 3. Optionally enable recommended APIs (uncomment to auto-enable)
# RECOMMENDED_APIS=(
#   "run.googleapis.com"
#   "artifactregistry.googleapis.com"
#   "secretmanager.googleapis.com"
#   "redis.googleapis.com"
#   "cloudbuild.googleapis.com"
#   "iam.googleapis.com"
#   "compute.googleapis.com"
#   "cloudresourcemanager.googleapis.com"
# )
# for API in "${RECOMMENDED_APIS[@]}"; do
#   gcloud services enable "$API" --project="$PROJECT_ID"
# done

# 4. List IAM policy bindings for review
echo
echo "3. Listing IAM policy bindings..."
gcloud projects get-iam-policy "$PROJECT_ID" --format="table(bindings.role, bindings.members)"

# 5. List all service accounts
echo
echo "4. Listing all service accounts..."
gcloud iam service-accounts list --format="table(email,displayName,disabled)"

echo
echo "=============================="
echo "Cleanup complete. Review output above for any legacy settings, unused service accounts, or disabled APIs."
echo "For maximum stability, keep only necessary constraints, APIs, and IAM bindings."
echo "=============================="

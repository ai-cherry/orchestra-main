#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# provision_cicd_service_account.sh
# -----------------------------------------------------------------------------
# Idempotently creates the CI/CD service account `cicd-sa` (if missing) in the
# current gcloud project, and grants the minimal roles needed for CI/CD:
#   - Cloud Build editor
#   - Cloud Run admin
#   - Artifact Registry writer
#   - Service Account User (for Cloud Run runtime SA)
#   - Secret Manager secretAccessor (optional – only if workflows update secret
#     bindings; comment out if you prefer tighter scope)
#
# USAGE: ./scripts/provision_cicd_service_account.sh
# -----------------------------------------------------------------------------
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [[ -z "$PROJECT_ID" ]]; then
  echo "❌  No active gcloud project set. Run 'gcloud config set project <id>' first." >&2
  exit 1
fi

SA_ID="cicd-sa"
SA_EMAIL="$SA_ID@$PROJECT_ID.iam.gserviceaccount.com"

# 1. Create SA if it doesn't exist
if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
  echo "➕ Creating service account $SA_EMAIL …"
  gcloud iam service-accounts create "$SA_ID" \
    --description="CI/CD GitHub Actions service account" \
    --display-name="CI/CD GitHub Actions"
else
  echo "✔️  Service account $SA_EMAIL already exists."
fi

# 2. Grant roles
roles=(
  roles/cloudbuild.builds.editor
  roles/run.admin
  roles/artifactregistry.writer
  roles/iam.serviceAccountUser
  roles/secretmanager.secretAccessor # comment/remove if not desired
)

for role in "${roles[@]}"; do
  echo "🔗 Ensuring role $role …"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$role" \
    --quiet
done

echo "✅  $SA_EMAIL now has required IAM roles."

echo "ℹ️  Next: configure Workload-Identity Federation linking this SA to your GitHub repo (follow GCP docs)." 
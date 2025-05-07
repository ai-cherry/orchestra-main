#!/bin/bash
# setup_gcp_now.sh
# Script to set up GCP infrastructure with badass Vertex AI and Gemini service accounts

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
GITHUB_ORG="ai-cherry"
GITHUB_REPO="orchestra-main"
GITHUB_TOKEN="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"
# OAuth Client ID for GCP authentication
CLIENT_ID="525398941159-7epg7sftcsi4jpkjjl8m6emge3hv3t3v.apps.googleusercontent.com"

# Log function
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${GREEN}[${timestamp}] [INFO] ${message}${NC}"
      ;;
    "WARN")
      echo -e "${YELLOW}[${timestamp}] [WARN] ${message}${NC}"
      ;;
    "ERROR")
      echo -e "${RED}[${timestamp}] [ERROR] ${message}${NC}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}"
      ;;
    *)
      echo -e "[${timestamp}] ${message}"
      ;;
  esac
}

# Step 1: Create service account key file
log "INFO" "Step 1: Creating service account key file..."
cat > project-admin-key.json << 'EOF'
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "216e545f19f380c72ad7eb704a15041621503f03",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDi3y+r4sY+2Jyj\ngdG/N5OrTNMKdhY2nndtxk4V4NVkRdSXKSGE3WEz6bLBaT0iVBXjDhuGyT1IzjiS\nCmkWjQ6CaGCwThjvHjkioHTIsgNO6/7FjCh0YRXJIz+gkY9O2P2UMKDMetlDz6la\nVdaFWHCro/ipoC9dZtiWxX7JoDw6+ZqoYct20qtrRDlh2trF+RT9QzxLJmeWoZxB\nvHU1oU1PsbGPDHyts/iXHqISyjEsUUtvOG/IsvMIWPVWvRCbnweQkktsATqzD7bH\nXZOj4cSqO2imAEPFkK/TZ+56JdjtHoZEaVyxzmXB4Pr9sde6KfuesdXjykufztMR\nwULU1B0fAgMBAAECggEASUsqVwD94+rN/ALiNMDrO5Gnsn8A4Sdj1PqWWnoW5nyq\n2CTpF8f/caqD3fk2T2NT6NUzbmGQI3fADepAFhF/CQFYj0zDwGiGs9mbsQTVjccv\nOTn1DdgZljAFi8XKwwHWNmxZXoYnr8EkaLNHiS/PwpvIJ2DBPI8P1PG76r6SBsjl\n7++ShV9r+m577erGvXUxk80dgYoHfBemwYBLSSm5LW0frSmEKHI7vBIT231YslTy\nYFODMOQQ0t+1MtX+7uNVyYOx+GdERkp9XfB3sgYVxZwdZ2pXha0pOZ2UieAm0Za6\nTNoUvhSYECXBfkMyXz89OaWI+4ycizvW9JziZeLk+QKBgQD5Znm9iYmdmvUYmI6T\nK7nBHDk3IXsJ+rwLOEDLHp0c1dhdgimgzFN81mKibDQ4jefRvTlDqSWbZ7Hn4YMF\nCTyZXgJKlU7A0qlufGWd3gfLGkwlDlzyi209mw7yE4W70sQpasea2e3cVWWYtxy9\nwSYQmxObgVZU5L7feVt1xmOIaQKBgQDo4BhN/6PzdnpyQfow4WLxFRCnjRnAZ4Ka\nLqHt8KB4L9K/3qjLFhJLNAUPcOL0C9K581CFfXqqN4gauKzGYa8id2RB9d8Q7LSE\nLNblKOMA3OoSGlWXDaWXLGLA9IsHyIgUqK6oRkoaW4a8XFN5ntgbJoEDpydfCXTs\nKOnAbIYIRwKBgQCB7U7y3RoiTz3siF2OcjMdVXTBMeIFeuhH+BBZQSOciBNl8494\nQ7oiyRUthK1X4SWp8KhKhW4gHc9i++rjzsIRLBaJgGs8rQKzmn7d1XO97X9JtsfZ\nW6WXeJY6qsz64nxrD0PZejselCaPfqWsfVk1QXTfiGvPYjPF/FUXcDkeMQKBgEOY\nYJWrYZyWxF4L9qJfmceetLHdzB7ELO2yIYCeewXH4+WbrOUeJ/s6Q0nDG615DRa6\noKHO1V85NUGEX2pKCnr3qttWkgQooRFIrqvf3Vxvw2WzzSpGZM1nrdaSZRTCSXWt\nrNzdYj8aWBauufAwgkwHNiWoTE5SwWSXT5pyJcmbAoGBALODSSlDnCtXqMry+lKx\nywyhRlYIk2QsmUjrJdYd74o6C8Q7D6o/p1Ah3uNl5fKvN+0QeNvpJB9yqiauS+w2\nlEMmVdcqYKwdmjkPxGiLKHhJcXiB62Nd5jUtVvGv9lz1c74bJdmhYjUOGuUtR5Ll\nxFFGN62B4+ed1wDppnemICJV\n-----END PRIVATE KEY-----\n",
  "client_email": "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "103717197419391442785",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/orchestra-project-admin-sa%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
log "SUCCESS" "Service account key file created"

# Step 2: Authenticate with GCP
log "INFO" "Step 2: Authenticating with GCP..."
# Export service account key for authentication
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/project-admin-key.json

# Authenticate with the service account
gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"

# Set the correct project ID explicitly 
gcloud config set project ${PROJECT_ID} --quiet
# Verify the account and project
gcloud config get-value account
gcloud config get-value project
log "SUCCESS" "Authenticated with GCP using service account"

# Step 3: Enable required APIs
log "INFO" "Step 3: Enabling required APIs..."
gcloud services enable iam.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable iamcredentials.googleapis.com
log "SUCCESS" "Required APIs enabled"

# Step 4: Create service accounts
log "INFO" "Step 4: Creating service accounts..."
gcloud iam service-accounts create vertex-ai-badass \
  --display-name="Vertex AI Badass Service Account" \
  --description="Service account with extensive permissions for all Vertex AI operations"

gcloud iam service-accounts create gemini-badass \
  --display-name="Gemini Badass Service Account" \
  --description="Service account with extensive permissions for all Gemini API operations"
log "SUCCESS" "Service accounts created"

# Step 5: Grant IAM permissions
log "INFO" "Step 5: Granting IAM permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

  --member="serviceAccount:vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
log "SUCCESS" "IAM permissions granted"

# Step 6: Create service account keys
log "INFO" "Step 6: Creating service account keys..."
gcloud iam service-accounts keys create vertex-ai-key.json \
  --iam-account=vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com

gcloud iam service-accounts keys create gemini-key.json \
  --iam-account=gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com
log "SUCCESS" "Service account keys created"

# Step 7: Store keys in Secret Manager
log "INFO" "Step 7: Storing keys in Secret Manager..."
gcloud secrets create vertex-ai-key \
  --data-file=vertex-ai-key.json \
  --project=${PROJECT_ID} || \
gcloud secrets versions add vertex-ai-key \
  --data-file=vertex-ai-key.json \
  --project=${PROJECT_ID}

gcloud secrets create gemini-key \
  --data-file=gemini-key.json \
  --project=${PROJECT_ID} || \
gcloud secrets versions add gemini-key \
  --data-file=gemini-key.json \
  --project=${PROJECT_ID}
log "SUCCESS" "Keys stored in Secret Manager"

# Step 8: Set up Workload Identity Federation for GitHub Actions
log "INFO" "Step 8: Setting up Workload Identity Federation for GitHub Actions..."
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool" \
  --description="Identity pool for GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe github-pool --location=global --format="value(name)")

gcloud iam service-accounts add-iam-policy-binding \
  vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"

gcloud iam service-accounts add-iam-policy-binding \
  gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
log "SUCCESS" "Workload Identity Federation set up"

# Step 9: Store secrets in GitHub (if GitHub CLI is installed)
if command -v gh &> /dev/null; then
  log "INFO" "Step 9: Storing secrets in GitHub..."
  
  # Authenticate with GitHub
  echo ${GITHUB_TOKEN} | gh auth login --with-token
  
  # Store Vertex AI key
  cat vertex-ai-key.json | gh secret set VERTEX_SERVICE_ACCOUNT_KEY --org ${GITHUB_ORG} --body -
  
  # Store Gemini key
  cat gemini-key.json | gh secret set GEMINI_SERVICE_ACCOUNT_KEY --org ${GITHUB_ORG} --body -
  
  # Store project ID
  echo ${PROJECT_ID} | gh secret set GCP_PROJECT_ID --org ${GITHUB_ORG} --body -
  
  # Store region
  echo ${REGION} | gh secret set GCP_REGION --org ${GITHUB_ORG} --body -
  
  # Store Workload Identity Provider
  echo "projects/${PROJECT_ID}/locations/global/workloadIdentityPools/github-pool/providers/github-provider" | \
    gh secret set WORKLOAD_IDENTITY_PROVIDER --org ${GITHUB_ORG} --body -
  
  # Store service account emails
  echo "vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com" | \
    gh secret set VERTEX_SERVICE_ACCOUNT_EMAIL --org ${GITHUB_ORG} --body -
  
  echo "gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com" | \
    gh secret set GEMINI_SERVICE_ACCOUNT_EMAIL --org ${GITHUB_ORG} --body -
  
  log "SUCCESS" "Secrets stored in GitHub"
else
  log "WARN" "GitHub CLI not installed. Skipping storing secrets in GitHub."
fi

# Step 10: Create GitHub Actions workflow
log "INFO" "Step 10: Creating GitHub Actions workflow..."
mkdir -p .github/workflows

cat > .github/workflows/deploy-to-gcp.yml << 'EOF'
name: Deploy to GCP

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.5.1
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.VERTEX_SERVICE_ACCOUNT_EMAIL }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy orchestra-api \
            --source . \
            --region ${{ secrets.GCP_REGION }} \
            --platform managed \
            --allow-unauthenticated
EOF
log "SUCCESS" "GitHub Actions workflow created"

# Step 11: Verify setup
log "INFO" "Step 11: Verifying setup..."
log "INFO" "Service accounts:"
gcloud iam service-accounts list

log "INFO" "Secrets:"
gcloud secrets list

log "INFO" "IAM policies for Vertex AI service account:"
gcloud projects get-iam-policy ${PROJECT_ID} --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com"

log "INFO" "IAM policies for Gemini service account:"
gcloud projects get-iam-policy ${PROJECT_ID} --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com"

log "SUCCESS" "Setup verification complete"

log "SUCCESS" "GCP infrastructure setup completed successfully!"
log "INFO" "You now have badass service accounts for Vertex AI and Gemini with extensive permissions."
log "INFO" "Service account keys have been stored in Secret Manager and GitHub secrets."
log "INFO" "Workload Identity Federation has been set up for GitHub Actions."
log "INFO" "A GitHub Actions workflow has been created for deploying to Cloud Run."
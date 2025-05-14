#!/bin/bash
# Direct Migration Execution Script with no dependency checks
# This script immediately runs the migration using existing environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             DIRECT GCP MIGRATION EXECUTION                    ║"
echo "║          Using Existing Environment Credentials               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Use existing environment variables
echo -e "${GREEN}Using existing environment variables for migration${NC}"
echo -e "GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
echo -e "GCP_REGION: ${GCP_REGION}"
echo -e "GCP_WORKLOAD_IDENTITY_PROVIDER: ${GCP_WORKLOAD_IDENTITY_PROVIDER}"
echo -e "GCP_PROJECT_AUTHENTICATION_EMAIL: ${GCP_PROJECT_AUTHENTICATION_EMAIL}"

# Use GH_CLASSIC_PAT_TOKEN if available
if [ -n "$GH_CLASSIC_PAT_TOKEN" ]; then
    if command -v gh &> /dev/null; then
        echo "$GH_CLASSIC_PAT_TOKEN" | gh auth login --with-token
        GH_USER=$(gh api user | jq -r '.login')
        echo -e "${GREEN}✓ Authenticated as GitHub user: ${GH_USER}${NC}"
    fi
fi

# Define GitHub repo
if [ -z "$GITHUB_ORG" ]; then
    GITHUB_ORG="$GH_USER"
fi
GITHUB_REPO="${GITHUB_ORG}/orchestra-main"

echo -e "${GREEN}✓ Using GitHub repository: ${GITHUB_REPO}${NC}"

# Set up service account key if available
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
    echo -e "${GREEN}Using GCP_MASTER_SERVICE_JSON for authentication${NC}"
    mkdir -p gcp_migration/credentials
    echo "$GCP_MASTER_SERVICE_JSON" > gcp_migration/credentials/key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/gcp_migration/credentials/key.json"
elif [ -n "$GCP_PROJECT_MANAGEMENT_KEY" ]; then
    echo -e "${GREEN}Using GCP_PROJECT_MANAGEMENT_KEY for authentication${NC}"
    mkdir -p gcp_migration/credentials
    echo "$GCP_PROJECT_MANAGEMENT_KEY" > gcp_migration/credentials/key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/gcp_migration/credentials/key.json"
fi

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}Authenticating gcloud with service account key...${NC}"
    gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Enable required APIs
echo -e "\n${BLUE}Enabling required GCP APIs...${NC}"
gcloud services enable iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com
echo -e "${GREEN}✓ Required GCP APIs enabled${NC}"

# Set up GitHub repository
if command -v gh &> /dev/null; then
    if ! gh repo view "$GITHUB_REPO" &>/dev/null; then
        echo -e "${YELLOW}Creating GitHub repository: $GITHUB_REPO${NC}"
        gh repo create "$GITHUB_REPO" --public
    else
        echo -e "${GREEN}Using existing GitHub repository: $GITHUB_REPO${NC}"
    fi
fi

# Create the deployment workflow file
mkdir -p .github/workflows
cat <<EOF > .github/workflows/deploy-cloud-run.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: 'read'
      id-token: 'write'

    steps:
      - uses: actions/checkout@v3

      - id: 'auth'
        name: 'Authenticate to Google Cloud'
        uses: 'google-github-actions/auth@v1'
        with:
          workload_identity_provider: '${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}'
          service_account: '${{ secrets.GCP_PROJECT_AUTHENTICATION_EMAIL }}'

      - name: 'Set up Cloud SDK'
        uses: 'google-github-actions/setup-gcloud@v1'

      - name: 'Use gcloud CLI'
        run: 'gcloud info'

      - name: 'Deploy to Cloud Run'
        run: |
          gcloud run deploy orchestra-app \
            --source . \
            --region ${{ secrets.GCP_REGION }} \
            --allow-unauthenticated
EOF

echo -e "${GREEN}✓ Created GitHub Actions workflow file${NC}"

# Push changes to GitHub if gh CLI is available
if command -v gh &> /dev/null; then
    echo -e "${YELLOW}Pushing changes to GitHub...${NC}"
    if [ ! -d .git ]; then
        git init
        git add .
        git config --local user.email "deploy@example.com"
        git config --local user.name "Deployment Script"
        git commit -m "Initial deployment setup"
        git branch -M main
        git remote add origin "https://github.com/$GITHUB_REPO.git"
        git push -u origin main
    else
        git add .github/workflows/deploy-cloud-run.yml
        git config --local user.email "deploy@example.com"
        git config --local user.name "Deployment Script"
        git commit -m "Add Cloud Run deployment workflow"
        git push
    fi
    echo -e "${GREEN}✓ Changes pushed to GitHub${NC}"
fi

# Final notes
echo -e "\n${GREEN}${BOLD}GCP MIGRATION COMPLETE!${NC}"
echo -e "Your GitHub repository is now integrated with GCP and ready for deployments."
echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. GitHub Actions will automatically deploy to Cloud Run on next push"
echo -e "2. Monitor deployments in GitHub Actions tab"

# Cleanup any sensitive files
if [ -f "$(pwd)/gcp_migration/credentials/key.json" ]; then
    echo -e "\n${YELLOW}Cleaning up sensitive files...${NC}"
    shred -u "$(pwd)/gcp_migration/credentials/key.json"
    echo -e "${GREEN}✓ Service account key file securely deleted${NC}"
fi

echo -e "\n${GREEN}${BOLD}AI Orchestra is now running in Google Cloud Platform!${NC}"

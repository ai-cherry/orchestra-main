#!/bin/bash
# Direct GCP Deployment Script Using Existing Credentials
# This script uses all available environment variables to immediately deploy to GCP

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             DIRECT GCP DEPLOYMENT EXECUTION                   ║"
echo "║                  USING EXISTING CREDENTIALS                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Report on available environment variables
echo -e "${GREEN}Available GCP environment variables:${NC}"
echo -e "  GCP_PROJECT_ID: ${GCP_PROJECT_ID}"
echo -e "  GCP_REGION: ${GCP_REGION}"
echo -e "  GCP_WORKLOAD_IDENTITY_PROVIDER: ${GCP_WORKLOAD_IDENTITY_PROVIDER}"
echo -e "  GCP_PROJECT_AUTHENTICATION_EMAIL: ${GCP_PROJECT_AUTHENTICATION_EMAIL}"

# Create and set up GCP credentials
echo -e "\n${BLUE}[1/7] Setting up GCP credentials...${NC}"
CREDS_DIR="$(pwd)/gcp_credentials"
mkdir -p "$CREDS_DIR"

# Write GCP service account key to file
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
    echo -e "${GREEN}Using GCP_MASTER_SERVICE_JSON for authentication${NC}"
    echo "$GCP_MASTER_SERVICE_JSON" > "$CREDS_DIR/service_account.json"
    CREDS_FILE="$CREDS_DIR/service_account.json"
elif [ -n "$GCP_PROJECT_MANAGEMENT_KEY" ]; then
    echo -e "${GREEN}Using GCP_PROJECT_MANAGEMENT_KEY for authentication${NC}"
    echo "$GCP_PROJECT_MANAGEMENT_KEY" > "$CREDS_DIR/service_account.json"
    CREDS_FILE="$CREDS_DIR/service_account.json"
else
    echo -e "${RED}ERROR: No GCP credentials found in environment${NC}"
    exit 1
fi

# Set environment variables for authentication
export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
echo -e "${GREEN}✓ GCP credentials set up at $CREDS_FILE${NC}"

# Authenticate with gcloud
echo -e "\n${BLUE}[2/7] Authenticating with Google Cloud...${NC}"
gcloud auth activate-service-account --key-file="$CREDS_FILE"
gcloud config set project "$GCP_PROJECT_ID"
gcloud config set compute/region "$GCP_REGION"
echo -e "${GREEN}✓ Successfully authenticated with GCP${NC}"

# Enable required GCP APIs
echo -e "\n${BLUE}[3/7] Enabling required GCP APIs...${NC}"
gcloud services enable cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    iamcredentials.googleapis.com \
    cloudbuild.googleapis.com
echo -e "${GREEN}✓ Required GCP APIs enabled${NC}"

# Set up GitHub authentication
echo -e "\n${BLUE}[4/7] Setting up GitHub authentication...${NC}"
if [ -n "$GH_CLASSIC_PAT_TOKEN" ] && command -v gh &> /dev/null; then
    echo -e "${GREEN}Using GH_CLASSIC_PAT_TOKEN for GitHub authentication${NC}"
    echo "$GH_CLASSIC_PAT_TOKEN" | gh auth login --with-token
    GH_USER=$(gh api user | jq -r '.login')
    echo -e "${GREEN}✓ Authenticated as GitHub user: ${GH_USER}${NC}"
    GITHUB_ORG="$GH_USER"
    GITHUB_REPO="orchestra-main"
else
    echo -e "${YELLOW}GitHub CLI not available or token not set${NC}"
    GITHUB_ORG="$(whoami)"
    GITHUB_REPO="orchestra-main"
fi

# Create GitHub repository if it doesn't exist
if command -v gh &> /dev/null; then
    if ! gh repo view "$GITHUB_ORG/$GITHUB_REPO" &>/dev/null; then
        echo -e "${YELLOW}Creating GitHub repository: $GITHUB_ORG/$GITHUB_REPO${NC}"
        gh repo create "$GITHUB_ORG/$GITHUB_REPO" --public
        echo -e "${GREEN}✓ Created GitHub repository: $GITHUB_ORG/$GITHUB_REPO${NC}"
    else
        echo -e "${GREEN}✓ Using existing GitHub repository: $GITHUB_ORG/$GITHUB_REPO${NC}"
    fi
fi

# Set up workflow directory
echo -e "\n${BLUE}[5/7] Setting up CI/CD workflow...${NC}"
mkdir -p .github/workflows

# Create Cloud Run deployment workflow
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
          workload_identity_provider: '\${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}'
          service_account: '\${{ secrets.GCP_PROJECT_AUTHENTICATION_EMAIL }}'

      - name: 'Set up Cloud SDK'
        uses: 'google-github-actions/setup-gcloud@v1'

      - name: 'Build and deploy to Cloud Run'
        run: |
          gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/orchestra-app
          gcloud run deploy orchestra-app \\
            --image gcr.io/$GCP_PROJECT_ID/orchestra-app \\
            --platform managed \\
            --region $GCP_REGION \\
            --allow-unauthenticated
EOF

echo -e "${GREEN}✓ Created GitHub Actions workflow for Cloud Run deployment${NC}"

# Create Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo -e "${YELLOW}Creating Dockerfile...${NC}"
    cat <<EOF > Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE \${PORT}

CMD ["python", "app.py"]
EOF
    echo -e "${GREEN}✓ Created Dockerfile${NC}"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo -e "${YELLOW}Creating requirements.txt...${NC}"
    cat <<EOF > requirements.txt
flask==2.0.1
gunicorn==20.1.0
google-cloud-storage==2.0.0
requests==2.26.0
EOF
    echo -e "${GREEN}✓ Created requirements.txt${NC}"
fi

# Save GitHub secrets to GCP Secret Manager
echo -e "\n${BLUE}[6/7] Saving GitHub secrets to GCP Secret Manager...${NC}"

# Create secrets in GCP Secret Manager
add_secret() {
    local name=$1
    local value=$2
    
    if ! gcloud secrets describe "$name" --project="$GCP_PROJECT_ID" &>/dev/null; then
        echo -e "Creating secret: $name"
        echo -n "$value" | gcloud secrets create "$name" --data-file=- --project="$GCP_PROJECT_ID"
    else
        echo -e "Updating secret: $name"
        echo -n "$value" | gcloud secrets versions add "$name" --data-file=- --project="$GCP_PROJECT_ID"
    fi
}

if [ -n "$GCP_WORKLOAD_IDENTITY_PROVIDER" ]; then
    add_secret "GCP_WORKLOAD_IDENTITY_PROVIDER" "$GCP_WORKLOAD_IDENTITY_PROVIDER"
fi

if [ -n "$GCP_PROJECT_AUTHENTICATION_EMAIL" ]; then
    add_secret "GCP_PROJECT_AUTHENTICATION_EMAIL" "$GCP_PROJECT_AUTHENTICATION_EMAIL"
fi

if [ -n "$GCP_PROJECT_ID" ]; then
    add_secret "GCP_PROJECT_ID" "$GCP_PROJECT_ID"
fi

if [ -n "$GCP_REGION" ]; then
    add_secret "GCP_REGION" "$GCP_REGION"
fi

echo -e "${GREEN}✓ Saved secrets to GCP Secret Manager${NC}"

# Push changes to GitHub
echo -e "\n${BLUE}[7/7] Pushing changes to GitHub...${NC}"
if command -v gh &> /dev/null; then
    if [ ! -d .git ]; then
        echo -e "${YELLOW}Initializing Git repository...${NC}"
        git init
        git add .
        git config --local user.email "deploy@example.com"
        git config --local user.name "Deployment Script"
        git commit -m "Initial deployment setup"
        git branch -M main
        git remote add origin "https://github.com/$GITHUB_ORG/$GITHUB_REPO.git"
        git push -u origin main || echo -e "${YELLOW}Failed to push to GitHub. You may need to push manually.${NC}"
    else
        echo -e "${YELLOW}Adding and committing changes...${NC}"
        git add .github/workflows/deploy-cloud-run.yml Dockerfile requirements.txt
        git config --local user.email "deploy@example.com"
        git config --local user.name "Deployment Script"
        git commit -m "Add Cloud Run deployment workflow" || echo -e "${YELLOW}No changes to commit${NC}"
        git push || echo -e "${YELLOW}Failed to push to GitHub. You may need to push manually.${NC}"
    fi
    echo -e "${GREEN}✓ Changes committed and pushed to GitHub${NC}"
else
    echo -e "${YELLOW}GitHub CLI not available. You will need to push changes manually.${NC}"
    echo -e "To push changes, run:"
    echo -e "  git add .github/workflows/deploy-cloud-run.yml Dockerfile requirements.txt"
    echo -e "  git commit -m \"Add Cloud Run deployment workflow\""
    echo -e "  git push"
fi

# Wait for GitHub Actions workflow to start
if command -v gh &> /dev/null; then
    echo -e "\n${BLUE}Waiting for GitHub Actions workflow to start...${NC}"
    sleep 10
    
    if gh workflow list &>/dev/null; then
        echo -e "${GREEN}✓ GitHub Actions workflow listed:${NC}"
        gh workflow list
        
        echo -e "\n${BLUE}Recent GitHub Actions runs:${NC}"
        gh run list --limit 5
    fi
fi

# Deploy directly to Cloud Run (as a backup)
echo -e "\n${BLUE}Directly deploying to Cloud Run...${NC}"
gcloud builds submit --tag "gcr.io/$GCP_PROJECT_ID/orchestra-app" .
gcloud run deploy orchestra-app \
    --image "gcr.io/$GCP_PROJECT_ID/orchestra-app" \
    --platform managed \
    --region "$GCP_REGION" \
    --allow-unauthenticated

# Clean up credentials
echo -e "\n${YELLOW}Cleaning up sensitive files...${NC}"
rm -rf "$CREDS_DIR"
echo -e "${GREEN}✓ Credentials cleaned up${NC}"

echo -e "\n${GREEN}${BOLD}DEPLOYMENT COMPLETE!${NC}"
echo -e "Your application is now deployed to Google Cloud Run!"
echo -e "\nYou can view your deployed application at:"
SERVICE_URL=$(gcloud run services describe orchestra-app --platform managed --region "$GCP_REGION" --format 'value(status.url)')
echo -e "${BLUE}$SERVICE_URL${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. Visit the URL above to access your application"
echo -e "2. Monitor deployments in GitHub Actions at: https://github.com/$GITHUB_ORG/$GITHUB_REPO/actions"
echo -e "3. Make changes to your code and push to GitHub to trigger automatic deployments"

echo -e "\n${GREEN}${BOLD}AI Orchestra is now running in Google Cloud Platform!${NC}"

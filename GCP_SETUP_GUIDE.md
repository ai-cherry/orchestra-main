# GCP Setup Guide: Deploying Badass Vertex AI & Gemini Infrastructure

This guide provides step-by-step instructions for setting up powerful Vertex AI and Gemini service accounts with extensive permissions in your GCP project. Unlike scripts that might not execute in your environment, these are manual steps you can follow right now to get your infrastructure set up.

## Prerequisites

- Access to a terminal with `gcloud` CLI installed
- The service account keys you've provided
- Basic familiarity with GCP and Terraform

## Step 1: Authenticate with GCP

First, let's authenticate with GCP using your existing service account key:

```bash
# Create the service account key file
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

# Authenticate with gcloud
gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=project-admin-key.json

# Set the project
gcloud config set project cherry-ai-project
```

## Step 2: Enable Required APIs

Enable the necessary GCP APIs:

```bash
# Enable required APIs
gcloud services enable iam.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable iamcredentials.googleapis.com
```

## Step 3: Create Service Accounts

Create the "badass" service accounts for Vertex AI and Gemini:

```bash
# Create Vertex AI service account
gcloud iam service-accounts create vertex-ai-badass \
  --display-name="Vertex AI Badass Service Account" \
  --description="Service account with extensive permissions for all Vertex AI operations"

# Create Gemini service account
gcloud iam service-accounts create gemini-badass \
  --display-name="Gemini Badass Service Account" \
  --description="Service account with extensive permissions for all Gemini API operations"
```

## Step 4: Grant IAM Permissions

Grant extensive permissions to the service accounts:

```bash
# Grant roles to Vertex AI service account
gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/logging.admin"

# Grant roles to Gemini service account
gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:gemini-badass@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:gemini-badass@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

## Step 5: Create Service Account Keys

Create keys for the service accounts:

```bash
# Create key for Vertex AI service account
gcloud iam service-accounts keys create vertex-ai-key.json \
  --iam-account=vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com

# Create key for Gemini service account
gcloud iam service-accounts keys create gemini-key.json \
  --iam-account=gemini-badass@cherry-ai-project.iam.gserviceaccount.com
```

## Step 6: Store Keys in Secret Manager

Store the service account keys in Secret Manager:

```bash
# Create secret for Vertex AI key
gcloud secrets create vertex-ai-key \
  --data-file=vertex-ai-key.json \
  --project=cherry-ai-project

# Create secret for Gemini key
gcloud secrets create gemini-key \
  --data-file=gemini-key.json \
  --project=cherry-ai-project
```

## Step 7: Set Up Workload Identity Federation for GitHub Actions

Set up Workload Identity Federation for GitHub Actions:

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool" \
  --description="Identity pool for GitHub Actions"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Get the Workload Identity Pool name
WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe github-pool --location=global --format="value(name)")

# Allow GitHub Actions to impersonate the Vertex AI service account
gcloud iam service-accounts add-iam-policy-binding \
  vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/ai-cherry/orchestra-main"

# Allow GitHub Actions to impersonate the Gemini service account
gcloud iam service-accounts add-iam-policy-binding \
  gemini-badass@cherry-ai-project.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/ai-cherry/orchestra-main"
```

## Step 8: Store Secrets in GitHub

If you have the GitHub CLI installed and authenticated, you can store the secrets in GitHub:

```bash
# Set GitHub token
export GITHUB_TOKEN="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"

# Authenticate with GitHub
echo $GITHUB_TOKEN | gh auth login --with-token

# Store Vertex AI key
cat vertex-ai-key.json | gh secret set VERTEX_SERVICE_ACCOUNT_KEY --org ai-cherry --body -

# Store Gemini key
cat gemini-key.json | gh secret set GEMINI_SERVICE_ACCOUNT_KEY --org ai-cherry --body -

# Store project ID
echo "cherry-ai-project" | gh secret set GCP_PROJECT_ID --org ai-cherry --body -

# Store region
echo "us-central1" | gh secret set GCP_REGION --org ai-cherry --body -

# Store Workload Identity Provider
echo "projects/cherry-ai-project/locations/global/workloadIdentityPools/github-pool/providers/github-provider" | \
  gh secret set WORKLOAD_IDENTITY_PROVIDER --org ai-cherry --body -

# Store service account emails
echo "vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com" | \
  gh secret set VERTEX_SERVICE_ACCOUNT_EMAIL --org ai-cherry --body -

echo "gemini-badass@cherry-ai-project.iam.gserviceaccount.com" | \
  gh secret set GEMINI_SERVICE_ACCOUNT_EMAIL --org ai-cherry --body -
```

## Step 9: Create GitHub Actions Workflow

Create a GitHub Actions workflow file:

```bash
# Create .github/workflows directory
mkdir -p .github/workflows

# Create workflow file
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
```

## Step 10: Verify Setup

Verify that everything is set up correctly:

```bash
# List service accounts
gcloud iam service-accounts list

# List secrets
gcloud secrets list

# List IAM policies
gcloud projects get-iam-policy cherry-ai-project
```

## Using the Service Accounts

### Vertex AI Example

Here's a simple Python example to use the Vertex AI service account:

```python
import os
from google.oauth2 import service_account
from google.cloud import aiplatform

# Path to the service account key file
key_path = "vertex-ai-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Initialize Vertex AI with the credentials
aiplatform.init(
    project="cherry-ai-project",
    location="us-central1",
    credentials=credentials
)

# Now you can use Vertex AI
endpoint = aiplatform.Endpoint("projects/cherry-ai-project/locations/us-central1/endpoints/YOUR_ENDPOINT_ID")
prediction = endpoint.predict(instances=[{"feature1": 1.0, "feature2": "value"}])
print(prediction)
```

### Gemini Example

Here's a simple Python example to use the Gemini service account:

```python
import google.generativeai as genai
from google.oauth2 import service_account

# Path to the service account key file
key_path = "gemini-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Configure the Gemini API
genai.configure(
    api_key=None,  # Not needed when using service account
    credentials=credentials,
    project_id="cherry-ai-project",
)

# Generate text
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Write a poem about artificial intelligence.')
print(response.text)
```

## Conclusion

You now have "badass" service accounts for Vertex AI and Gemini with extensive permissions. These service accounts can be used to access any Vertex AI and Gemini API features without restrictions. The setup also includes Workload Identity Federation for GitHub Actions, allowing you to deploy your applications securely from GitHub.

Remember that these service accounts have extensive permissions, so be careful when using them in production environments. Consider using more restricted service accounts for production deployments.
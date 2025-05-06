# GCP Manual Setup Steps

This document outlines the manual steps you need to perform in GCP to complete the infrastructure setup for the AI Orchestra project.

## Initial Project Setup

1. **Create or Select GCP Project**:
   - Go to the [GCP Console](https://console.cloud.google.com/)
   - Create a new project or select the existing `cherry-ai-project`
   - Note the Project ID for later use

2. **Enable Required APIs**:
   - Go to "APIs & Services > Library"
   - Search for and enable the following APIs:
     - Secret Manager API
     - Identity and Access Management (IAM) API
     - Vertex AI API
     - Cloud Storage API
     - Cloud Build API
     - Workload Identity Federation API

## Create Master Service Account

1. **Create Service Account**:
   - Go to "IAM & Admin > Service Accounts"
   - Click "Create Service Account"
   - Name: `master-service-account`
   - Description: "Master service account for infrastructure management"
   - Click "Create and Continue"

2. **Grant Permissions**:
   - Role: "Owner" (for full access)
   - Click "Continue"
   - Click "Done"

3. **Create Service Account Key**:
   - Find the service account in the list
   - Click the three dots menu > "Manage keys"
   - Click "Add Key" > "Create new key"
   - Key type: JSON
   - Click "Create"
   - The key file will be downloaded to your computer
   - Rename it to `master-service-account-key.json`

## Set Up Secret Manager

1. **Create Secret for Master Key**:
   - Go to "Security > Secret Manager"
   - Click "Create Secret"
   - Name: `master-service-account-key`
   - Upload file: Select the `master-service-account-key.json` file
   - Click "Create Secret"

## Set Up Workload Identity Federation

1. **Create Workload Identity Pool**:
   - Go to "IAM & Admin > Workload Identity Pools"
   - Click "Create Pool"
   - Name: `github-actions-pool`
   - Description: "Pool for GitHub Actions"
   - Click "Continue"

2. **Add Provider**:
   - Click "Add Provider"
   - Provider type: "OpenID Connect (OIDC)"
   - Provider name: `github-actions-provider`
   - Issuer URL: `https://token.actions.githubusercontent.com`
   - Click "Continue"

3. **Configure Provider Attributes**:
   - Attribute mapping:
     - `google.subject`: `assertion.sub`
     - `attribute.actor`: `assertion.actor`
     - `attribute.repository`: `assertion.repository`
     - `attribute.repository_owner`: `assertion.repository_owner`
   - Click "Continue"

4. **Create Service Account for GitHub Actions**:
   - Go to "IAM & Admin > Service Accounts"
   - Click "Create Service Account"
   - Name: `github-actions`
   - Description: "Service account for GitHub Actions"
   - Click "Create and Continue"
   - Grant necessary roles (e.g., Secret Manager Admin, Storage Admin)
   - Click "Done"

5. **Configure Workload Identity Federation**:
   - Go to "IAM & Admin > Workload Identity Pools"
   - Click on the pool you created
   - Click on the provider you created
   - Click "Add Mapping"
   - Attribute: `attribute.repository_owner`
   - Value: `ai-cherry`
   - Service account: Select the GitHub Actions service account
   - Click "Save"

## Create Terraform State Bucket (Optional)

1. **Create Storage Bucket**:
   - Go to "Cloud Storage > Buckets"
   - Click "Create Bucket"
   - Name: `cherry-ai-terraform-state`
   - Location type: Region
   - Location: `us-central1` (or your preferred region)
   - Storage class: Standard
   - Access control: Fine-grained
   - Click "Create"

## Next Steps

After completing these manual steps, you can run the scripts we've created:

1. Set the GitHub token:
   ```bash
   export GITHUB_TOKEN="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"
   ```

2. Run the script to create powerful service account keys:
   ```bash
   export GCP_MASTER_SERVICE_JSON="$(cat /path/to/master-service-account-key.json)"
   ./scripts/create_powerful_service_keys.sh
   ```

3. Update GitHub organization secrets:
   ```bash
   ./scripts/update_github_org_secrets.sh
   ```

4. Update GitHub Codespaces secrets:
   ```bash
   ./scripts/update_codespaces_secrets.sh
   ```

5. Test the GCP integration:
   ```bash
   ./scripts/test_gcp_integration.sh
   ```

Alternatively, you can trigger the GitHub Actions workflow we created, which will automate most of these steps after the initial manual setup.
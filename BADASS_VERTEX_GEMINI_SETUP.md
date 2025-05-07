# Badass Vertex AI and Gemini Setup

This guide provides instructions for setting up "badass" service accounts for Vertex AI and Gemini with extensive permissions in your GCP project. These service accounts will have all the necessary permissions to perform any operation with Vertex AI and Gemini APIs.

## Files Included

1. `terraform/vertex_gemini_setup.tf` - Terraform configuration for creating the service accounts and setting up Workload Identity Federation
2. `apply_vertex_gemini_setup.sh` - Shell script to apply the Terraform configuration and set up GitHub secrets

## Prerequisites

- Google Cloud SDK (gcloud) installed and configured
- Terraform installed (version 1.0.0 or later)
- GitHub CLI (gh) installed
- Existing service account keys with sufficient permissions to create new service accounts and grant IAM permissions

## Setup Instructions

### Step 1: Make the script executable

```bash
chmod +x apply_vertex_gemini_setup.sh
```

### Step 2: Run the setup script

```bash
./apply_vertex_gemini_setup.sh
```

This script will:

1. Authenticate with GCP using your existing service account key
2. Initialize and apply the Terraform configuration
3. Create service account keys for the new Vertex AI and Gemini service accounts
4. Store the keys in Secret Manager
5. Store the keys in GitHub secrets
6. Create a GitHub Actions workflow for deploying to Cloud Run

### Step 3: Verify the setup

After running the script, you should have:

1. Two new service accounts in your GCP project:
   - `vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com`
   - `gemini-badass@cherry-ai-project.iam.gserviceaccount.com`

2. Service account keys stored in Secret Manager:
   - `vertex-ai-key`
   - `gemini-key`

3. GitHub secrets in your organization:
   - `VERTEX_SERVICE_ACCOUNT_KEY`
   - `GEMINI_SERVICE_ACCOUNT_KEY`
   - `WORKLOAD_IDENTITY_PROVIDER`

4. A GitHub Actions workflow file at `.github/workflows/deploy-to-gcp.yml`

## Using the Service Accounts

### Vertex AI Service Account

The Vertex AI service account has the following roles:
- `roles/aiplatform.admin`
- `roles/aiplatform.user`
- `roles/storage.admin`
- `roles/logging.admin`
- `roles/iam.serviceAccountUser`
- `roles/iam.serviceAccountTokenCreator`

You can use this service account for:
- Creating and managing Vertex AI resources
- Training and deploying models
- Running predictions
- Managing datasets
- Accessing logs

### Gemini Service Account

The Gemini service account has the following roles:
- `roles/aiplatform.user`
- `roles/serviceusage.serviceUsageConsumer`
- `roles/iam.serviceAccountUser`
- `roles/iam.serviceAccountTokenCreator`

You can use this service account for:
- Accessing Gemini API
- Running predictions
- Fine-tuning models

## GitHub Actions Integration

The setup includes Workload Identity Federation for GitHub Actions, which allows your GitHub Actions workflows to authenticate with GCP without storing service account keys in GitHub secrets.

The workflow file at `.github/workflows/deploy-to-gcp.yml` demonstrates how to use Workload Identity Federation to deploy to Cloud Run.

## Troubleshooting

If you encounter any issues during setup:

1. Check that your existing service account has sufficient permissions
2. Verify that the Terraform configuration is valid
3. Check the gcloud and Terraform logs for error messages
4. Ensure that the GitHub CLI is authenticated with a token that has sufficient permissions

## Security Considerations

The service accounts created by this setup have extensive permissions. In a production environment, you should follow the principle of least privilege and grant only the permissions that are necessary for your specific use case.

However, as requested, these service accounts are intentionally created with "badass" permissions to give you maximum flexibility for development and testing.
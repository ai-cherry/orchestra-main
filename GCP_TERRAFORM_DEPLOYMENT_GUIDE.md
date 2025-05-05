# GCP Terraform Deployment Guide

This guide outlines the process for deploying GCP infrastructure using Terraform with temporary service account key authentication, and then transitioning to the more secure Workload Identity Federation (WIF).

## Overview

The deployment process consists of three main phases:

1. **Create Service Account Keys**: Generate service account keys with necessary permissions for Vertex AI, Gemini, and Secret Management.
2. **Apply Terraform Configurations**: Deploy infrastructure to common, dev, and prod environments.
3. **Switch to Workload Identity Federation**: Replace service account key authentication with WIF for improved security.

## Prerequisites

- Google Cloud SDK installed and configured
- Terraform installed (v1.5.7 or later)
- GitHub CLI installed (for updating secrets)
- Access to the GitHub organization `ai-cherry`
- Appropriate IAM permissions in GCP project `cherry-ai-project`

## Step 1: Create Service Account Keys

The script `create_badass_service_keys.sh` creates service accounts with extensive permissions for Vertex AI and Gemini services.

```bash
# Run the secure wrapper script, which will prompt for GitHub PAT if needed
./secure_service_key_creation.sh
```

This script will:
- Create three service accounts: vertex-admin-sa, gemini-admin-sa, and secret-management-sa
- Assign comprehensive roles to each service account
- Generate and download service account keys
- Provide instructions for updating GitHub organization secrets

## Step 2: Apply Terraform Configurations

The `apply_terraform_sequence.sh` script applies Terraform configurations in sequence:

```bash
# Run the Terraform apply sequence
./apply_terraform_sequence.sh
```

This script will:
1. Apply the 'common' environment configuration
2. Extract Workload Identity Federation values for later use
3. Apply the 'dev' environment configuration
4. Apply the 'prod' environment configuration

All configurations will use the project ID `cherry-ai-project` and the temporary service account key authentication.

## Step 3: Set Up Workload Identity Federation

After successful Terraform deployment, set up Workload Identity Federation for improved security:

```bash
# Run the script to set up Workload Identity Federation
./secure_setup_workload_identity.sh
```

This script will:
- Create a Workload Identity Pool and Provider in GCP
- Configure service accounts with appropriate IAM bindings
- Update GitHub organization secrets with WIF values

Once WIF is set up, switch the GitHub workflows to use it:

```bash
# Run the script to switch GitHub workflows to WIF authentication
./switch_to_wif_authentication.sh
```

This script will:
- Update the GitHub Actions workflow files to use WIF instead of service account keys
- Provide instructions for updating GitHub secrets with WIF values
- Guide you through committing and pushing the changes

## GitHub Secrets

The following GitHub secrets are used in this process:

1. **During Service Account Key Authentication (Temporary)**:
   - `GCP_ADMIN_SA_KEY_JSON`: Service account key for Vertex AI admin
   - `GCP_GEMINI_SA_KEY_JSON`: Service account key for Gemini services
   - `GCP_SECRET_MANAGEMENT_KEY`: Service account key for Secret Management
   - `GCP_PROJECT_ID`: Project ID (cherry-ai-project)

2. **After Switching to WIF**:
   - `WORKLOAD_IDENTITY_PROVIDER`: WIF provider from Terraform output
   - `SERVICE_ACCOUNT`: Service account email from Terraform output
   - `GCP_PROJECT_ID`: Project ID (remains the same)

## Security Considerations

- Service account keys provide extensive permissions and should be treated as highly sensitive
- The keys are intended for initial setup only; transition to WIF as soon as possible
- Delete local copies of service account keys after updating GitHub secrets
- Consider key rotation policies for any keys that must remain in use
- Audit IAM permissions regularly to ensure principle of least privilege

## Troubleshooting

- If Terraform apply fails, check the error logs for missing permissions or incorrect configuration
- Ensure all required APIs are enabled in the GCP project
- Verify that service account keys have the necessary permissions
- Check GitHub secrets are correctly set with valid values

## Support

Contact cloud-admins@example.com for assistance with this deployment process.

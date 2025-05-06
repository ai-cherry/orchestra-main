# GitHub and GCP Service Keys Management

This repository contains scripts for creating and managing service account keys for Vertex AI and Gemini services in Google Cloud Platform (GCP), as well as synchronizing secrets between GitHub and GCP Secret Manager.

## Overview

These scripts automate the creation of "badass" service accounts with extensive permissions for Vertex AI and Gemini services, along with setting up continuous synchronization between GitHub organization secrets and GCP Secret Manager.

## Scripts

### 1. `configure_badass_keys_and_sync.sh`

This comprehensive script automates the following:

- Creates service accounts for Vertex AI and Gemini services with extensive permissions
- Generates service account keys and uploads them as GitHub organization secrets
- Sets up GitHub organization variables with GCP project information
- Creates a Cloud Function for syncing secrets between GitHub and GCP
- Sets up a Cloud Scheduler job for regular synchronization
- Creates a GitHub Actions workflow for on-demand synchronization

**Usage:**

```bash
chmod +x configure_badass_keys_and_sync.sh
./configure_badass_keys_and_sync.sh
```

### 2. `github_to_gcp_secret_sync.sh`

This dedicated script focuses specifically on setting up synchronization between GitHub organization secrets and GCP Secret Manager:

- Lists all GitHub organization secrets
- Creates corresponding secrets in GCP Secret Manager
- Sets up a Cloud Function for automated synchronization
- Creates a Cloud Scheduler job for daily sync

**Usage:**

```bash
chmod +x github_to_gcp_secret_sync.sh
./github_to_gcp_secret_sync.sh
```

## Configuration

Both scripts use the following configuration variables at the top, which you can modify as needed:

```bash
# Configuration variables
GCP_PROJECT_ID="cherry-ai-project"
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"
```

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- GitHub CLI (`gh`) installed and configured (scripts will attempt to install if not found)
- `jq` for JSON processing (scripts will attempt to install if not found)
- Active GCP project with billing enabled
- GitHub organization with admin permissions
- GitHub Personal Access Token (PAT) with appropriate permissions

## Service Accounts Created

### Vertex AI and Gemini Service Accounts

1. `vertex-ai-badass-access`: For Vertex AI services
2. `gemini-api-badass-access`: For Gemini API services
3. `gemini-code-assist-badass-access`: For Gemini Code Assist services
4. `gemini-cloud-assist-badass-access`: For Gemini Cloud Assist services

### Secret Synchronization Service Account

- `github-secret-sync-sa`: For synchronizing secrets between GitHub and GCP

## GitHub Secrets Created/Updated

- `VERTEX_AI_BADASS_KEY`: Service account key for Vertex AI
- `GEMINI_API_BADASS_KEY`: Service account key for Gemini API
- `GEMINI_CODE_ASSIST_BADASS_KEY`: Service account key for Gemini Code Assist
- `GEMINI_CLOUD_ASSIST_BADASS_KEY`: Service account key for Gemini Cloud Assist
- `GCP_SECRET_SYNC_KEY`: Service account key for secret synchronization

## GitHub Organization Variables Set

- `GCP_PROJECT_ID`: The GCP project ID
- `GCP_PROJECT_NAME`: The GCP project name
- `GCP_REGION`: The GCP region (default: us-central1)
- `GCP_ZONE`: The GCP zone (default: us-central1-a)
- `DEPLOYMENT_ENVIRONMENT`: The deployment environment (default: production)

## Secret Synchronization Limitations

Due to GitHub API limitations, the scripts cannot directly retrieve the values of GitHub organization secrets. The synchronization process:

1. Creates corresponding secrets in GCP Secret Manager with placeholder values
2. Sets up scheduled synchronization to maintain the structure (new secrets, renamed secrets, etc.)
3. **Manual step required**: You must update each secret in GCP Secret Manager with its actual value

## Using Service Account Keys in GitHub Actions

Example workflow for Vertex AI:

```yaml
- name: 'Authenticate to Google Cloud for Vertex AI'
  uses: 'google-github-actions/auth@v1'
  with:
    credentials_json: '${{ secrets.VERTEX_AI_BADASS_KEY }}'
```

Example workflow for Gemini API:

```yaml
- name: 'Authenticate to Google Cloud for Gemini API'
  uses: 'google-github-actions/auth@v1'
  with:
    credentials_json: '${{ secrets.GEMINI_API_BADASS_KEY }}'
```

## Security Considerations

1. **Key Rotation**: Regularly rotate service account keys to mitigate risk
2. **Principle of Least Privilege**: Consider reducing permissions from "badass" to the minimum required
3. **Workload Identity Federation**: For production, consider transitioning to Workload Identity Federation instead of service account keys
4. **GitHub PAT Security**: The GitHub PAT included in the scripts should be rotated and secured

## Transitioning to Workload Identity Federation

For improved security in production environments, consider using Workload Identity Federation instead of service account keys. The `switch_to_wif_authentication.sh` script can assist with this transition.

## Troubleshooting

- **Authentication Issues**: Ensure you're logged in with both `gcloud auth login` and `gh auth login`
- **API Enablement**: If API enablement fails, ensure billing is enabled on your GCP project
- **Permission Errors**: Verify that your user account has necessary roles in GCP and GitHub

## Maintenance

- Run the scripts periodically to update keys and ensure sync is working
- Check Cloud Scheduler logs to verify sync execution
- Review secret values in GCP Secret Manager to ensure they are current

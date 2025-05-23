# Secret Management in CI/CD Pipeline

This document explains how secret management is integrated with our CI/CD pipeline using GitHub Actions and Google Cloud Secret Manager.

## Overview

The integration allows for secure handling of API keys and other sensitive credentials during deployment, with these key features:

- Secrets are stored in GitHub Secrets, never committed to the repository
- During CI/CD pipeline execution, secrets are securely passed to GCP Secret Manager
- Cloud Run deployments access these secrets directly from Secret Manager at runtime
- Pre-commit hooks protect against accidental secret commits

## Required GitHub Secrets

Set up the following secrets in your GitHub repository settings (Settings > Secrets and variables > Actions):

1. `PORTKEY_KEY_CONTENT` - The raw content of your Portkey API key file
2. `GCP_SA_KEY_6833bc94f0e3ef8648efc1578caa23ba2b8a8a52` - The GCP service account JSON key with permissions to:
   - Access Secret Manager
   - Deploy to Cloud Run

## Workflow Implementation

The GitHub Actions workflow (`.github/workflows/deploy.yml`) handles the complete deployment process:

1. **Authentication**: Uses the GCP service account key to authenticate with Google Cloud
2. **Secret Creation**: Creates a temporary file from GitHub Secrets
3. **Secret Management**: Runs our `secrets_setup.sh` script to create/update the secret in GCP Secret Manager
4. **Cleanup**: Removes temporary files to maintain security
5. **Deployment**: Deploys to Cloud Run with the secret injected as an environment variable

```yaml
# Key Secret Management Steps
- name: Create Key File
  run: |
    echo "${{ secrets.PORTKEY_KEY_CONTENT }}" > portkey.key
  shell: bash

- name: Set up Secret Manager
  run: |
    chmod +x secrets_setup.sh
    ./secrets_setup.sh \
      --project=cherry-ai-project \
      --file=portkey.key \
      --secret=PORTKEY_API_KEY \
      --service-account=vertex-agent@cherry-ai-project.iam.gserviceaccount.com

- name: Cleanup sensitive files
  run: rm -f portkey.key
  shell: bash
```

## Secret Injection

Secrets are injected into the Cloud Run service as environment variables:

```yaml
- name: Deploy to Cloud Run
  run: |-
    gcloud run deploy orchestra-prod \
      --image=us-docker.pkg.dev/cherry-ai-project/orchestra/app:latest \
      --service-account=orchestra-cloud-run-prod@cherry-ai-project.iam.gserviceaccount.com \
      --set-env-vars=PORTKEY_API_KEY=$(gcloud secrets versions access latest --secret=PORTKEY_API_KEY)
```

## Local Development Protection

To protect against accidentally committing secrets:

1. Install the pre-commit hook:

   ```bash
   ./scripts/install-pre-commit-hook.sh
   ```

2. The hook will prevent commits containing files with `.key` or `gsa-key.json` patterns.

## IAM Permissions

The service accounts need specific permissions:

1. **vertex-agent@cherry-ai-project.iam.gserviceaccount.com**:

   - `roles/secretmanager.secretAccessor` - To read secrets
   - `roles/aiplatform.reasoningEngineServiceAgent` - For AI platform operations

2. **orchestra-cloud-run-prod@cherry-ai-project.iam.gserviceaccount.com**:
   - Used as the runtime service account for Cloud Run

## Security Considerations

- Secrets are never committed to the repository
- Temporary files are created only during deployment and immediately cleaned up
- Access is controlled through IAM permissions
- Pre-commit hooks provide an additional layer of protection

## Troubleshooting

If deployment fails with secret-related issues:

1. Verify GitHub Secrets are correctly set up
2. Check IAM permissions for both service accounts
3. Review Cloud Build logs for specific error messages
4. Ensure Secret Manager API is enabled in your GCP project

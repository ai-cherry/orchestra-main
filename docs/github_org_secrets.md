# GitHub Organization Secrets Configuration

This document provides information about the GitHub organization secrets required for CI/CD deployment of the Orchestra application.

## Required Secrets

These secrets are used by GitHub Actions workflows to deploy the application to Google Cloud Platform.

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `ORG_GCP_PROJECT_ID` | Google Cloud Platform Project ID | `cherry-ai-project` |
| `ORG_GCP_CREDENTIALS` | GCP Service Account Key JSON | `{"type":"service_account","project_id":"cherry-ai-project",...}` |
| `ORG_GCP_REGION` | GCP Region for deployment | `us-west4` |
| `ORG_GKE_CLUSTER_PROD` | GKE Cluster name for production | `autopilot-cluster-1` |
| `ORG_GKE_CLUSTER_STAGING` | GKE Cluster name for staging | `autopilot-cluster-1` |
| `ORG_REDIS_HOST` | Redis instance hostname | `redis-12345.c12345.us-west4-1.gcp.cloud.redislabs.com` |
| `ORG_REDIS_PORT` | Redis instance port | `6379` |
| `ORG_REDIS_PASSWORD` | Redis instance password | `your-redis-password` |
| `DOCKERHUB_USERNAME` | Docker Hub username for storing images | `your-dockerhub-username` |
| `DOCKERHUB_TOKEN` | Docker Hub access token | `your-dockerhub-token` |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for notifications | `https://hooks.slack.com/services/...` |

## Setting Up Secrets

You can set up these secrets using one of the following methods:

### Method 1: Using GitHub Web Interface

1. Navigate to your GitHub repository
2. Go to Settings → Secrets and variables → Actions
3. Click on "New repository secret"
4. Enter the name and value of the secret
5. Click "Add secret"

### Method 2: Using GitHub CLI

```bash
gh secret set GCP_PROJECT_MANAGEMENT_KEY --repo your-org/your-repo --body "$(cat /path/to/your-key-file.json)"
```

### Method 3: Using the Provided Script

We've created a script to help you set up these secrets:

```bash
./update_github_secrets.sh
```

The script will guide you through setting up all required secrets.

## Service Account Requirements

The GCP service account used for deployment (specified in `ORG_GCP_CREDENTIALS`) should have the following roles:

- Cloud Run Admin (`roles/run.admin`)
- Service Account User (`roles/iam.serviceAccountUser`)
- Storage Admin (`roles/storage.admin`)
- Artifact Registry Admin (`roles/artifactregistry.admin`)
- Kubernetes Engine Admin (`roles/container.admin`) - If using GKE
- Secret Manager Admin (`roles/secretmanager.admin`)

## Secret Rotation

It's recommended to rotate sensitive secrets periodically:

1. GCP Service Account Keys: Rotate every 90 days
2. Docker Hub Tokens: Rotate every 180 days
3. Redis passwords: Rotate every 180 days

After rotating secrets, update the corresponding GitHub secrets with the new values.

## Troubleshooting

If you encounter issues with GitHub Actions deployment related to secrets:

1. Verify that all required secrets are set correctly
2. Check that the GCP service account has the necessary permissions
3. Ensure the service account key hasn't expired or been revoked
4. Verify the JSON format of the GCP credentials is valid

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Google Cloud Service Account Documentation](https://cloud.google.com/iam/docs/creating-managing-service-accounts)

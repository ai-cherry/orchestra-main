# Service Account Key Authentication

This document explains how to use service account key authentication for deploying the MCP server to Google Cloud Platform.

## Overview

While Workload Identity Federation is the recommended approach for authenticating with Google Cloud Platform from GitHub Actions, service account key authentication provides an alternative method that may be easier to set up in some environments.

## Service Account Key Authentication

Service account key authentication involves:

1. Creating a service account in Google Cloud Platform
2. Generating a key for the service account
3. Storing the key as a secret in GitHub
4. Using the key to authenticate with Google Cloud Platform during deployment

## Setup Process

### 1. Create a Service Account

```bash
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"
```

### 2. Grant Necessary Permissions

```bash
# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Grant Storage Admin role (for pushing Docker images)
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Grant Service Account User role
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 3. Generate a Service Account Key

```bash
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=github-actions-sa@your-project-id.iam.gserviceaccount.com
```

### 4. Store the Key as a GitHub Secret

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Name: `GCP_SA_KEY`
5. Value: Copy and paste the entire contents of the `service-account-key.json` file
6. Click "Add secret"

### 5. Add Other Required Secrets

1. `GCP_PROJECT_ID`: Your Google Cloud project ID
2. `GCP_REGION`: Your Google Cloud region (e.g., `us-central1`)

## GitHub Actions Workflow

The GitHub Actions workflow for service account key authentication is defined in `.github/workflows/key-deploy.yml`. This workflow:

1. Runs tests to ensure code quality
2. Sets up the service account key
3. Authenticates to Google Cloud Platform
4. Builds and pushes the Docker image
5. Deploys the service to Cloud Run
6. Verifies the deployment

## Local Deployment

For local deployment, you can use the `deploy_with_key.sh` script:

```bash
./deploy_with_key.sh your-project-id us-central1 dev latest service-account-key.json
```

This script:

1. Authenticates with Google Cloud Platform using the service account key
2. Loads environment-specific configurations
3. Builds and pushes the Docker image
4. Deploys the service to Cloud Run
5. Verifies the deployment

## Security Considerations

Service account keys should be handled with care:

1. **Limit Permissions**: Grant only the necessary permissions to the service account
2. **Secure Storage**: Store the key securely and never commit it to version control
3. **Regular Rotation**: Rotate the key regularly to minimize the risk of compromise
4. **Consider Alternatives**: When possible, use Workload Identity Federation instead of service account keys

## Comparison with Workload Identity Federation

| Feature          | Service Account Key          | Workload Identity Federation     |
| ---------------- | ---------------------------- | -------------------------------- |
| Setup Complexity | Simpler                      | More complex                     |
| Security         | Less secure (long-lived key) | More secure (short-lived tokens) |
| Key Management   | Manual key rotation required | No keys to manage                |
| Audit Trail      | Less detailed                | More detailed                    |
| Recommended For  | Development, testing         | Production                       |

## Best Practices

1. **Limit Key Access**: Restrict access to the service account key to only those who need it
2. **Monitor Usage**: Regularly review audit logs for unexpected access patterns
3. **Implement Least Privilege**: Grant only the minimum necessary permissions to the service account
4. **Consider Environment**: Use different service accounts for different environments (dev, staging, prod)
5. **Plan for Migration**: Consider migrating to Workload Identity Federation for production environments

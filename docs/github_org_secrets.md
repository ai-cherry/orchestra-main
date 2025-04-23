# GitHub Organization Secrets for GCP Storage Integration

This document provides instructions for setting up the organization-level GitHub secrets required for the Orchestra project to connect to Google Cloud Platform (GCP) Firestore and Redis services.

## Why Organization-Level Secrets?

Organization-level secrets offer several advantages:

1. **Centralized Management**: Manage secrets in one place for all repositories in your organization.
2. **Consistent Access**: Ensure all repositories have access to the same production credentials.
3. **Reduced Duplication**: Avoid duplicating sensitive credentials across multiple repositories.
4. **Simplified Rotation**: Update credentials in a single location when they need to be rotated.

## Required Organization Secrets

Set up the following secrets in your GitHub organization:

### GCP Authentication

| Secret Name | Description |
|-------------|-------------|
| `ORG_GCP_CREDENTIALS` | JSON service account key with permissions for Firestore and GKE |
| `ORG_GCP_PROJECT_ID` | Your Google Cloud project ID |
| `ORG_GCP_SERVICE_ACCOUNT_KEY` | JSON service account key for application-level access |
| `ORG_GCP_REGION` | GCP region where your resources are deployed |

### GKE Clusters

| Secret Name | Description |
|-------------|-------------|
| `ORG_GKE_CLUSTER_PROD` | Name of production GKE cluster |
| `ORG_GKE_CLUSTER_STAGING` | Name of staging GKE cluster |

### Redis Configuration

| Secret Name | Description |
|-------------|-------------|
| `ORG_REDIS_HOST` | Hostname of Redis instance (e.g., `10.0.0.1` or `redis-primary.redis.svc.cluster.local`) |
| `ORG_REDIS_PORT` | Port of Redis instance (typically `6379`) |
| `ORG_REDIS_PASSWORD` | Password for authenticating with Redis |

## Setting Up Organization Secrets

1. Navigate to your GitHub organization settings
2. Select "Secrets and variables" from the left sidebar
3. Click on "Actions" to manage GitHub Actions secrets
4. Click "New organization secret"
5. Enter the name and value for each secret listed above
6. For repository access:
   - Select "All repositories" to make the secret available to all repositories in the organization
   - Or select "Selected repositories" and choose specific repositories

## Service Account Permissions

The GCP service account used for the `ORG_GCP_CREDENTIALS` and `ORG_GCP_SERVICE_ACCOUNT_KEY` secrets should have the following permissions:

### For CI/CD and Deployment
- `roles/container.developer` - For deploying to GKE
- `roles/storage.admin` - For accessing GCS buckets

### For Application Data Access
- `roles/datastore.user` - For Firestore access
- `roles/redis.editor` - For Redis (Cloud Memorystore) access

## Redis Setup

If you're using Google Cloud Memorystore for Redis:

1. Create a Redis instance in Google Cloud Console
2. Make sure it's in the same VPC network as your GKE cluster
3. Set up VPC peering if needed for connectivity
4. For production, consider enabling authentication and TLS

## Security Considerations

- Rotate service account keys periodically
- Use the principle of least privilege when assigning IAM roles
- Consider using Workload Identity Federation instead of service account keys for production environments
- For Redis, use authentication and consider using VPC Service Controls for additional security

## Troubleshooting

If you encounter issues with the integration:

1. Check the GitHub Actions workflow logs for error messages
2. Verify that all secrets are correctly set and accessible to the repository
3. Confirm that the service account has the necessary permissions
4. For Redis connectivity issues, check network connectivity and firewall rules

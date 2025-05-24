# AI Orchestra Optimized Deployment Guide

This guide provides instructions for deploying the AI Orchestra project using the performance-optimized deployment tools. These tools leverage the provided credentials (GCP_MASTER_SERVICE_JSON, GH_CLASSIC_PAT_TOKEN, and GH_FINE_GRAINED_PAT_TOKEN) to streamline authentication and deployment processes.

## Prerequisites

- Google Cloud Platform account with the following APIs enabled:
  - Cloud Run
  - Secret Manager
  - Artifact Registry
  - IAM
  - Cloud Build
- GitHub account with access to the repository
- Docker installed locally for building images
- gcloud CLI installed and configured

## Credentials Setup

The deployment tools require the following credentials:

1. **GCP_MASTER_SERVICE_JSON**: A service account key with permissions to deploy to Cloud Run, access Secret Manager, and push to Artifact Registry.
2. **GH_CLASSIC_PAT_TOKEN**: A GitHub Personal Access Token with classic permissions.
3. **GH_FINE_GRAINED_PAT_TOKEN**: A GitHub Personal Access Token with fine-grained permissions.

### Setting Up Credentials Locally

```bash
# Set up GCP credentials
export GCP_MASTER_SERVICE_JSON='{"type":"service_account",...}'

# Set up GitHub tokens
export GH_CLASSIC_PAT_TOKEN='your-classic-token'
export GH_FINE_GRAINED_PAT_TOKEN='your-fine-grained-token'
```

### Setting Up Credentials in GitHub

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following repository secrets:
   - `GCP_MASTER_SERVICE_JSON`: The full JSON content of your service account key
   - `GH_CLASSIC_PAT_TOKEN`: Your GitHub classic PAT token
   - `GH_FINE_GRAINED_PAT_TOKEN`: Your GitHub fine-grained PAT token

## Deployment Methods

### Method 1: Local Deployment Using Script

The `deploy_optimized.sh` script provides a quick way to deploy the application from your local machine:

```bash
# Make the script executable (if not already)
chmod +x deploy_optimized.sh

# Deploy to development environment (default)
./deploy_optimized.sh

# Deploy to a specific environment (dev, staging, prod)
./deploy_optimized.sh prod
```

### Method 2: Automated Deployment Using GitHub Actions

The repository includes a GitHub Actions workflow file (`.github/workflows/performance-optimized-deploy.yml`) that automates the deployment process:

1. Push to the `develop` branch to deploy to the development environment
2. Push to the `main` branch to deploy to the production environment
3. Manually trigger the workflow from the GitHub Actions tab to deploy to a specific environment

## Performance Optimizations

The deployment tools include several performance optimizations:

### 1. Cloud Run Optimizations

- Increased CPU and memory allocation (2 CPU, 1GB memory)
- Configured min/max instances for better scaling (1-10 instances)
- Increased concurrency to handle more requests (80 concurrent requests)
- Enabled startup CPU boost for faster cold starts

### 2. Docker Image Optimizations

- Multi-stage build to reduce image size
- Optimized dependency installation
- Pre-configured environment variables for performance
- Non-root user for better security

### 3. MCP Server Performance Tuner

The `mcp_server/utils/performance_tuner.py` module provides utilities for optimizing the runtime performance of the MCP server:

```python
from mcp_server.utils.performance_tuner import cache_result, track_performance, get_metrics

# Cache function results
@cache_result(ttl=300)
def expensive_operation(data):
    # ...
    return result

# Track function performance
@track_performance
def important_function():
    # ...
    return result

# Get performance metrics
metrics = get_metrics()
print(f"Memory usage: {metrics['memory_usage']} MB")
```

## Monitoring and Verification

After deployment, you can monitor the application using:

1. **Cloud Run Console**: View logs, metrics, and revisions
2. **Cloud Monitoring**: Set up dashboards and alerts
3. **Performance Metrics API**: Access runtime metrics through the `/metrics` endpoint

## Troubleshooting

### Common Issues

1. **Deployment Fails with Authentication Error**:

   - Ensure the GCP_MASTER_SERVICE_JSON has the correct permissions
   - Check that the service account has the necessary roles

2. **Container Fails to Start**:

   - Check the Cloud Run logs for startup errors
   - Verify that the GCP_SECRET_MANAGEMENT_KEY secret exists in Secret Manager

3. **Performance Issues**:
   - Adjust the resource limits in the deployment script or workflow
   - Check the performance metrics to identify bottlenecks

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the Cloud Run logs for detailed error messages
2. Review the GitHub Actions workflow run for deployment errors
3. Contact the AI Orchestra team for assistance

## Security Considerations

The deployment tools use service account keys and GitHub tokens, which should be kept secure:

1. Never commit credentials to the repository
2. Rotate credentials regularly
3. Use the principle of least privilege when assigning permissions
4. Consider using Workload Identity Federation for production deployments

## Next Steps

After deploying the application, you may want to:

1. Set up custom domains and SSL certificates
2. Configure Cloud Armor for additional security
3. Implement continuous monitoring and alerting
4. Set up automated backups for critical data

## Conclusion

The optimized deployment tools provide a streamlined way to deploy the AI Orchestra project with performance optimizations. By leveraging the provided credentials and automation, you can quickly deploy the application to Google Cloud Run with minimal manual intervention.

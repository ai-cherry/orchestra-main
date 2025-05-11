# AI Orchestra Deployment Guide

This guide provides instructions for deploying the AI Orchestra project to Google Cloud Platform (GCP). The deployment process includes setting up the necessary infrastructure, deploying the MCP Server, and deploying the main application.

## Prerequisites

Before deploying the AI Orchestra project, ensure you have the following:

1. **GCP Project**: A GCP project with billing enabled
2. **GCP Service Account**: A service account with the following roles:
   - Cloud Run Admin
   - Secret Manager Admin
   - Redis Admin
   - Monitoring Admin
   - Storage Admin
   - Service Account User
   - Artifact Registry Admin
   - IAM Admin
3. **Service Account Key**: The service account key in JSON format
4. **Required Tools**:
   - Google Cloud SDK (`gcloud`)
   - Docker
   - Python 3.11+
   - Poetry

## Deployment Steps

### 1. Fix Dependencies

The first step is to fix the dependencies in the MCP Server component. There was an issue with the `google-cloud-secretmanager` package version. This has been fixed by updating the version constraint in the `pyproject.toml` file.

```bash
cd mcp_server
poetry update
cd ..
```

### 2. Deploy the Entire Project

The deployment process has been simplified with a single script that handles the entire deployment process. The script performs the following steps:

1. Fix dependencies and update Poetry
2. Authenticate with GCP
3. Enable required APIs
4. Apply Terraform configuration
5. Build and deploy the MCP Server
6. Build and deploy the main application

To deploy the entire project, run the following command:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

You can customize the deployment with the following options:

```bash
./deploy.sh --project PROJECT_ID --region REGION --env ENV
```

Where:
- `PROJECT_ID` is your GCP project ID (default: cherry-ai-project)
- `REGION` is the GCP region to deploy to (default: us-central1)
- `ENV` is the environment to deploy to (dev, staging, prod) (default: dev)

### 3. Verify the Deployment

After the deployment is complete, you can verify that everything is working correctly by accessing the deployed services:

1. **MCP Server**: The URL will be displayed at the end of the deployment process
2. **Main Application**: The URL will be displayed at the end of the deployment process

You can also check the status of the deployed services in the GCP Console:

1. Go to the [Cloud Run page](https://console.cloud.google.com/run) in the GCP Console
2. Verify that the MCP Server and main application services are running
3. Click on the services to view details and logs

## Troubleshooting

If you encounter any issues during the deployment process, here are some common problems and their solutions:

### Dependency Resolution Issues

If you encounter dependency resolution issues with Poetry, try the following:

1. Update Poetry to the latest version:
   ```bash
   pip install --upgrade poetry
   ```

2. Clear the Poetry cache:
   ```bash
   poetry cache clear --all pypi
   ```

3. Update the dependencies:
   ```bash
   poetry update
   ```

### Authentication Issues

If you encounter authentication issues with GCP, ensure that:

1. The `GCP_MASTER_SERVICE_JSON` environment variable is set to the content of your service account key JSON
2. The service account has the necessary permissions
3. The APIs are enabled in your GCP project

### Deployment Script Not Found

If you encounter an error like `bash: deploy.sh: command not found`, ensure that:

1. You are in the correct directory (the root directory of the project)
2. The script is executable:
   ```bash
   chmod +x deploy.sh
   ```

3. Try running the script with the full path:
   ```bash
   ./deploy.sh
   ```

## Next Steps

After deploying the AI Orchestra project, consider the following next steps:

1. **Set up Workload Identity Federation**: For improved security, set up Workload Identity Federation to eliminate the need for service account keys
2. **Configure Monitoring**: Set up monitoring and alerting for the deployed services
3. **Set up CI/CD**: Configure CI/CD pipelines for automated deployment

## Additional Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
- [Poetry Documentation](https://python-poetry.org/docs/)
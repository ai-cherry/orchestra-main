# Orchestra Deployment Steps

This document provides a step-by-step guide for deploying the Orchestra application to
## Prerequisites

Before starting the deployment process, ensure you have:

- Access to the `cherry-ai-project` - Permissions to create service accounts and resources in - GitHub repository access (if using CI/CD deployment)

## Environment Preparation

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd orchestra-main
   ```

2. **Make Deployment Scripts Executable**

   ```bash
   chmod +x make_scripts_executable.sh
   ./make_scripts_executable.sh
   ```

   This will make all deployment-related scripts executable.

3. **Verify Deployment Readiness**

   ```bash
   ./verify_deployment_readiness.sh
   ```

   This script checks if your environment is properly set up for deployment and identifies any missing components.

## Authentication and Infrastructure Setup

1. **Set Up
   ```bash
   ./setup_vertex_key.sh
   ```

   This script:

   - Installs    - Sets up authentication with    - Creates or imports a vertex-agent service account key
   - Tests authentication with the service account key

2. **Set Up Redis for Production**

   ```bash
   ./setup_redis_for_deployment.sh prod
   ```

   This script:

   - Creates a Redis instance in    - Generates a secure password and stores it in    - Updates the .env file with Redis connection information

3. **Install Deployment Requirements**

   ```bash
   ./prepare_for_deployment.sh
   ```

   This script installs Docker and other requirements needed for deployment.

## Deployment Options

Choose one of the following deployment methods:

### Option 1: Direct
This is the simplest method for quick deployment:

```bash
./deploy_to_cloud_run.sh prod
```

This script:

- Builds a Docker image of the application
- Pushes the image to Google Artifact Registry
- Deploys the application to - Sets up environment variables and secrets

### Option 2: Terraform Infrastructure Deployment

For more comprehensive infrastructure deployment:

```bash
cd infra
./run_terraform.sh
```

This creates all the required
- - MongoDB
- Redis instance
- - VPC network and connector
- Monitoring and logging

### Option 3: GitHub Actions CI/CD (Recommended for Production)

1. **Configure GitHub Secrets**

   ```bash
   ./update_github_secrets.sh
   ```

   This script sets up the required secrets in your GitHub repository.

2. **Push Changes to GitHub**

   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

3. **Monitor Deployment Progress**

   Go to your GitHub repository's "Actions" tab to monitor the deployment process.

## Post-Deployment Verification

After deployment is complete:

1. **Test the API Endpoint**

   ```bash
   # For    curl $(g   ```

2. **Monitor Logs**

   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-prod" --limit=10
   ```

3. **Check Metrics Dashboard**

   Visit the    https://console.cloud.google.com/monitoring/dashboards?project=cherry-ai-project

## Troubleshooting

If you encounter issues during deployment:

1. **Check Authentication**

   ```bash
   ./test_   ```

2. **Verify Environment Configuration**

   ```bash
   cat .env
   ```

   Ensure that all required environment variables are set correctly.

3. **Check
   ```bash
   g   ```

4. **View Build Logs**

   If using Cloud Build:

   ```bash
   gcloud builds list
   gcloud builds log <build-id>
   ```

## Security Considerations

1. **Service Account Key Security**

   - Keep the service account key secure
   - Consider rotating the key periodically

2. **Secret Management**

   - Use    - Avoid hardcoding secrets in configuration files

3. **Network Security**
   - Configure VPC for proper isolation
   - Use private endpoints where possible

## Maintenance

1. **Update Dependencies**

   Regularly update dependencies by updating requirements files and redeploying.

2. **Monitor Resource Usage**

   Set up budget alerts and monitor resource usage to control costs.

3. **Backup Data**

   Regularly back up MongoDB

## Additional Resources

- [- [- [GitHub Actions Documentation](https://docs.github.com/en/actions)

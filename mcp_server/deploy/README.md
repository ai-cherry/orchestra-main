# MCP Server Deployment Guide

This guide provides instructions for deploying the MCP Server to Google Cloud Platform (GCP) with performance-optimized settings. The deployment process is designed to be fast, reliable, and secure.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Quick Start](#quick-start)
- [Detailed Deployment Steps](#detailed-deployment-steps)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the MCP Server, ensure you have the following:

1. **GCP Project**: A GCP project with billing enabled
2. **GCP Service Account**: A service account with the following roles:
   - Cloud Run Admin
   - Secret Manager Admin
   - Redis Admin
   - Monitoring Admin
   - Storage Admin
   - Service Account User
3. **Service Account Key**: The service account key in JSON format
4. **GitHub Tokens**: If using GitHub Actions for CI/CD:
   - `GH_CLASSIC_PAT_TOKEN`: A classic personal access token with `repo` scope
   - `GH_FINE_GRAINED_PAT_TOKEN`: A fine-grained personal access token with `deployments` scope
5. **Required Tools**:
   - Google Cloud SDK (`gcloud`)
   - Docker
   - Python 3.8+
   - Poetry

## Deployment Options

The MCP Server can be deployed using one of the following methods:

1. **Manual Deployment**: Using the `deploy_optimized.sh` script
2. **Pulumi Deployment**: Using the Pulumi configuration in `pulumi/main.py`
3. **CI/CD Deployment**: Using GitHub Actions workflow in `.github/workflows/deploy.yml`

## Quick Start

For a quick deployment to the development environment:

```bash
# Set environment variables
export GCP_MASTER_SERVICE_JSON=$(cat /path/to/service-account-key.json)
export GCP_PROJECT_ID=cherry-ai-project
export GCP_REGION=us-central1

# Run the deployment script
cd mcp_server
chmod +x deploy/deploy_optimized.sh
./deploy/deploy_optimized.sh
```

## Detailed Deployment Steps

### 1. Manual Deployment

The `deploy_optimized.sh` script automates the deployment process:

```bash
./deploy/deploy_optimized.sh \
  --project cherry-ai-project \
  --region us-central1 \
  --service-name mcp-server \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 2 \
  --memory 2Gi \
  --concurrency 80
```

Available options:

| Option             | Description              | Default             |
| ------------------ | ------------------------ | ------------------- |
| `--project`        | GCP project ID           | `cherry-ai-project` |
| `--region`         | GCP region               | `us-central1`       |
| `--service-name`   | Cloud Run service name   | `mcp-server`        |
| `--min-instances`  | Minimum instances        | `1`                 |
| `--max-instances`  | Maximum instances        | `100`               |
| `--cpu`            | CPU count                | `2`                 |
| `--memory`         | Memory size              | `2Gi`               |
| `--concurrency`    | Concurrency per instance | `80`                |
| `--timeout`        | Request timeout          | `300s`              |
| `--vpc-connector`  | VPC connector name       | `vpc-connector`     |
| `--redis-instance` | Redis instance name      | `mcp-redis`         |
| `--redis-tier`     | Redis tier               | `STANDARD_HA`       |
| `--redis-size`     | Redis size in GB         | `10`                |

### 2. Pulumi Deployment

The Pulumi configuration in `pulumi/main.py` provides a declarative way to deploy the MCP Server:

```bash
# Initialize Pulumi
cd mcp_server/pulumi
pulumi init \
  -backend-config="bucket=cherry-ai-project-pulumi-state" \
  -backend-config="prefix=mcp-server"

# Plan the deployment
pulumi plan \
  -var="project_id=cherry-ai-project" \
  -var="region=us-central1" \
  -var="env=dev" \
  -out=pulumi-plan

# Apply the deployment
pulumi apply pulumi-plan
```

### 3. CI/CD Deployment

The GitHub Actions workflow in `.github/workflows/deploy.yml` automates the CI/CD process:

1. Set up the following secrets in your GitHub repository:

   - `GCP_PROJECT_ID`: Your GCP project ID
   - `WIF_PROVIDER`: Your Workload Identity Federation provider
   - `WIF_SERVICE_ACCOUNT`: Your Workload Identity Federation service account
   - `GH_CLASSIC_PAT_TOKEN`: GitHub classic personal access token
   - `GH_FINE_GRAINED_PAT_TOKEN`: GitHub fine-grained personal access token
   - `SLACK_WEBHOOK_URL`: Slack webhook URL for notifications

2. Push to the `main` branch or manually trigger the workflow:
   - Push to `main`: Deploys to the development environment
   - Manual trigger: Choose the environment (dev, staging, prod)

## Environment Configuration

The MCP Server uses environment-specific configurations:

| Environment | Min Instances | Max Instances | CPU | Memory | Concurrency |
| ----------- | ------------- | ------------- | --- | ------ | ----------- |
| dev         | 0             | 5             | 1   | 512Mi  | 20          |
| staging     | 1             | 10            | 1   | 1Gi    | 40          |
| prod        | 2             | 100           | 2   | 2Gi    | 80          |

To customize the environment configuration:

1. For manual deployment: Use command-line options
2. For Pulumi deployment: Modify `locals.env_config` in `pulumi/main.py`
3. For CI/CD deployment: Modify environment variables in `.github/workflows/deploy.yml`

## Monitoring and Observability

The MCP Server includes comprehensive monitoring and observability:

1. **Custom Metrics**: Defined in `monitoring/monitoring.yaml`
2. **Dashboards**: Pre-configured dashboards for performance monitoring
3. **Alerts**: Alerts for high CPU/memory usage, error rates, etc.
4. **Uptime Checks**: Health checks for the MCP Server

To deploy the monitoring configuration:

```bash
cd mcp_server
python scripts/deploy_monitoring.py \
  --project-id cherry-ai-project \
  --service-name mcp-server \
  --environment dev \
  --notification-channel projects/cherry-ai-project/notificationChannels/123456789 \
  --service-url https://mcp-server-dev-abcdefghij-uc.a.run.app
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:

   - Ensure `GCP_MASTER_SERVICE_JSON` is correctly set
   - Verify the service account has the required permissions

2. **Deployment Failures**:

   - Check Cloud Build logs for build errors
   - Verify VPC connector exists and is properly configured

3. **Redis Connection Issues**:
   - Ensure VPC connector is properly configured
   - Check Redis instance status in GCP Console

### Logs and Debugging

To view logs:

```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-server" --project=cherry-ai-project --limit=10

# View Redis logs
gcloud logging read "resource.type=redis_instance AND resource.labels.instance_id=mcp-redis" --project=cherry-ai-project --limit=10
```

For more detailed debugging:

1. Enable debug logging by setting `DEBUG=true` in the environment variables
2. Use the Cloud Run console to view detailed logs and metrics
3. Check the Cloud Monitoring dashboards for performance metrics

### Support

For additional support:

1. Check the [MCP Server documentation](../README.md)
2. Open an issue on the GitHub repository
3. Contact the AI Orchestra team at support@example.com

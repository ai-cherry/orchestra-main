# MCP Server Deployment Guide for Lambda

This guide provides instructions for deploying the MCP Server to **Lambda** with performance-optimized settings. The deployment process is designed to be fast, reliable, and secure.

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

1.  **Lambda Account**: A Lambda account with billing enabled.
2.  **Lambda API Key**: Generated from your Lambda account panel with necessary permissions.
3.  **SSH Key**: An SSH key pair added to your Lambda account for instance access.
4.  **GitHub Tokens**: If using GitHub Actions for CI/CD:
    *   `GH_CLASSIC_PAT_TOKEN`: A classic personal access token with `repo` scope.
    *   `GH_FINE_GRAINED_PAT_TOKEN`: A fine-grained personal access token with `deployments` scope.
5.  **Required Tools**:
    *   `Lambda-cli` (Optional, but helpful for Lambda management)
    *   Docker
    *   Python 3.8+
    *   Poetry
    *   Pulumi (if using Pulumi deployment method)

## Deployment Options

The MCP Server can be deployed to Lambda using one of the following methods:

1.  **Manual Deployment**: Using a deployment script (e.g., `deploy_mcp_to_lambda.sh`)
2.  **Pulumi Deployment**: Using the Pulumi configuration with the Lambda provider.
3.  **CI/CD Deployment**: Using GitHub Actions workflow configured for lambda.

## Quick Start

For a quick deployment to a Lambda instance:

```bash
# Set environment variables
export LAMBDA_API_KEY="your_LAMBDA_API_KEY_here"
export Lambda_SSH_KEY_ID="your_Lambda_ssh_key_id" # ID of SSH key in Lambda

# Run the deployment script (ensure it's created and executable)
cd mcp_server
chmod +x deploy/deploy_mcp_to_lambda.sh # Example script name
./deploy/deploy_mcp_to_lambda.sh
```

## Detailed Deployment Steps

### 1. Manual Deployment (Using a Script like `deploy_mcp_to_lambda.sh`)

A script like `deploy_mcp_to_lambda.sh` would typically automate:
- Provisioning a Lambda VPS instance.
- Setting up the operating system and Docker.
- Cloning the repository.
- Building and running the MCP server Docker container.

```bash
# Example script execution
./deploy/deploy_mcp_to_lambda.sh \
  --api-key $LAMBDA_API_KEY \
  --ssh-key-id $Lambda_SSH_KEY_ID \
  --region "ewr" \        # Example: Newark
  --plan "vc2-2c-4gb" \   # Example: 2 CPU, 4GB RAM
  --os "ubuntu_22.04_x64" \ # Example: Ubuntu 22.04
  --service-name "mcp-server-prod" \
  --startup-script "mcp_server/deploy/startup_script.sh" # Script to run on instance boot
```

Available options for such a script would typically include:

| Option                | Description                                   | Example Value         |
| --------------------- | --------------------------------------------- | --------------------- |
| `--api-key`           | Lambda API Key                                 | (env var)             |
| `--ssh-key-id`        | ID of your SSH key in Lambda                   | (env var)             |
| `--region`            | Lambda region for deployment                   | `ewr`, `lax`, `fra`   |
| `--plan`              | Lambda instance plan (CPU, RAM, Storage)       | `vc2-2c-4gb`          |
| `--os`                | Operating system ID for the instance          | `ubuntu_22.04_x64`    |
| `--service-name`      | A label/hostname for your instance            | `mcp-server-prod`     |
| `--startup-script`    | Path to a startup script for instance setup   | `path/to/script.sh`   |
| `--app-port`          | Port the MCP server will listen on            | `8080`                |

*(Note: This `deploy_mcp_to_lambda.sh` script needs to be created. The above is an example of how it might be used.)*

### 2. Pulumi Deployment (Using Lambda Provider)

The Pulumi configuration (e.g., in `mcp_server/pulumi/Lambda_mcp/`) would define the Lambda instance and necessary resources.

```bash
# Initialize Pulumi for Lambda
cd mcp_server/pulumi/Lambda_mcp # Example path
pulumi login # Or pulumi login --local
pulumi stack init dev

# Configure Lambda API Key for Pulumi (if not set globally)
pulumi config set Lambda:apiKey YOUR_LAMBDA_API_KEY --secret

# Plan the deployment
pulumi preview \
  --config="Lambda:region=ewr" \
  --config="instancePlan=vc2-1c-2gb"

# Apply the deployment
pulumi up
```
*(Note: The Pulumi Python code for Lambda needs to be written in `mcp_server/pulumi/Lambda_mcp/`)*

### 3. CI/CD Deployment (Using GitHub Actions for Lambda)

The GitHub Actions workflow would automate deployment to Lambda:

1.  Set up the following secrets in your GitHub repository:
    *   `LAMBDA_API_KEY`: Your Lambda API Key.
    *   `SSH_PRIVATE_KEY`: Private SSH key for accessing the Lambda instance (if needed for provisioning).
    *   `SLACK_WEBHOOK_URL`: Slack webhook URL for notifications.

2.  The workflow (e.g., `.github/workflows/deploy_mcp_lambda.yml`) would typically:
    *   Build the Docker image for MCP Server.
    *   Push the image to a container registry (e.g., Docker Hub, Lambda Container Registry if available).
    *   Use `Lambda-cli` or an SSH-based script to update the running instance or provision a new one with the new image.

## Environment Configuration

The MCP Server can be configured for different environments (dev, staging, prod) typically by setting environment variables when running the Docker container on the Lambda instance. Lambda instance plans can be chosen to match environment needs:

| Environment | Recommended Lambda Plan (Example) | CPU | Memory | Notes                     |
| ----------- | ------------------------------ | --- | ------ | ------------------------- |
| dev         | `vc2-1c-1gb`                   | 1   | 1GB    | For testing, light load   |
| staging     | `vc2-2c-4gb`                   | 2   | 4GB    | For pre-production tests  |
| prod        | `vc2-4c-8gb` or larger        | 4+  | 8GB+   | Scaled for production load|

Configuration is managed via:
1.  **Startup Scripts**: For Lambda instances, use startup scripts to set environment variables and run the application.
2.  **Docker Environment Variables**: Pass variables when running the Docker container.
3.  **Pulumi Configuration**: Define instance types and environment variables in your Pulumi code.
4.  **CI/CD Variables**: Set environment-specific variables in your GitHub Actions workflow.

## Monitoring and Observability

For MCP Server instances deployed on Lambda:

1.  **Lambda Metrics**: Use the Lambda cloud console to monitor basic instance metrics (CPU, Disk I/O, Network).
2.  **Application Logs**: Configure the MCP server to output structured logs. Access these logs by SSHing into the instance and viewing log files or using a log management service.
3.  **Custom Monitoring**: Deploy Prometheus/Grafana on a Lambda instance or use a managed monitoring service to collect application-specific metrics from the MCP server.
    *   The MCP server should expose a `/metrics` endpoint for Prometheus.
4.  **Uptime Checks**: Use external services (e.g., UptimeRobot, StatusCake) to monitor the public endpoint of your MCP server.

## Troubleshooting

### Common Issues

1.  **Authentication Errors**:
    *   Ensure `LAMBDA_API_KEY` is correctly set and has the required permissions.
    *   Verify your SSH key is correctly added to Lambda and used for instance access.

2.  **Deployment Failures (Manual/Scripted)**:
    *   Check Lambda instance console for boot errors.
    *   Examine startup script logs (e.g., `/var/log/cloud-init-output.log` on Ubuntu).
    *   Ensure Docker is installed and running correctly on the instance.
    *   Check firewall rules on Lambda and within the instance OS.

3.  **Application Not Responding**:
    *   SSH into the instance and check Docker container logs (`docker logs <container_name_or_id>`).
    *   Verify the MCP server process is running inside the container.
    *   Check instance firewall and Lambda firewall settings.

### Logs and Debugging

To view logs on a Lambda instance:

```bash
# SSH into your Lambda instance

# View Docker container logs
docker ps # Find your MCP server container ID
docker logs <container_id>

# View application-specific log files (if configured)
# e.g., tail -f /app/logs/mcp_server.log
```

For more detailed debugging:
1.  Enable debug logging in the MCP server by setting `LOG_LEVEL=DEBUG` (or similar) environment variable.
2.  Use `Lambda-cli compute instance get <INSTANCE_ID>` for instance details.

### Support

For additional support:
1.  Check the [MCP Server documentation](../README.md)
2.  Open an issue on the GitHub repository
3.  Consult Lambda's documentation and support channels.

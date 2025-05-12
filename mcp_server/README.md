# MCP Server Deployment Guide

This guide provides instructions for deploying the MCP (Model Context Protocol) server to Google Cloud Platform (GCP) using the provided deployment scripts.

## Prerequisites

Before deploying the MCP server, ensure you have the following:

1. A GCP project with the following APIs enabled:
   - Cloud Run API
   - Container Registry API
   - Secret Manager API
   - IAM API

2. GitHub organization with the following secrets configured:
   - `GCP_PROJECT_ID`: The ID of your GCP project
   - `GCP_PROJECT_NUMBER`: The numeric ID of your GCP project
   - `GCP_REGION`: The GCP region to deploy to (e.g., `us-central1`)
   - `GCP_PROJECT_ADMIN_KEY`: Service account key with admin permissions
   - `GCP_SECRET_MANAGEMENT_KEY`: Service account key for secret management

3. Docker installed locally for building and testing the container

## Deployment Options

There are two ways to deploy the MCP server:

### 1. Setting Up Powerful Service Accounts

To set up powerful service accounts for Vertex AI and Gemini, run:

```bash
./setup_badass_credentials.sh
```

This script will:
1. Create a Vertex AI service account with extensive permissions
2. Create a Gemini service account with necessary permissions
3. Update GitHub organization secrets with the new service account keys

### 2. Manual Deployment

To deploy the MCP server manually, run the following command:

```bash
./deploy_mcp_server.sh [environment]
```

Where `[environment]` is optional and defaults to `dev`. Valid environments are `dev`, `staging`, and `prod`.

This script will:
1. Set up GCP credentials using the `GCP_PROJECT_ADMIN_KEY` environment variable
2. Update Poetry dependencies
3. Build a Docker image
4. Deploy the image to Cloud Run

## Environment Variables

The MCP server uses the following environment variables:

- `ENV`: The deployment environment (`dev`, `staging`, or `prod`)
- `PROJECT_ID`: The GCP project ID

## Troubleshooting

### Poetry Dependency and Startup Issues

If you encounter dependency resolution or MCP server startup issues, try the following:

1. Update Poetry to the latest version:
   ```bash
   pip install --upgrade poetry
   ```

2. Clear Poetry's cache:
   ```bash
   poetry cache clear --all pypi
   ```

3. Rebuild the lock file:
   ```bash
   poetry lock --no-update
   ```

4. Update dependencies:
   ```bash
   poetry update
   ```

5. If you're encountering import problems, check that the package structure is correct:
   - The `mcp_server` package should use absolute imports (e.g., `from mcp_server.config import load_config`)
   - Run the server using the provided helper script: `./start_mcp_server.sh`

### Running the MCP Server Locally

For development purposes, we've added a simple helper script to run the MCP server:

```bash
# From the project root
./start_mcp_server.sh
```

Alternatively, you can run it manually:

```bash
# Navigate to the mcp_server directory
cd mcp_server

# Install dependencies
poetry install

# Run the server
poetry run python -m mcp_server.run_mcp_server --config ./config.json
```

### Authentication Issues

If you encounter authentication issues with GCP, ensure that:

1. The `GCP_PROJECT_ADMIN_KEY` environment variable is set correctly
2. The service account has the necessary permissions
3. The service account key is valid and not expired

### Deployment Issues

If the deployment fails, check the Cloud Run logs for more information:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-server-dev" --limit=10
```

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)

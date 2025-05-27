# MCP Server Deployment Guide

This guide provides instructions for deploying the MCP (Model Context Protocol) server to
## Prerequisites

Before deploying the MCP server, ensure you have the following:

1. A
   -    - Container Registry API
   -    - IAM API

2. GitHub organization with the following secrets configured:

   - `   - `   - `   - `   - `   - `   - `
3. Docker installed locally for building and testing the container

## Deployment Options

There are three ways to deploy the MCP server:

### 1. Manual Deployment

To deploy the MCP server manually, run the following command:

```bash
./deploy_mcp_server.sh [environment]
```

Where `[environment]` is optional and defaults to `dev`. Valid environments are `dev`, `staging`, and `prod`.

This script will:

1. Set up 2. Update Poetry dependencies
3. Build a Docker image
4. Deploy the image to
### 2. Setting Up Powerful Service Accounts

To set up powerful service accounts for
```bash
./setup_badass_credentials.sh
```

This script will:

1. Create a 2. Create a Gemini service account with necessary permissions
3. Update GitHub organization secrets with the new service account keys

### 3. Automated Deployment with GitHub Actions

The repository includes a GitHub Actions workflow that automatically deploys the MCP server when changes are pushed to the `main` branch or when manually triggered.

To manually trigger a deployment:

1. Go to the "Actions" tab in the GitHub repository
2. Select the "Deploy MCP Server" workflow
3. Click "Run workflow"
4. Select the environment to deploy to (`dev`, `staging`, or `prod`)
5. Click "Run workflow"

## Environment Variables

The MCP server uses the following environment variables:

- `ENV`: The deployment environment (`dev`, `staging`, or `prod`)
- `PROJECT_ID`: The
## Troubleshooting

### Poetry Dependency Issues

If you encounter dependency resolution issues with Poetry, try the following:

1. Update Poetry to the latest version:

   ```bash
   pip install --upgrade poetry
   ```

2. Clear Poetry's cache:

   ```bash
   poetry cache clear --all pypi
   ```

3. Update dependencies:
   ```bash
   cd mcp_server && poetry update
   ```

### Authentication Issues

If you encounter authentication issues with
1. The `2. The service account has the necessary permissions
3. The service account key is valid and not expired

### Deployment Issues

If the deployment fails, check the
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-server-dev" --limit=10
```

## Additional Resources

- [- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)

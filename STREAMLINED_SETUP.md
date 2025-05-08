# Streamlined Orchestra Setup

This document provides instructions for setting up and deploying the Orchestra project using a streamlined, performance-focused approach.

## Overview

This implementation prioritizes:
- **Performance**: Optimized for speed and efficiency
- **Simplicity**: Streamlined setup and deployment
- **Development Speed**: Reduced complexity for faster iterations

## Prerequisites

Before you begin, you need:

1. **GCP Service Account Key**: Set as `GCP_MASTER_SERVICE_JSON` environment variable
2. **GitHub Personal Access Token**: Set as `GH_CLASSIC_PAT_TOKEN` environment variable (for GitHub Actions)
3. **Docker**: For building and running containers
4. **Python 3.11+**: For local development
5. **Poetry**: For dependency management

## Quick Start

### 1. Setup Development Environment

Run the setup script to prepare your development environment:

```bash
./setup_dev.sh
```

This script:
- Authenticates with GCP using your service account key
- Installs dependencies using Poetry
- Sets up environment variables
- Enables required GCP APIs
- Makes scripts executable

### 2. Direct Authentication

For quick GCP authentication:

```bash
./direct_auth.sh
```

This script:
- Authenticates with GCP using your service account key
- Sets up gcloud configuration
- Enables required GCP APIs

### 3. Deploy Infrastructure and Application

For one-command deployment:

```bash
./deploy_all.sh
```

This script:
- Authenticates with GCP
- Enables required APIs
- Deploys infrastructure with Terraform
- Builds and pushes Docker image
- Deploys to Cloud Run
- Outputs the service URL

## Components

### Terraform Configuration

The simplified Terraform configuration is located in `infra/simplified-terraform/`:

- `main.tf`: Core infrastructure (Redis, service accounts, APIs)
- `cloudsql.tf`: PostgreSQL database with pgvector
- `variables.tf`: Variable definitions

### Memory System

The performance-optimized memory system includes:

- `mcp_server/managers/performance_memory_manager.py`: Memory manager optimized for performance
- `app_performance.py`: FastAPI application with performance monitoring

### GitHub Actions

The simplified GitHub Actions workflow is in `.github/workflows/simplified-deploy.yml`.

## Performance Monitoring

The application includes built-in performance monitoring:

- `/metrics`: Returns performance metrics (request times, memory usage, CPU usage)
- `/health`: Returns health check information

## Security Considerations

This implementation prioritizes performance and development speed over security. See `SECURITY_DEBT.md` for details on security considerations that should be addressed as the project scales.

## Local Development

To run the application locally:

```bash
poetry run uvicorn app_performance:app --reload
```

## Customization

### Environment Variables

You can customize the deployment by setting environment variables:

- `PROJECT_ID`: GCP project ID (default: "cherry-ai-project")
- `REGION`: GCP region (default: "us-west4")
- `ENV`: Environment (default: "dev")

### Terraform Variables

You can customize the Terraform deployment by modifying `infra/simplified-terraform/variables.tf`.

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:

```bash
# Check authentication status
gcloud auth list

# Reauthenticate
./direct_auth.sh
```

### Deployment Issues

If deployment fails:

```bash
# Check Terraform state
cd infra/simplified-terraform
terraform state list

# Check Cloud Run service
gcloud run services describe orchestra-api --region us-west4
```

## Next Steps

1. Explore the API at the deployed URL
2. Add your application logic to `app_performance.py`
3. Customize the memory system for your specific needs
4. Review `SECURITY_DEBT.md` for future security improvements
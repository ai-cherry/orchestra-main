# AI Orchestra

AI Orchestra is a comprehensive platform for orchestrating AI models and workflows using Google Cloud Platform services, particularly Vertex AI and Gemini.

## Overview

This project provides a complete setup for deploying AI services on GCP, including:

- FastAPI application for serving AI models
- Vertex AI integration for model deployment and inference
- Gemini API integration for text generation
- Cloud Run deployment for scalable serving
- Terraform configuration for infrastructure as code
- GitHub Actions workflows for CI/CD

## Project Structure

```
.
├── .github/workflows/       # GitHub Actions workflows
├── packages/                # Python packages
│   └── api/                 # FastAPI application
├── scripts/                 # Shell scripts
├── terraform/               # Terraform configuration
│   └── modules/             # Terraform modules
├── .env                     # Environment variables
├── Dockerfile               # Docker configuration
├── pyproject.toml           # Poetry configuration
└── deploy.sh                # Consolidated deployment script
```

## Prerequisites

- Python 3.11+
- Poetry
- Google Cloud SDK
- Docker

## Setup

### Local Development

1. Install dependencies:

```bash
poetry install
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the API locally:

```bash
poetry run uvicorn packages.api.main:app --reload
```

### GCP Environment Setup

1. Set up non-interactive authentication (optional but recommended):

```bash
# Make the script executable
chmod +x setup_service_account.sh

# Run the service account setup script
./setup_service_account.sh
```

This eliminates browser-based authentication prompts during deployment.

2. Make the deployment script executable:

```bash
chmod +x deploy.sh
```

3. Run the deployment script:

```bash
./deploy.sh
```

This script will:
- Configure your GCP environment
- Build and push a Docker image to Artifact Registry
- Deploy the application to Cloud Run
- Verify the deployment

For more detailed instructions, see:
- [CLOUD_RUN_DEPLOYMENT_GUIDE.md](CLOUD_RUN_DEPLOYMENT_GUIDE.md) - Detailed deployment guide
- [NON_INTERACTIVE_AUTH_GUIDE.md](NON_INTERACTIVE_AUTH_GUIDE.md) - Non-interactive authentication guide
- [SIMPLE_DEPLOYMENT.md](SIMPLE_DEPLOYMENT.md) - Quick-start deployment guide
- [docs/GCP_DEPLOYMENT_GUIDE.md](docs/GCP_DEPLOYMENT_GUIDE.md) - GCP-specific deployment guide

## API Endpoints

The API provides the following endpoints:

- `GET /health`: Health check endpoint
- `GET /api/models`: List available AI models
- `POST /api/predict`: Make predictions using Vertex AI
- `POST /api/gemini`: Generate text using Gemini API
- `POST /api/orchestrate`: Orchestrate an AI workflow
- `GET /api/workflows/{execution_id}`: Get workflow status

## Deployment

AI Orchestra offers multiple deployment options:

### Script-Based Deployment

Use the consolidated deployment script with sensible defaults:

```bash
./deploy.sh
```

Or customize your deployment:

```bash
./deploy.sh \
  --project my-project-id \
  --region us-central1 \
  --service my-service \
  --env production \
  --min-instances 1 \
  --max-instances 10
```

### CI/CD Deployment

The project includes a GitHub Actions workflow for automated deployment:

1. **Automatic Staging Deployment**: Push to the main branch
2. **Manual Production Deployment**: Use the workflow dispatch with production environment

The workflow is defined in `.github/workflows/deploy-cloud-run.yml`.

### Environment-Specific Configuration

Create environment files for different deployment environments:

1. **Environment Variables**: Store in `.env.{environment}` files
   - Example: `.env.staging`, `.env.production`

2. **Secrets Configuration**: Define in `secrets.{environment}.txt` files

## Vertex AI Integration

The project integrates with Vertex AI for model deployment and inference. See [vertex_ai_setup.py](vertex_ai_setup.py) for utilities to manage Vertex AI resources.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

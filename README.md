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
└── setup_gcp_environment.sh # GCP environment setup script
```

## Prerequisites

- Python 3.11+
- Poetry
- Google Cloud SDK
- Terraform
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

1. Make the setup script executable:

```bash
chmod +x setup_gcp_environment.sh
```

2. Run the setup script:

```bash
./setup_gcp_environment.sh
```

This script will:
- Initialize the GCP workspace
- Deploy basic infrastructure
- Configure Vertex AI resources
- Deploy the application to Cloud Run
- Configure the data sync pipeline

For more detailed instructions, see [GCP_ENVIRONMENT_SETUP_GUIDE.md](GCP_ENVIRONMENT_SETUP_GUIDE.md).

## API Endpoints

The API provides the following endpoints:

- `GET /health`: Health check endpoint
- `GET /api/models`: List available AI models
- `POST /api/predict`: Make predictions using Vertex AI
- `POST /api/gemini`: Generate text using Gemini API
- `POST /api/orchestrate`: Orchestrate an AI workflow
- `GET /api/workflows/{execution_id}`: Get workflow status

## Deployment

### Manual Deployment

Deploy to Cloud Run:

```bash
gcloud run deploy orchestra-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

### CI/CD Deployment

Push to the main branch to trigger automatic deployment via GitHub Actions.

## Vertex AI Integration

The project integrates with Vertex AI for model deployment and inference. See [vertex_ai_setup.py](vertex_ai_setup.py) for utilities to manage Vertex AI resources.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

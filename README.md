# AI Orchestra - AI Orchestration System

AI Orchestra is a flexible orchestration system for AI agents, designed to manage interactions between users and AI models through a persona-based architecture.

## Overview

The system coordinates multiple AI agents, maintains conversation memory, provides a unified API for client applications, and handles different LLM providers with robust fallback mechanisms.

## Key Features

- **Persona-Based Interactions**: Dynamic personality selection for contextual responses
- **Memory Management**: Conversation history storage with semantic search capabilities
- **LLM Provider Abstraction**: Support for multiple providers with fallback mechanisms
- **Agent Orchestration**: Coordinate multiple specialized AI agents
- **FastAPI Backend**: Modern, asynchronous API implementation

## System Architecture

The system follows a modular design with clearly separated concerns:

- **Core** (`/core/orchestrator/`): Core orchestration logic and API endpoints
- **Packages** (`/packages/`): Shared libraries for memory, agents, and personas
- **Tests** (`/tests/`): Comprehensive test suite for all components
- **Infrastructure** (`/infra/`): Deployment configuration

## Quick Start

1. Set up environment with required API keys:

```bash
cp .env.example .env
# Edit .env to add your API keys
```

2. Start the API server:

```bash
./run_api.sh
```

3. Test the API with sample requests:

```bash
python test_personas_api_manually.py
```

## Documentation

- **API Documentation**: Available at `http://localhost:8000/docs` when running locally
- **Architecture**: See `AI_CONTEXT.md` for a comprehensive system overview
- **Memory System**: Detailed in `packages/shared/src/memory/MEMORY_CONTEXT.md`
- **LLM Providers**: Explained in `core/orchestrator/src/services/llm/LLM_PROVIDER_CONTEXT.md`
- **Deployment**: Production deployment guidance in `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

## Deployment

Orchestra provides a streamlined deployment process for both development and production environments using **Google Cloud Run** as the primary deployment target. For detailed information on our deployment approach and rationale, see the [Deployment Strategy](./DEPLOYMENT_STRATEGY.md) document.

### Development Deployment

Verify your development setup before proceeding to production:

```bash
./run_pre_deployment_automated.sh
```

This runs comprehensive checks including environment validation, integrated services connectivity, and test validations.

### Secret Management in CI/CD

We've implemented secure secret management in our CI/CD pipeline. Key features:

- Secrets stored in GitHub Secrets and GCP Secret Manager
- Automated secret handling during deployments
- Pre-commit hooks to prevent accidental secret commits
- IAM-based access control

See [Secret Management CI/CD Documentation](docs/SECRET_MANAGEMENT_CICD.md) for details.

To set up the pre-commit hook for local development:
```bash
./scripts/install-pre-commit-hook.sh
```

### Production Deployment

Orchestra uses a two-service architecture:
1. **Orchestra API**: The main backend service
2. **Phidata Agent UI**: A placeholder frontend UI that connects to the API

For production deployment, follow these steps:

1. Setup production secrets:
   ```bash
   ./scripts/setup_prod_secrets.sh
   ```

2. Run the production deployment script:
   ```bash
   ./deploy_to_production.sh
   ```

The production deployment script guides you through:
- Prerequisite verification
- Secret configuration
- Infrastructure deployment via Terraform (deploying both API and UI services)
- Application deployment
- Post-deployment validation of both services
- Monitoring setup

After deployment, you'll have two Cloud Run services:
- `orchestrator-api-prod`: The Orchestra backend API
- `phidata-agent-ui-prod`: The Phidata Agent UI frontend

For detailed deployment documentation, refer to the [Production Deployment Guide](./docs/PRODUCTION_DEPLOYMENT_GUIDE.md) and the [Deployment Strategy](./DEPLOYMENT_STRATEGY.md).

## Development

This project is developed using a containerized environment for consistency:
- Python 3.11
- FastAPI for API development
- Pydantic for data validation
- DevContainer configuration for VS Code

For detailed development information, see the `.devcontainer` directory.

## Workspace Setup and Usage

### Google Cloud Code (Gemini) Setup

#### Features
- **Cloud Build Integration**: Automate builds and deployments using `cloudbuild.yaml`.
- **Cloud Run Debugging**: Debug applications deployed to Cloud Run.
- **AI Assistance**: Use Gemini for code suggestions and deployment guidance.

#### Usage
1. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project <PROJECT_ID>
   ```
2. **Run Cloud Build Pipelines**:
   - Use the following tasks in VS Code:
     - `Run Cloud Build Pipeline`
     - `Run Data Sync Pipeline`
     - `Run Migration Pipeline`
3. **Deploy to Cloud Run**:
   - Use the `Deploy to Cloud Run` task or run:
     ```bash
     gcloud run deploy --image=gcr.io/my-project/my-image
     ```

#### Debugging
- Use Google Cloud Code's debugging tools to debug applications locally or in Cloud Run.

### Roo Code and MCP

#### MCP Servers
- **Terraform Helper**: Automates Terraform plan generation.
- **GCP Deployer**: Automates deployment to Google Cloud Run.
- **DB Migrator**: Handles database migrations.
- **API Tester**: Tests API endpoints.

#### Roo Code Modes
- **Architect Mode**: For system design and planning.
- **Code Mode**: For general development with auto-complete, linting, and formatting.
- **Debug Mode**: For troubleshooting and diagnostics.
- **Orchestrator Mode**: For workflow orchestration and task delegation.

#### Automated Tasks
- **Terraform Plan**: Run `terraform plan` to preview infrastructure changes.
- **Deploy to Cloud Run**: Deploy applications to Google Cloud Run.
- **Run Cloud Build Pipelines**: Automate builds and deployments.

## Enhanced Tool Usage

### Terraform Workflows
- **Terraform Validate**: Ensures Terraform configurations are valid.
- **Terraform Apply**: Applies infrastructure changes automatically.
- **Pre-Commit Hooks**: Enforces validation and linting before commits.

### Google Cloud Code (Gemini)
- **Cloud Build Pipelines**:
  - `Run Cloud Build Pipeline`: Automates builds and deployments.
  - `Run Data Sync Pipeline`: Synchronizes data workflows.
  - `Run Migration Pipeline`: Executes migration workflows.
- **Cloud Run Deployment**:
  - Use the `Deploy to Cloud Run` task for deploying containerized applications.

### Roo Code Modes
- **Terraform Mode**:
  - Focused on infrastructure management and validation.
  - Supports `.tf` and `.tfvars` files.
- **Deployment Mode**:
  - Optimized for GCP deployment workflows.
  - Supports `.yaml` and `.json` files.

### MCP Servers
- **Terraform Helper**: Automates Terraform planning.
- **GCP Deployer**: Manages Cloud Run deployments.
- **Secret Manager**: Handles secure secret management.
- **Pipeline Monitor**: Monitors CI/CD pipelines.

### Pre-Approvals
- All MCP tools are pre-approved for seamless usage.

### Debugging and Validation
- Use Roo Code's `Debug Mode` for troubleshooting.
- Validate environments with `diagnose_environment.py`.

### CI/CD Integration
- Integrate Terraform and GCP workflows into CI pipelines.

### Troubleshooting
- Restart VS Code if extensions or Roo Code are not responding.
- Check `.roo/mcp.json` for MCP server configurations.

### Secure API Keys
- Store API keys in environment variables or VS Code Secret Storage.

### Pre-Commit Hooks
- Use `husky` to enforce linting and validation before commits.

### CI/CD Integration
- Integrate Terraform and GCP workflows into CI pipelines.

### Troubleshooting
- Restart VS Code if extensions or Roo Code are not responding.
- Check `.roo/mcp.json` for MCP server configurations.

## Updated Workspace Setup

### Docker and Poetry
- **Dockerfile**:
  - Now uses Poetry for dependency management.
  - Automatically installs dependencies from `poetry.lock` and `pyproject.toml`.
- **Docker Compose**:
  - Added `docker-compose.yml` for simplified multi-container setups.
  - Run the application with:
    ```bash
    docker-compose up
    ```

### Pre-Commit Hooks
- **Setup**:
  - Install pre-commit hooks with:
    ```bash
    pip install pre-commit
    pre-commit install
    ```
- **Enforced Checks**:
  - Terraform validation and linting.
  - Python formatting with Black.

### Environment Validation
- Use the `diagnose_environment.py` script to validate the development environment:
  ```bash
  python diagnose_environment.py
  ```

### Recommended Extensions
- Python, Docker, Terraform, YAML, GitLens, Google Cloud Code, Roo Code, ShellCheck, EditorConfig, and Code Spell Checker.

## License

This project is proprietary and not licensed for external use or distribution.

# Container Management Optimization Plan for AI Orchestra

This document outlines a comprehensive plan to stabilize and optimize container management across the AI Orchestra project, addressing dependency issues, redundancies, and inconsistencies.

## 1. Project ID Standardization

**Issue:** The codebase contains 277+ references to `cherry-ai-project` which should be `cherry-ai-project`.

**Solution:**
1. Use the `update-project-id.sh` script to automatically update all references:
   ```bash
   ./update-project-id.sh
   ```
2. Manually verify critical files after the update:
   - Terraform configurations
   - GitHub Actions workflows
   - Docker configurations
   - Service account references

## 2. Poetry Configuration Standardization

**Issue:** Inconsistent Poetry versions (1.6.1 in CI/CD vs 1.7.1 in Dockerfile/DevContainer)

**Solution:**
1. Standardize on Poetry 1.7.1 across all environments
2. Update CI/CD workflow:
   ```yaml
   - name: Install Poetry
     uses: snok/install-poetry@v1
     with:
       version: 1.7.1
       virtualenvs-create: true
       virtualenvs-in-project: true
   ```
3. Ensure consistent dependency groups in pyproject.toml:
   - Core dependencies
   - Development dependencies
   - Test dependencies

## 3. Docker Configuration Optimization

**Issue:** Multiple Dockerfiles with different approaches and redundant steps

**Solution:**
1. Consolidate Docker build stages:
   - Create a common base image with shared dependencies
   - Use multi-stage builds consistently
   - Implement proper layer caching

2. Optimize the main Dockerfile:
   ```dockerfile
   # Base stage with common dependencies
   FROM python:3.11-slim AS base

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       curl \
       gcc \
       build-essential \
       git \
       && rm -rf /var/lib/apt/lists/*

   # Install Poetry
   ENV POETRY_HOME=/opt/poetry
   ENV POETRY_VIRTUALENVS_IN_PROJECT=true
   ENV POETRY_NO_INTERACTION=1
   ENV PATH="$POETRY_HOME/bin:$PATH"

   RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.7.1

   # Set working directory
   WORKDIR /app

   # Copy project configuration
   COPY pyproject.toml poetry.lock* ./

   # Development stage
   FROM base AS development
   RUN poetry install --with dev

   # Production stage
   FROM base AS production
   RUN poetry install --only main

   # Copy application code
   COPY core /app/core
   COPY shared /app/shared
   COPY config /app/config

   # Set environment variables
   ENV PYTHONPATH=/app
   ENV PORT=8080
   ENV GCP_PROJECT_ID=cherry-ai-project
   ENV GCP_REGION=us-west4

   # Expose the port
   EXPOSE ${PORT}

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:${PORT}/health || exit 1

   # Command to run the application
   CMD ["poetry", "run", "uvicorn", "core.orchestrator.src.api.app:app", "--host", "0.0.0.0", "--port", "${PORT}"]
   ```

3. Update docker-compose.yml to use environment variables from a central source:
   ```yaml
   version: '3.8'

   services:
     orchestra-api:
       build:
         context: .
         dockerfile: Dockerfile
         target: development
       ports:
         - "8000:8000"
       env_file:
         - .env.development
       volumes:
         - ./core:/app/core
         - ./packages:/app/packages
       networks:
         - orchestra-network
       depends_on:
         - redis
         - postgres
   ```

## 4. DevContainer Stability Improvements

**Issue:** Complex postCreateCommand and potential instability

**Solution:**
1. Update .devcontainer/devcontainer.json:
   ```json
   {
     "name": "AI Orchestra Dev Container",
     "image": "mcr.microsoft.com/devcontainers/python:3.11-bullseye",
     "features": {
       "ghcr.io/devcontainers/features/terraform:1": {
         "version": "1.5.7"
       },
       "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {},
       "ghcr.io/devcontainers/features/google-cloud-cli:1": {},
       "ghcr.io/devcontainers/features/github-cli:1": {}
     },
     "customizations": {
       "vscode": {
         "extensions": [
           "ms-python.python",
           "ms-python.vscode-pylance",
           "hashicorp.terraform",
           "ms-azuretools.vscode-docker",
           "googlecloudtools.cloudcode",
           "github.copilot",
           "ms-python.black-formatter",
           "ms-python.flake8"
         ],
         "settings": {
           "python.defaultInterpreterPath": "/workspaces/orchestra-main/.venv/bin/python",
           "python.linting.enabled": true,
           "python.linting.flake8Enabled": true,
           "python.formatting.provider": "black",
           "editor.formatOnSave": true,
           "editor.codeActionsOnSave": {
             "source.organizeImports": true
           },
           "python.formatting.blackArgs": [
             "--line-length",
             "100"
           ],
           "python.linting.flake8Args": [
             "--max-line-length=100",
             "--ignore=E203,W503"
           ]
         }
       }
     },
     "postCreateCommand": "./.devcontainer/setup.sh",
     "remoteUser": "vscode",
     "remoteEnv": {
       "PYTHONPATH": "${containerWorkspaceFolder}",
       "GCP_PROJECT_ID": "cherry-ai-project",
       "GCP_REGION": "us-west4"
     }
   }
   ```

2. Create a more robust .devcontainer/setup.sh:
   ```bash
   #!/bin/bash
   set -e

   echo "Setting up AI Orchestra development environment..."

   # Install Poetry
   echo "Installing Poetry 1.7.1..."
   curl -sSL https://install.python-poetry.org | python3 - --version 1.7.1
   echo "export PATH=\"$HOME/.local/bin:$PATH\"" >> ~/.bashrc
   source ~/.bashrc

   # Configure Poetry
   echo "Configuring Poetry..."
   cd /workspaces/orchestra-main
   poetry config virtualenvs.in-project true

   # Install dependencies
   echo "Installing project dependencies..."
   poetry install --with dev

   # Set up pre-commit hooks
   echo "Setting up pre-commit hooks..."
   poetry run pre-commit install

   echo "Setup complete!"
   ```

## 5. CI/CD Pipeline Optimization

**Issue:** Multiple overlapping workflows, inconsistent configurations

**Solution:**
1. Consolidate GitHub Actions workflows:
   ```yaml
   name: AI Orchestra CI/CD Pipeline

   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main, develop ]

   jobs:
     test:
       name: Test and Lint
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         
         - name: Install Poetry
           uses: snok/install-poetry@v1
           with:
             version: 1.7.1
             virtualenvs-create: true
             virtualenvs-in-project: true
         
         - name: Load cached venv
           id: cached-poetry-dependencies
           uses: actions/cache@v3
           with:
             path: .venv
             key: venv-${{ runner.os }}-python-3.11-${{ hashFiles('**/poetry.lock') }}
         
         - name: Install dependencies
           run: poetry install --with dev
         
         - name: Lint with flake8
           run: poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
           
         - name: Test with pytest
           run: poetry run pytest tests/ --cov=./ --cov-report=xml
     
     deploy-dev:
       name: Deploy to Development
       needs: test
       if: github.ref == 'refs/heads/develop'
       runs-on: ubuntu-latest
       permissions:
         contents: read
         id-token: write
       steps:
         - uses: actions/checkout@v3
         
         - name: Authenticate to Google Cloud
           id: auth
           uses: google-github-actions/auth@v2
           with:
             workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
             service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
         
         - name: Set up Cloud SDK
           uses: google-github-actions/setup-gcloud@v2
           with:
             project_id: cherry-ai-project
         
         - name: Submit Cloud Build
           run: |-
             gcloud builds submit . \
               --config cloudbuild.yaml \
               --region=us-west4 \
               --substitutions=_ENV=dev,_GCP_REGION=us-west4 \
               --timeout=20m
     
     deploy-prod:
       name: Deploy to Production
       needs: test
       if: github.ref == 'refs/heads/main'
       runs-on: ubuntu-latest
       permissions:
         contents: read
         id-token: write
       environment: production
       steps:
         - uses: actions/checkout@v3
         
         - name: Authenticate to Google Cloud
           id: auth
           uses: google-github-actions/auth@v2
           with:
             workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
             service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
         
         - name: Set up Cloud SDK
           uses: google-github-actions/setup-gcloud@v2
           with:
             project_id: cherry-ai-project
         
         - name: Submit Cloud Build
           run: |-
             gcloud builds submit . \
               --config cloudbuild.yaml \
               --region=us-west4 \
               --substitutions=_ENV=prod,_GCP_REGION=us-west4 \
               --timeout=20m
   ```

2. Update cloudbuild.yaml to use environment variables:
   ```yaml
   steps:
   # Setup Python and dependencies
   - name: 'python:3.11-slim'
     id: 'install-dependencies'
     entrypoint: 'bash'
     args:
       - '-c'
       - |
         pip install poetry
         poetry install
         
   # Run linting and formatting checks
   - name: 'python:3.11-slim'
     id: 'linting'
     entrypoint: 'bash'
     args:
       - '-c'
       - |
         pip install poetry
         poetry install
         poetry run black --check . || echo "Warning: Formatting check with black failed."
         poetry run isort --check-only --diff . || echo "Warning: Import sorting check with isort failed."
         poetry run flake8 . || echo "Warning: Linting check with flake8 failed."
         
   # Run critical tests
   - name: 'python:3.11-slim'
     id: 'critical-tests'
     entrypoint: 'bash'
     args:
       - '-c'
       - |
         pip install poetry
         poetry install
         export PYTHONPATH=$(pwd)
         poetry run pytest tests/ -m critical -v
         
   # Build and push Docker image
   - name: 'gcr.io/cloud-builders/docker'
     id: 'build-docker-image'
     args:
       - 'build'
       - '-t'
       - 'us-docker.pkg.dev/${PROJECT_ID}/orchestra/app:${_ENV}-${SHORT_SHA}'
       - '.'
       
   - name: 'gcr.io/cloud-builders/docker'
     id: 'push-docker-image'
     args:
       - 'push'
       - 'us-docker.pkg.dev/${PROJECT_ID}/orchestra/app:${_ENV}-${SHORT_SHA}'
       
   # Deploy to Cloud Run with secrets from Secret Manager
   - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
     id: 'deploy-cloud-run'
     entrypoint: 'bash'
     args:
       - '-c'
       - |
         # Get the secrets
         OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=OPENAI_API_KEY)
         PORTKEY_API_KEY=$(gcloud secrets versions access latest --secret=PORTKEY_API_KEY)
         
         # Deploy to Cloud Run with secrets
         gcloud run deploy orchestra-${_ENV} \
           --image=us-docker.pkg.dev/${PROJECT_ID}/orchestra/app:${_ENV}-${SHORT_SHA} \
           --set-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest,PORTKEY_API_KEY=PORTKEY_API_KEY:latest \
           --region=${_GCP_REGION} \
           --project=${PROJECT_ID} \
           --service-account=vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com
           
   # Default timeout is 10 minutes
   timeout: 1800s
   
   # Use environment variables
   options:
     logging: CLOUD_LOGGING_ONLY
     machineType: 'E2_HIGHCPU_8'
     env:
       - 'PYTHONUNBUFFERED=1'
       - 'PROJECT_ID=${PROJECT_ID}'
       
   # Use a service account with the necessary permissions
   serviceAccount: 'projects/${PROJECT_ID}/serviceAccounts/vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com'
   
   # Artifacts configuration for storing build outputs
   artifacts:
     objects:
       location: 'gs://${PROJECT_ID}-cloudbuild-artifacts/'
       paths: ['scan-results.json']
   ```

## 6. Implementation Plan

1. **Phase 1: Project ID Migration**
   - Run the update-project-id.sh script
   - Verify critical files
   - Test local development environment

2. **Phase 2: DevContainer Stabilization**
   - Update devcontainer.json
   - Create setup.sh script
   - Test DevContainer rebuild

3. **Phase 3: Docker Optimization**
   - Update Dockerfile
   - Update docker-compose.yml
   - Test local Docker builds

4. **Phase 4: CI/CD Pipeline Update**
   - Consolidate GitHub Actions workflows
   - Update cloudbuild.yaml
   - Test CI/CD pipeline with a small change

5. **Phase 5: Verification**
   - Verify all environments use consistent versions
   - Run end-to-end tests
   - Document the changes

## 7. Benefits

- **Stability:** Consistent environment configurations reduce "works on my machine" issues
- **Maintainability:** Centralized configuration makes updates easier
- **Performance:** Optimized Docker builds reduce build times and image sizes
- **Security:** Proper secret management improves security posture
- **Developer Experience:** Streamlined setup reduces onboarding time
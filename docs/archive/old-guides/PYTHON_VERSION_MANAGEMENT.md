# Python Version Management for AI Orchestra

This document outlines the approach for managing multiple Python versions across different services in the AI Orchestra project.

## Overview

AI Orchestra uses multiple Python versions for different services:

- **Core Services**: Python 3.11
- **Ingestion Service**: Python 3.10
- **LLM Test Service**: Python 3.11
- **Phidata Agents**: Python 3.11

This approach allows each service to use the optimal Python version for its dependencies while maintaining a consistent development environment.

## Development Environment Setup

### 1. DevContainer Configuration

The DevContainer is configured to use pyenv for managing multiple Python versions. When you open the project in VS Code with the Dev Containers extension, it will:

1. Install pyenv
2. Install Python 3.10.9 and 3.10.13
3. Set Python 3.10.9 as the global default
4. Install Poetry 1.7.1
5. Set up the project's dependencies

### 2. Service-Specific Python Environments

To work on a specific service:

```bash
# Set up the Python environment for a service
./scripts/setup_python_env.sh <service_name>

# Set up the Poetry environment for the service
./scripts/setup_poetry_env.sh <service_name>

# Activate the environment
cd .python-envs/<service_name> && poetry shell
```

Available services: `core`, `ingestion`, `llm-test`, `phidata`

### 3. CI/CD Pipeline

The CI/CD pipeline is configured to use pyenv for managing Python versions. It will:

1. Install pyenv
2. Install the required Python versions
3. Use the appropriate Python version for each service

## Docker Builds

The project includes a multi-stage Dockerfile that supports building images for different services with their appropriate Python versions.

To build a Docker image for a specific service:

```bash
# Build the Docker image for a service
./scripts/build_docker.sh --service <service_name>

# Build and push to GCR
./scripts/build_docker.sh --service <service_name> --push
```

## Benefits of This Approach

1. **Dependency Isolation**: Each service has its own isolated Python environment, preventing dependency conflicts.

2. **Version-Specific Optimizations**: Services can use the optimal Python version for their specific requirements.

3. **Consistent Development**: All developers work with the same Python versions and dependencies, reducing "works on my machine" issues.

4. **CI/CD Stability**: The CI/CD pipeline uses the same Python versions as development, ensuring consistent builds.

5. **Deployment Flexibility**: Docker images are built with the appropriate Python version for each service.

## Troubleshooting

If you encounter issues with Python versions or dependencies:

1. Ensure pyenv is installed and configured correctly
2. Check that the correct Python version is active for the service you're working on
3. Verify that Poetry is using the correct Python version
4. Try recreating the environment: `rm -rf .python-envs/<service_name> && ./scripts/setup_python_env.sh <service_name> && ./scripts/setup_poetry_env.sh <service_name>`

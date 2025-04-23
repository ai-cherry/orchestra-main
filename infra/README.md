# Orchestra Infrastructure

This directory contains the Terraform configurations for the Orchestra platform infrastructure on Google Cloud Platform.

## Overview

Orchestra uses a standard Terraform approach for infrastructure management, organized by environment with shared modules for common components.

## Directory Structure

- **`dev/`**: Development environment configuration
- **`prod/`**: Production environment configuration
- **`modules/`**: Reusable Terraform modules
  - `cloud-run/`: Cloud Run service configuration
  - `firestore/`: Firestore database configuration
  - `pubsub/`: Pub/Sub topics and subscriptions
  - `vertex/`: Vertex AI Vector Search configuration

## Quick Start

```bash
# Development environment
cd dev
terraform init
terraform workspace new dev  # first time only
terraform apply -var="env=dev"

# Production environment
cd ../prod
terraform init
terraform workspace new prod  # first time only
terraform apply -var="env=prod"
```

## Documentation

For comprehensive documentation on the infrastructure setup and operations, see [docs/infra.md](../docs/infra.md).

## Key Features

- **Environment Isolation**: Separate configurations for dev and prod environments
- **Modular Design**: Reusable modules for consistent configuration across environments
- **Standard Workflow**: Uses standard Terraform commands for clear, auditable infrastructure changes
- **Workspace Support**: Uses Terraform workspaces for state management

## Requirements

- Terraform 1.5+
- Google Cloud SDK
- Access to the `agi-baby-cherry` GCP project
- Authentication via service account (see documentation)

## Notes for RC-Arena Non-Profit Project

The infrastructure can support the RC-Arena Non-Profit project in the same GCP project using a separate Terraform workspace. See the documentation for details on creating a `nonprofit` workspace.

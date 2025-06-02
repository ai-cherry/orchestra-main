# Orchestra Infrastructure Documentation

This document describes the infrastructure setup for the Orchestra platform using Pulumi on
## Overview

Orchestra's infrastructure is managed using Pulumi and deployed on
### Key Components

- **- **MongoDB
- **Pub/Sub**: Event bus for communication between services
- **- **- **Artifact Registry**: Stores Docker images

## Directory Structure

```
infra/
├── dev/                 # Development environment configuration
│   └── main.py
├── prod/                # Production environment configuration
│   └── main.py
├── modules/             # Shared Pulumi modules
│   ├── cloud-run/       # │   ├── MongoDB
│   ├── pubsub/          # Pub/Sub topics module
│   └── vertex/          # └── README.md            # Infrastructure overview
```

## Prerequisites

Before you begin, ensure you have:

1. [2. [Pulumi](https://www.pulumi.io/downloads.html) (version 1.5+ recommended) installed
3. Access to the `cherry-ai-project` 4. A service account key with appropriate permissions

## Authentication

To authenticate with
```bash
# Using a service account key
echo "$gcloud auth activate-service-account --key-file=/tmp/gsa-key.json

# Set default project and region
gcloud config set project cherry-ai-project
gcloud config set run/region us-west2
```

## Standard Pulumi Workflow

### 1. Initialize Pulumi

First, navigate to the appropriate environment directory and initialize Pulumi:

```bash
cd infra/dev  # or infra/prod
pulumi init
```

This will download the required providers and set up the Pulumi working directory.

### 2. Create a New Workspace (First Time Only)

```bash
pulumi workspace new dev  # or prod
```

### 3. Select an Existing Workspace

```bash
pulumi workspace select dev  # or prod
```

### 4. Plan the Changes

Before applying changes, review what Pulumi will do:

```bash
pulumi plan -var="env=dev"  # or -var="env=prod"
```

This will show you what resources will be created, modified, or deleted.

### 5. Apply the Changes

Once you're satisfied with the plan, apply the changes:

```bash
pulumi apply -var="env=dev"  # or -var="env=prod"
```

Pulumi will ask for confirmation before proceeding.

### 6. Destroy Resources (When Needed)

To tear down the infrastructure:

```bash
pulumi destroy -var="env=dev"  # or -var="env=prod"
```

**CAUTION**: This will remove all resources. Use with care, especially in production.

## Environment-Specific Configurations

### Development Environment

- Minimum instances: 0 (scales to zero when idle)
- Maximum instances: 20
- Features full development setup with lower resource allocation

### Production Environment

- Minimum instances: 1 (always running)
- Maximum instances: 50
- Higher replication for better availability

## CI/CD Integration

To integrate with CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Pulumi

on:
  push:
    branches: [main]
    paths: ["infra/**"]
  pull_request:
    branches: [main]
    paths: ["infra/**"]

jobs:
  pulumi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Pulumi
        uses: pulumi/setup-pulumi@v2

      - name: Authenticate to         uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.
      - name: Initialize Pulumi
        working-directory: infra/dev # or infra/prod
        run: pulumi init

      - name: Pulumi Plan
        working-directory: infra/dev # or infra/prod
        run: pulumi plan -var="env=dev" # or -var="env=prod"

      # Only apply on push to main
      - name: Pulumi Apply
        if: github.event_name == 'push'
        working-directory: infra/dev # or infra/prod
        run: pulumi apply -auto-approve -var="env=dev" # or -var="env=prod"
```

## Remote State Management

For team environments, consider using a remote state backend. To enable this:

1. Uncomment the backend configuration in `main.py`
2. Create a GCS bucket for Pulumi state:

```bash
gsutil mb -l us-west2 gs://cherry-ai-project-pulumi-state
gsutil versioning set on gs://cherry-ai-project-pulumi-state
```

3. Re-initialize Pulumi to migrate state:

```bash
pulumi init -migrate-state
```

## Best Practices

1. **Version Control**: Always commit Pulumi changes to version control
2. **Plan Before Apply**: Always run `pulumi plan` before `pulumi apply`
3. **Use Workspaces**: Keep environments separate with workspaces
4. **Protect Secrets**: Never commit sensitive values to version control
5. **Lock State**: Use remote state with locking for team workflows

## Testing Infrastructure Changes

For significant changes, consider testing using a temporary environment:

```bash
pulumi workspace new test-feature
pulumi apply -var="env=test"
# Verify changes work as expected
pulumi destroy -var="env=test"
pulumi workspace select dev
pulumi workspace delete test-feature
```

## Troubleshooting

### Common Issues

- **Authentication errors**: Ensure your service account has the necessary permissions
- **Pulumi state lock**: If a lock persists after an interrupted operation, use `pulumi force-unlock`
- **Resource conflicts**: If resources already exist, consider importing them with `pulumi import`

### Getting Help

For assistance with infrastructure issues:

- Check the [Pulumi - Review the module code in `infra/modules/`
- Consult the Orchestra team Slack channel

## RC-Arena Non-Profit Project Integration

To deploy infrastructure for the RC-Arena Non-Profit project:

1. Create a new workspace for the non-profit project:

   ```bash
   cd infra/dev
   pulumi workspace new nonprofit
   ```

2. Apply with appropriate variables:
   ```bash
   pulumi apply -var="env=nonprofit"
   ```

This allows sharing the same message bus and other infrastructure components.

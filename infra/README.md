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
- Access to the `cherry-ai-project` GCP project
- Authentication via service account (see documentation)

## Notes for RC-Arena Non-Profit Project

The infrastructure can support the RC-Arena Non-Profit project in the same GCP project using a separate Terraform workspace. See the documentation for details on creating a `nonprofit` workspace.

# Pulumi GCP Infrastructure

This directory contains a Pulumi program to provision Google Cloud Platform (GCP) resources for this project.

## Prerequisites

1.  **Install Pulumi**: Follow the instructions at [pulumi.com/docs/get-started/install/](https://pulumi.com/docs/get-started/install/).
2.  **Configure GCP Credentials**: Ensure you have authenticated with GCP and set up your credentials for Pulumi. Refer to [pulumi.com/docs/intro/cloud-providers/gcp/setup/](https://pulumi.com/docs/intro/cloud-providers/gcp/setup/).
    Typically, this involves running:
    ```bash
    gcloud auth application-default login
    ```
3.  **Install Python**: This Pulumi program is written in Python (>=3.7 recommended).
4.  **Install Python Dependencies**: Navigate to this `infra` directory and install the required Python packages:
    ```bash
    cd infra
    pip install pulumi pulumi_gcp
    ```
5.  **Pulumi Backend**: Ensure you are logged into a Pulumi backend. By default, this is the Pulumi SaaS backend ([app.pulumi.com](https://app.pulumi.com)). You can log in using:
    ```bash
    pulumi login
    ```
    Alternatively, you can use a self-managed backend (e.g., Google Cloud Storage). See [pulumi.com/docs/intro/concepts/state/](https://pulumi.com/docs/intro/concepts/state/).

## Project Setup

1.  **Create a Pulumi Project (if not already done by this script)**:
    Pulumi projects are typically initialized once. If this `infra` directory doesn't behave as a Pulumi project, you might need to run `pulumi new python --dir . -y` inside it. However, the necessary `__main__.py` and `Pulumi.yaml` (implicitly created by stack selection) should be enough.

2.  **Create a Pulumi Stack**:
A stack is an isolated instance of your Pulumi program. We'll use a stack named `dev`.
    ```bash
    pulumi stack init dev
    ```
    This will create a `Pulumi.dev.yaml` file if it doesn't exist, or select it if it does.

3.  **Configure the Stack**:
    Edit the `infra/Pulumi.dev.yaml` file with your specific configuration values:
    *   `gcp:project`: Your Google Cloud project ID.
    *   `gcp:region`: Your preferred GCP region (e.g., `us-central1`).
    *   `cloudRunImage`: The full path to your Docker image in Artifact Registry or Google Container Registry (e.g., `us-central1-docker.pkg.dev/YOUR_PROJECT/YOUR_REPO/YOUR_IMAGE:tag` or `gcr.io/YOUR_PROJECT/YOUR_IMAGE:tag`).
    *   `githubRepoOwner`: Your GitHub username or organization name.
    *   `githubRepoName`: The name of your GitHub repository.
    *   `cloudRunServiceAccountEmail` (Optional): If your Cloud Run service uses a specific service account for accessing secrets, provide its email.
    *   `secretIdToAccess` (Optional): If `cloudRunServiceAccountEmail` is set, specify the ID of the secret in Secret Manager that this service account should be granted access to.

    Example `Pulumi.dev.yaml` structure:
    ```yaml
    config:
      gcp:project: cherry-ai-project
      gcp:region: us-central1
      cloudRunImage: us-central1-docker.pkg.dev/cherry-ai-project/orchestra/ai-orchestra:latest
      githubRepoOwner: scoobyjava
      githubRepoName: orchestra-main
      # cloudRunServiceAccountEmail: my-cloud-run-sa@cherry-ai-project.iam.gserviceaccount.com
      # secretIdToAccess: my-app-secret
    ```

## Deploying the Infrastructure

Once the prerequisites are met and the stack is configured:

1.  **Preview the Changes**:
    From the `infra` directory, run:
    ```bash
    pulumi preview
    ```
    This command shows you what resources will be created, updated, or deleted.

2.  **Deploy the Infrastructure**:
    If the preview looks correct, deploy the changes:
    ```bash
    pulumi up
    ```
    Pulumi will ask for confirmation before proceeding with the deployment.

## Accessing Outputs

After a successful deployment, Pulumi will display any exported outputs, such as the Cloud Run service URL or the Cloud Build trigger ID. You can also view stack outputs at any time with:

```bash
pulumi stack output
```

## Managing Secrets for the Application

This Pulumi program can grant a Cloud Run service account access to secrets stored in Google Cloud Secret Manager. The application code running within Cloud Run should be configured to read these secrets from environment variables that are populated from Secret Manager.

To set this up:
1.  Ensure the secrets exist in Secret Manager in your GCP project.
2.  In `infra/__main__.py`, uncomment and configure the `envs` section within the `gcp.cloudrunv2.Service` resource definition to map secrets to environment variables for your container. For example:
    ```python
    # ... inside gcp.cloudrunv2.Service template.containers block
    "envs": [
        {
            "name": "API_KEY", # Environment variable name in your container
            "value_source": {
                "secret_key_ref": {
                    "secret": "name-of-secret-in-secret-manager",
                    "version": "latest" # or a specific version number
                }
            }
        }
    ],
    ```
3.  Ensure the `cloudRunServiceAccountEmail` and `secretIdToAccess` are correctly set in `Pulumi.dev.yaml` if you want Pulumi to manage the IAM binding for secret access. If you manage IAM permissions separately, ensure the Cloud Run service's runtime service account has the `roles/secretmanager.secretAccessor` role on the required secrets.

## Cleaning Up

To remove all resources provisioned by this Pulumi stack:

1.  From the `infra` directory, run:
    ```bash
    pulumi destroy
    ```
    Confirm the action when prompted.

2.  To remove the stack itself (optional, if you no longer need it):
    ```bash
    pulumi stack rm dev
    ```

## Mono-repo Conventions

This setup places the infrastructure code (`infra/`) alongside the application code in the same repository, following common mono-repo practices. The Cloud Build trigger is configured to act on pushes to the main branch, facilitating CI/CD for both application and infrastructure if desired (e.g., by having `cloudbuild.yaml` in the root handle both).

# MCP Server Terraform Module

This module deploys the MCP (Model Context Protocol) server to Google Cloud Run with appropriate configuration and security settings.

## Features

- Deploys MCP server as a Cloud Run service
- Configures Secret Manager for API keys
- Sets up IAM permissions
- Configures Firestore for data persistence (optional)
- Supports environment-specific configuration

## Usage

```hcl
module "mcp_server" {
  source = "./modules/mcp_server"

  project_id            = var.project_id
  region                = var.region
  env                   = var.env
  image                 = "gcr.io/${var.project_id}/mcp-server:latest"
  service_account_email = google_service_account.mcp_server_sa.email
  
  # Optional configurations
  memory_limit          = "1Gi"
  cpu_limit             = "1"
  min_instances         = 1
  max_instances         = 5
  gemini_api_key_secret_id = "mcp-gemini-api-key"
}
```

## Prerequisites

Before using this module, you should:

1. Build and push the MCP server Docker image to Google Container Registry
2. Create a service account for the MCP server
3. Store API keys in Secret Manager

## Example Workflow

### 1. Create Service Account

```hcl
resource "google_service_account" "mcp_server_sa" {
  account_id   = "mcp-server-sa"
  display_name = "MCP Server Service Account"
}

# Grant necessary permissions
resource "google_project_iam_member" "mcp_server_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.mcp_server_sa.email}"
}
```

### 2. Build and Push Docker Image

Use Cloud Build to build and push the Docker image:

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/${PROJECT_ID}/mcp-server:latest', '-f', 'mcp_server/scripts/Dockerfile', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/${PROJECT_ID}/mcp-server:latest']
```

### 3. Deploy MCP Server

```hcl
module "mcp_server" {
  source = "./modules/mcp_server"

  project_id            = "cherry-ai-project"
  region                = "us-central1"
  env                   = "dev"
  service_account_email = google_service_account.mcp_server_sa.email
}
```

## Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| project_id | The GCP project ID | string | - |
| region | The GCP region to deploy to | string | "us-central1" |
| env | Environment (dev, staging, prod) | string | "dev" |
| image | Docker image for the MCP server | string | "gcr.io/${var.project_id}/mcp-server:latest" |
| memory_limit | Memory limit for the Cloud Run service | string | "512Mi" |
| cpu_limit | CPU limit for the Cloud Run service | string | "1" |
| min_instances | Minimum number of instances | number | 0 |
| max_instances | Maximum number of instances | number | 10 |
| service_account_email | Service account email for the Cloud Run service | string | - |
| gemini_api_key_secret_id | Secret ID for the Gemini API key in Secret Manager | string | "mcp-gemini-api-key" |

## Outputs

| Name | Description |
|------|-------------|
| mcp_server_url | The URL of the deployed MCP server |
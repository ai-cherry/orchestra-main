# GCP Infrastructure Patterns for GitHub Copilot
# This file serves as a reference for common GCP patterns
# to improve GitHub Copilot suggestions in infrastructure code

# Variables for patterns
variable "env" {
  description = "Environment (staging or production)"
  type        = string
  default     = "staging"
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-west4"
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "example-org"
}

# Pattern: Secure Cloud Run service with VPC connector
resource "google_cloud_run_v2_service" "secure_api" {
  name     = "secure-api"
  location = var.region
  
  template {
    containers {
      image = "gcr.io/${var.project_id}/api:latest"
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      # Secret reference pattern
      env {
        name = "API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_key.secret_id
            version = "latest"
          }
        }
      }
    }
    
    # VPC connector pattern
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    
    # IAM service account binding pattern
    service_account = google_service_account.run_service_account.email
  }
}

# Pattern: GitHub repository with GCP service account integration
resource "github_repository" "api_repo" {
  name        = "api-service"
  description = "API Service with GCP integration"
  visibility  = "private"
  
  template {
    owner      = var.github_owner
    repository = "service-template"
  }
}

resource "github_actions_secret" "gcp_service_account" {
  repository      = github_repository.api_repo.name
  secret_name     = "GCP_SA_KEY"
  plaintext_value = google_service_account_key.github_key.private_key
}

# Pattern: GCP Workload Identity Federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Pattern: Full CI/CD pipeline with Cloud Build triggers
resource "google_cloudbuild_trigger" "github_pr_trigger" {
  name     = "pr-validation"
  filename = "cloudbuild-pr.yaml"
  
  github {
    owner = var.github_owner
    name  = github_repository.api_repo.name
    pull_request {
      branch = ".*"
      comment_control = "COMMENTS_ENABLED"
    }
  }
}

resource "google_cloudbuild_trigger" "deploy_trigger" {
  name     = "deploy-to-production"
  filename = "cloudbuild-deploy.yaml"
  
  github {
    owner = var.github_owner
    name  = github_repository.api_repo.name
    push {
      branch = "^main$"
    }
  }
}

# Pattern: Integrate GitHub Codespaces with GCP services
resource "github_codespaces_secret" "gcp_credentials" {
  repository      = github_repository.api_repo.name
  secret_name     = "GCP_CREDENTIALS"
  plaintext_value = google_service_account_key.codespaces_key.private_key
}

resource "github_repository_file" "devcontainer" {
  repository = github_repository.api_repo.name
  file       = ".devcontainer/devcontainer.json"
  content    = <<-EOT
  {
    "name": "GCP Development Environment",
    "features": {
      "ghcr.io/devcontainers/features/terraform:1": {},
      "ghcr.io/devcontainers/features/gcloud:1": {}
    },
    "containerEnv": {
      "GOOGLE_CLOUD_PROJECT": "${var.project_id}"
    },
    "postCreateCommand": "gcloud auth activate-service-account --key-file=/tmp/gcp-key.json"
  }
  EOT
}
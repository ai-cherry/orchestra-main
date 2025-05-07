# Terraform configuration for AI Orchestra project
# This file sets up the core GCP environment for the project

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
  default     = "525398941159"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "github_actions_sa" {
  description = "The email of the GitHub Actions service account"
  type        = string
  default     = "github-actions@cherry-ai-project.iam.gserviceaccount.com"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "workstations.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Service accounts
resource "google_service_account" "vertex_ai_sa" {
  account_id   = "vertex-ai-badass"
  display_name = "Vertex AI Badass Service Account"
  description  = "Service account with extensive permissions for all Vertex AI operations"
  project      = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_service_account" "gemini_sa" {
  account_id   = "gemini-badass"
  display_name = "Gemini Badass Service Account"
  description  = "Service account with extensive permissions for all Gemini API operations"
  project      = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "orchestra-api-sa"
  display_name = "Orchestra API Service Account"
  description  = "Service account for the Orchestra API Cloud Run service"
  project      = var.project_id

  depends_on = [google_project_service.required_apis]
}

# IAM permissions for Vertex AI service account
resource "google_project_iam_member" "vertex_ai_permissions" {
  for_each = toset([
    "roles/aiplatform.admin",
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/logging.admin",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountTokenCreator"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.vertex_ai_sa.email}"

  depends_on = [google_service_account.vertex_ai_sa]
}

# IAM permissions for Gemini service account
resource "google_project_iam_member" "gemini_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountTokenCreator"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gemini_sa.email}"

  depends_on = [google_service_account.gemini_sa]
}

# IAM permissions for Cloud Run service account
resource "google_project_iam_member" "cloud_run_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"

  depends_on = [google_service_account.cloud_run_sa]
}

# Storage buckets
resource "google_storage_bucket" "model_artifacts" {
  name     = "${var.project_id}-model-artifacts-${var.env}"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "data_sync" {
  name     = "${var.project_id}-data-sync-${var.env}"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "vertex_ai_key" {
  secret_id = "vertex-ai-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "gemini-key"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

# Workload Identity Federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
  project                   = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  project = var.project_id

  depends_on = [google_iam_workload_identity_pool.github_pool]
}

# Allow GitHub Actions to impersonate the service accounts
resource "google_service_account_iam_binding" "vertex_ai_workload_identity" {
  service_account_id = google_service_account.vertex_ai_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main"
  ]

  depends_on = [
    google_service_account.vertex_ai_sa,
    google_iam_workload_identity_pool.github_pool,
    google_iam_workload_identity_pool_provider.github_provider
  ]
}

resource "google_service_account_iam_binding" "gemini_workload_identity" {
  service_account_id = google_service_account.gemini_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main"
  ]

  depends_on = [
    google_service_account.gemini_sa,
    google_iam_workload_identity_pool.github_pool,
    google_iam_workload_identity_pool_provider.github_provider
  ]
}

# Cloud Run service
resource "google_cloud_run_v2_service" "orchestra_api" {
  name     = "orchestra-api-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra/api:latest"
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      env {
        name  = "REGION"
        value = var.region
      }
      
      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }
    }

    service_account = google_service_account.cloud_run_sa.email
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.required_apis,
    google_service_account.cloud_run_sa
  ]
}

# Allow unauthenticated access to the Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.orchestra_api.location
  project  = google_cloud_run_v2_service.orchestra_api.project
  service  = google_cloud_run_v2_service.orchestra_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_v2_service.orchestra_api]
}

# Outputs
output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.orchestra_api.uri
}

output "workload_identity_provider" {
  description = "The Workload Identity Provider for GitHub Actions"
  value       = "projects/${var.project_id}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
}

output "vertex_ai_service_account" {
  description = "The email of the Vertex AI service account"
  value       = google_service_account.vertex_ai_sa.email
}

output "gemini_service_account" {
  description = "The email of the Gemini service account"
  value       = google_service_account.gemini_sa.email
}
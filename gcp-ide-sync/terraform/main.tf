terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  backend "gcs" {
    bucket = "cherry-ai-project-terraform-state"
    prefix = "gcp-ide-sync"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "us-west4"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "workstations.googleapis.com",
    "iam.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "sync_service_repo" {
  provider = google-beta

  location      = var.region
  repository_id = "gcp-ide-sync"
  description   = "Docker repository for GCP IDE Sync service"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Service account for the sync service
resource "google_service_account" "sync_service_sa" {
  account_id   = "gcp-ide-sync-service"
  display_name = "GCP IDE Sync Service"
  description  = "Service account for GCP IDE Sync service"
}

# IAM permissions for the service account
resource "google_project_iam_member" "sync_service_permissions" {
  for_each = toset([
    "roles/workstations.user",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.sync_service_sa.email}"
}

# Secret for Google Client ID
resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "gcp-ide-sync-google-client-id"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Secret for JWT Secret
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "gcp-ide-sync-jwt-secret"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Secret access for service account
resource "google_secret_manager_secret_iam_member" "sync_service_secret_access" {
  for_each = {
    "google_client_id" = google_secret_manager_secret.google_client_id.id
    "jwt_secret"       = google_secret_manager_secret.jwt_secret.id
  }

  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sync_service_sa.email}"
}

# Cloud Run service for the sync service
resource "google_cloud_run_service" "sync_service" {
  name     = "gcp-ide-sync-service"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.sync_service_repo.repository_id}/sync-service:latest"
        
        env {
          name  = "PORT"
          value = "3000"
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCP_REGION"
          value = var.region
        }
        
        # Secret environment variables
        env {
          name = "GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_id.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "JWT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
      
      service_account_name = google_service_account.sync_service_sa.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.sync_service_repo
  ]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_policy" "sync_service_noauth" {
  location    = google_cloud_run_service.sync_service.location
  project     = google_cloud_run_service.sync_service.project
  service     = google_cloud_run_service.sync_service.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# IAM policy data for allowing unauthenticated access
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# Outputs
output "sync_service_url" {
  value = google_cloud_run_service.sync_service.status[0].url
}

output "artifact_registry_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.sync_service_repo.repository_id}"
}
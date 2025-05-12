terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.60.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.60.0"
    }
  }
  backend "gcs" {
    # Update this with your own backend bucket
    # bucket = "your-tf-state-bucket"
    # prefix = "terraform/state/gcp-migration"
  }
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Storage bucket for migration data
resource "google_storage_bucket" "migration_data" {
  name          = "${var.project_id}-migration-data-${var.environment}"
  location      = var.region
  force_destroy = var.environment != "prod"
  
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
  
  uniform_bucket_level_access = true
}

# Firestore database (in Native mode)
resource "google_firestore_database" "migration_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Secret for GitHub token
resource "google_secret_manager_secret" "github_token" {
  secret_id = "gcp-migration-github-token"
  
  replication {
    user_managed {
      replicas {
        location = "us-central1"
      }
    }
  }
}

# Secret version placeholder - actual values should be set using Secret Manager UI or gcloud
resource "google_secret_manager_secret_version" "github_token_version" {
  secret      = google_secret_manager_secret.github_token.id
  secret_data = "placeholder-replace-with-real-token"
  
  lifecycle {
    ignore_changes = [
      secret_data,
    ]
  }
}

# Service account for the migration toolkit
resource "google_service_account" "migration_service_account" {
  account_id   = "gcp-migration-sa"
  display_name = "GCP Migration Toolkit Service Account"
  description  = "Service account used by the GCP Migration Toolkit"
}

# IAM permissions for service account
resource "google_project_iam_member" "migration_iam_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.migration_service_account.email}"
}

resource "google_project_iam_member" "migration_iam_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.migration_service_account.email}"
}

resource "google_project_iam_member" "migration_iam_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.migration_service_account.email}"
}

# Cloud Run service
resource "google_cloud_run_service" "migration_api" {
  name     = "gcp-migration"
  location = var.region
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/gcp-migration:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        
        env {
          name  = "GCP_LOCATION"
          value = var.region
        }
        
        env {
          name = "GITHUB_TOKEN"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.github_token.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      service_account_name = google_service_account.migration_service_account.email
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_iam_member.migration_iam_storage_admin,
    google_project_iam_member.migration_iam_secret_accessor,
    google_project_iam_member.migration_iam_firestore_user,
  ]
}

# Allow unauthenticated access to the Cloud Run service
resource "google_cloud_run_service_iam_member" "migration_api_public" {
  location = google_cloud_run_service.migration_api.location
  service  = google_cloud_run_service.migration_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Workstation cluster configuration
resource "google_workstations_workstation_cluster" "default" {
  provider               = google-beta
  workstation_cluster_id = "default-cluster"
  location               = var.region
  
  network    = "default"
  subnetwork = "default"
  
  private_cluster_config {
    enable_private_endpoint = false
  }
}

resource "google_workstations_workstation_config" "default" {
  provider              = google-beta
  workstation_config_id = "default-config"
  workstation_cluster_id = google_workstations_workstation_cluster.default.workstation_cluster_id
  location              = var.region
  
  host {
    gce_instance {
      machine_type      = "e2-standard-4"
      boot_disk_size_gb = 50
      tags              = ["workstation"]
    }
  }
  
  # Removing persistent_directories due to compatibility issues with current provider version
  # For persistent storage, use GCS buckets with gsutil mount or increase boot disk size
  # Host configuration has boot_disk_size_gb already configured to 50GB
}

# Outputs
output "migration_api_url" {
  value = google_cloud_run_service.migration_api.status[0].url
}

output "storage_bucket" {
  value = google_storage_bucket.migration_data.name
}

output "workstation_cluster_id" {
  value = google_workstations_workstation_cluster.default.workstation_cluster_id
}

output "workstation_config_id" {
  value = google_workstations_workstation_config.default.workstation_config_id
}
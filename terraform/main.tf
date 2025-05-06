# AI Orchestra GCP Infrastructure
# This Terraform configuration sets up the core GCP infrastructure for AI Orchestra

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.80.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.80.0"
    }
  }

  backend "gcs" {
    bucket = "cherry-ai-project-terraform-state"
    prefix = "terraform/state"
  }
}

# Variables
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

variable "env" {
  description = "Environment (staging or production)"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["staging", "production"], var.env)
    error_message = "Environment must be either 'staging' or 'production'."
  }
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

# Local variables
locals {
  service_name = "ai-orchestra"
  service_account_name = "ai-orchestra-sa"
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
}

# Service Account for AI Orchestra
resource "google_service_account" "ai_orchestra" {
  account_id   = local.service_account_name
  display_name = "AI Orchestra Service Account"
  description  = "Service account for AI Orchestra application"
}

# Grant necessary roles to the service account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.ai_orchestra.email}"
}

resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.ai_orchestra.email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ai_orchestra.email}"
}

resource "google_project_iam_member" "storage_object_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.ai_orchestra.email}"
}

# Firestore database
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  lifecycle {
    prevent_destroy = true
  }
}

# Cloud Storage buckets
resource "google_storage_bucket" "assets" {
  name          = "${var.project_id}-assets-${var.env}"
  location      = var.region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
  
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
  
  labels = local.labels
}

resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-backups-${var.env}"
  location      = var.region
  storage_class = "NEARLINE"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.labels
}

# Secret Manager secrets
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = local.labels
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = local.labels
}

resource "google_secret_manager_secret" "portkey_api_key" {
  secret_id = "portkey-api-key"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = local.labels
}

# Note: Secret versions would typically be managed outside of Terraform
# or using sensitive variables with appropriate safeguards

# Vertex AI Vector Search index for semantic memory
resource "google_vertex_ai_index" "semantic_memory" {
  provider = google-beta
  
  display_name = "semantic-memory-${var.env}"
  description  = "Vector index for semantic memory in ${var.env} environment"
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.assets.name}/vector-index"
    config {
      dimensions = 768
      approximate_neighbors_count = 150
      distance_measure_type = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
  
  index_update_method = "BATCH_UPDATE"
  
  labels = local.labels
}

# Cloud Run service
resource "google_cloud_run_service" "ai_orchestra" {
  name     = "${local.service_name}-${var.env}"
  location = var.region
  
  template {
    spec {
      service_account_name = google_service_account.ai_orchestra.email
      
      containers {
        image = "gcr.io/${var.project_id}/${local.service_name}:latest"
        
        resources {
          limits = {
            cpu    = var.env == "production" ? "2" : "1"
            memory = var.env == "production" ? "4Gi" : "2Gi"
          }
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.env
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "REGION"
          value = var.region
        }
        
        # Secret environment variables
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openai_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "ANTHROPIC_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.anthropic_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "PORTKEY_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.portkey_api_key.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      # Container concurrency
      container_concurrency = var.env == "production" ? 100 : 80
      
      # Timeout
      timeout_seconds = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.env == "production" ? "2" : "1"
        "autoscaling.knative.dev/maxScale" = var.env == "production" ? "20" : "10"
      }
      
      labels = local.labels
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_iam_member.firestore_user,
    google_project_iam_member.secretmanager_accessor,
    google_project_iam_member.aiplatform_user,
    google_project_iam_member.storage_object_viewer
  ]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.ai_orchestra.location
  project     = google_cloud_run_service.ai_orchestra.project
  service     = google_cloud_run_service.ai_orchestra.name
  
  policy_data = data.google_iam_policy.noauth.policy_data
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# Pub/Sub topic for event-driven communication
resource "google_pubsub_topic" "ai_orchestra_events" {
  name = "ai-orchestra-events-${var.env}"
  
  labels = local.labels
  
  message_retention_duration = "86600s"  # 24 hours + 100 seconds
}

# Cloud Scheduler job for periodic tasks
resource "google_cloud_scheduler_job" "cleanup_job" {
  name             = "ai-orchestra-cleanup-${var.env}"
  description      = "Periodic cleanup job for AI Orchestra"
  schedule         = "0 */6 * * *"  # Every 6 hours
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"
  
  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.ai_orchestra.status[0].url}/api/maintenance/cleanup"
    
    oidc_token {
      service_account_email = google_service_account.ai_orchestra.email
    }
  }
}

# Outputs
output "cloud_run_url" {
  value       = google_cloud_run_service.ai_orchestra.status[0].url
  description = "The URL of the deployed Cloud Run service"
}

output "firestore_database" {
  value       = google_firestore_database.database.name
  description = "The name of the Firestore database"
}

output "assets_bucket" {
  value       = google_storage_bucket.assets.name
  description = "The name of the assets bucket"
}

output "backups_bucket" {
  value       = google_storage_bucket.backups.name
  description = "The name of the backups bucket"
}

output "pubsub_topic" {
  value       = google_pubsub_topic.ai_orchestra_events.name
  description = "The name of the Pub/Sub topic"
}
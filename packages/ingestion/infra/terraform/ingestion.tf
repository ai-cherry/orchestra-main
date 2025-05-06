# Terraform configuration for Orchestra File Ingestion System
#
# This file defines the infrastructure resources needed for the ingestion system,
# including Cloud Run services, Pub/Sub topics, and GCS buckets.

# Variables
variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# GCS buckets for raw files and processed text
resource "google_storage_bucket" "raw_files" {
  name     = "orchestra-ingestion-raw-${var.environment}"
  location = var.region
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 30  # Keep files for 30 days by default
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "processed_text" {
  name     = "orchestra-ingestion-processed-text-${var.environment}"
  location = var.region
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 30  # Keep processed text for 30 days by default
    }
    action {
      type = "Delete"
    }
  }
}

# Pub/Sub topics and subscriptions
resource "google_pubsub_topic" "ingestion_queue" {
  name = "file-ingestion-queue-${var.environment}"
}

resource "google_pubsub_subscription" "ingestion_subscription" {
  name  = "file-ingestion-subscription-${var.environment}"
  topic = google_pubsub_topic.ingestion_queue.name
  
  # Set acknowledgement deadline to 5 minutes for long-running tasks
  ack_deadline_seconds = 300
  
  # Enable message ordering if needed
  enable_message_ordering = false
  
  # Configure retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes max backoff
  }
  
  # Set expiration policy - messages expire after 7 days if not processed
  expiration_policy {
    ttl = "604800s"  # 7 days
  }
}

# Service Account for the ingestion worker
resource "google_service_account" "ingestion_worker_sa" {
  account_id   = "ingestion-worker-${var.environment}"
  display_name = "Orchestra Ingestion Worker Service Account"
  description  = "Service account for the file ingestion worker"
}

# IAM permissions for the ingestion worker
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.ingestion_worker_sa.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.ingestion_worker_sa.email}"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.ingestion_worker_sa.email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ingestion_worker_sa.email}"
}

# Cloud Run service for the ingestion worker
resource "google_cloud_run_service" "ingestion_worker" {
  name     = "ingestion-worker-${var.environment}"
  location = var.region
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/ingestion-worker:latest"
        
        resources {
          limits = {
            cpu    = "2.0"
            memory = "4Gi"
          }
        }
        
        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
      }
      
      # Service account
      service_account_name = google_service_account.ingestion_worker_sa.email
      
      # Increase timeout for long-running tasks
      timeout_seconds = 900  # 15 minutes
    }

    # Configure CPU allocation
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"         = "1"
        "autoscaling.knative.dev/maxScale"         = "10"
        "run.googleapis.com/cpu-throttling"        = "false"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Pub/Sub subscription with push endpoint to the worker
resource "google_pubsub_subscription" "ingestion_push_subscription" {
  name  = "file-ingestion-push-${var.environment}"
  topic = google_pubsub_topic.ingestion_queue.name
  
  push_config {
    push_endpoint = google_cloud_run_service.ingestion_worker.status[0].url
    
    attributes = {
      x-goog-version = "v1"
    }
    
    # Service account for authentication
    oidc_token {
      service_account_email = google_service_account.ingestion_worker_sa.email
    }
  }
  
  # Retain acked messages for debugging
  retain_acked_messages = true
  
  # Configure retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes max backoff
  }
  
  # Set acknowledgement deadline to 5 minutes for long-running tasks
  ack_deadline_seconds = 300
}

# Outputs
output "raw_files_bucket" {
  value = google_storage_bucket.raw_files.name
}

output "processed_text_bucket" {
  value = google_storage_bucket.processed_text.name
}

output "ingestion_topic" {
  value = google_pubsub_topic.ingestion_queue.name
}

output "worker_service_url" {
  value = google_cloud_run_service.ingestion_worker.status[0].url
}

output "worker_service_account" {
  value = google_service_account.ingestion_worker_sa.email
}

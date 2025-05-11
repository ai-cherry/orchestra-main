# Performance-optimized Cloud Run configuration for AI Orchestra
# This configuration prioritizes stability and performance over cost
# With improved security, parameterization, and resource management

# Core variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-west4"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Cloud Run resource configuration variables
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run service"
  type        = string
  default     = "2"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run service"
  type        = string
  default     = "2Gi"
}

variable "cloud_run_min_instances" {
  description = "Minimum instances for Cloud Run service"
  type        = number
  default     = 1
}

variable "cloud_run_max_instances" {
  description = "Maximum instances for Cloud Run service"
  type        = number
  default     = 20
}

variable "cloud_run_concurrency" {
  description = "Request concurrency for Cloud Run service"
  type        = number
  default     = 80
}

variable "cloud_run_timeout" {
  description = "Request timeout for Cloud Run service in seconds"
  type        = number
  default     = 300
}

# Monitoring variables
variable "latency_threshold_ms" {
  description = "Latency threshold for alerting in milliseconds"
  type        = number
  default     = 2000  # 2 seconds
}

variable "scheduler_interval" {
  description = "Interval for the keep-warm job in cron format"
  type        = string
  default     = "*/5 * * * *"  # Every 5 minutes
}

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  service            = each.key
  disable_on_destroy = false
}

# Create Artifact Registry repository for container images
resource "google_artifact_registry_repository" "ai_orchestra_repo" {
  provider      = google
  location      = var.region
  repository_id = "ai-orchestra-${var.env}"
  description   = "Docker repository for AI Orchestra ${var.env} environment"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Create a service account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  account_id   = "ai-orchestra-${var.env}-sa"
  display_name = "AI Orchestra ${var.env} Service Account"
  description  = "Service account for AI Orchestra Cloud Run service"
}

# Grant necessary logging and monitoring permissions to the service account
resource "google_project_iam_member" "cloud_run_basic_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Create Secret Manager secret for service account key
resource "google_secret_manager_secret" "secret_management_key" {
  secret_id = "secret-management-key-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Create initial secret version with placeholder data
resource "google_secret_manager_secret_version" "initial_version" {
  secret      = google_secret_manager_secret.secret_management_key.id
  secret_data = "placeholder-to-be-updated-by-deployment-script"
}

# Grant secret access to the service account (scoped to specific secret)
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.secret_management_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant Firestore access to the service account
resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/firestore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant Vertex AI access to the service account
resource "google_project_iam_member" "vertex_ai_access" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Create Cloud Run service with performance optimizations
resource "google_cloud_run_service" "ai_orchestra" {
  name     = "ai-orchestra-${var.env}"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.cloud_run_service_account.email
      
      containers {
        image = "gcr.io/${var.project_id}/ai-orchestra:latest"
        
        resources {
          limits = {
            cpu    = var.cloud_run_cpu
            memory = var.cloud_run_memory
          }
        }
        
        # Environment variables
        env {
          name  = "ENV"
          value = var.env
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
          name = "SECRET_MANAGER_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.secret_management_key.secret_id
              key  = "latest"
            }
          }
        }
        
        # Performance optimizations
        env {
          name  = "PYTHONOPTIMIZE"
          value = "2"
        }
        
        env {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }
        
        # Startup probe for stability
        startup_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 5
          failure_threshold     = 3
        }
        
        # Liveness probe for stability
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 30
          timeout_seconds       = 5
          period_seconds        = 30
          failure_threshold     = 3
        }
      }
      
      # Concurrency settings for performance
      container_concurrency = var.cloud_run_concurrency
      timeout_seconds       = var.cloud_run_timeout
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = tostring(var.cloud_run_min_instances)
        "autoscaling.knative.dev/maxScale"        = tostring(var.cloud_run_max_instances)
        "run.googleapis.com/cpu-throttling"       = "false"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost"    = "true"
        "run.googleapis.com/vpc-access-egress"    = "all-traffic"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.ai_orchestra_repo,
    google_secret_manager_secret.secret_management_key,
    google_secret_manager_secret_version.initial_version
  ]
}

# IAM policy to make the service publicly accessible
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# Apply the IAM policy to the service
resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.ai_orchestra.location
  project     = google_cloud_run_service.ai_orchestra.project
  service     = google_cloud_run_service.ai_orchestra.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# Create Cloud Monitoring alert policy for performance monitoring
resource "google_monitoring_alert_policy" "high_latency_alert" {
  display_name = "AI Orchestra ${var.env} High Latency Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High latency"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.latency_threshold_ms
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }

  notification_channels = []  # Add notification channels as needed
  
  depends_on = [google_project_service.required_apis]
}

# Create Cloud Scheduler job to keep the service warm
resource "google_cloud_scheduler_job" "keep_warm_job" {
  name        = "ai-orchestra-${var.env}-keep-warm"
  description = "Keep AI Orchestra service warm to prevent cold starts"
  schedule    = var.scheduler_interval
  
  http_target {
    uri         = google_cloud_run_service.ai_orchestra.status[0].url
    http_method = "GET"
    
    headers = {
      "User-Agent" = "Google-Cloud-Scheduler"
    }
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_service.ai_orchestra
  ]
}

# Output the service URL
output "service_url" {
  value       = google_cloud_run_service.ai_orchestra.status[0].url
  description = "The URL of the deployed Cloud Run service"
}

# Output the service account email
output "service_account_email" {
  value       = google_service_account.cloud_run_service_account.email
  description = "The email of the service account used by the Cloud Run service"
}

# Output the secret ID
output "secret_id" {
  value       = google_secret_manager_secret.secret_management_key.id
  description = "The ID of the Secret Manager secret for authentication"
}
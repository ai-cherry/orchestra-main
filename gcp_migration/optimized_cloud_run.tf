# Performance-optimized Cloud Run configuration for AI Orchestra
# This configuration prioritizes performance, fast response times, and eliminates cold starts

# Variable declarations
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Local values for configuration
locals {
  service_name = "ai-orchestra-api"
  
  # Performance-optimized settings
  cpu_limit          = 4     # 4 CPU cores (higher than default)
  memory_limit       = 2048  # 2GB memory (higher than default)
  concurrency        = 80    # Higher concurrency (default is 30)
  min_instances      = 1     # Warm instances to eliminate cold starts
  timeout_seconds    = 300   # 5 minutes for longer operations
  
  # Common labels
  common_labels = {
    app         = "ai-orchestra"
    environment = var.env
    managed-by  = "terraform"
  }
}

# Cloud Run service with performance optimizations
resource "google_cloud_run_service" "api" {
  name     = local.service_name
  location = var.region
  project  = var.project_id

  template {
    spec {
      # Performance configuration
      container_concurrency = local.concurrency
      timeout_seconds       = local.timeout_seconds
      
      containers {
        image = "gcr.io/${var.project_id}/${local.service_name}:latest"
        
        # Resource limits - higher CPU and memory for better performance
        resources {
          limits = {
            cpu    = "${local.cpu_limit}"
            memory = "${local.memory_limit}Mi"
          }
        }
        
        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = var.env
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        # Vector search optimization variables
        env {
          name  = "VECTOR_LISTS"
          value = "4000" # Optimized IVF lists count
        }
        
        env {
          name  = "BATCH_SIZE"
          value = "500" # Larger batch size for efficiency
        }
        
        env {
          name  = "DEBOUNCE_INTERVAL"
          value = "0.1" # Aggressive synchronization
        }
        
        # Secret references
        # Using secret manager for sensitive data
        env {
          name = "DB_CONNECTION_STRING"
          value_from {
            secret_key_ref {
              name = "db-connection-string"
              key  = "latest"
            }
          }
        }
        
        # Port configuration
        ports {
          container_port = 8080
        }
      }
    }
    
    metadata {
      annotations = {
        # Important performance annotations
        "autoscaling.knative.dev/minScale"        = local.min_instances
        "autoscaling.knative.dev/maxScale"        = "10"
        "run.googleapis.com/cpu-throttling"       = "false"
        "run.googleapis.com/startup-cpu-boost"    = "true"
        "run.googleapis.com/cloudsql-instances"   = "REPLACE_WITH_CLOUDSQL_CONNECTION_NAME"
        "run.googleapis.com/vpc-access-connector" = "REPLACE_WITH_VPC_CONNECTOR"
      }
      
      labels = local.common_labels
    }
  }

  # Progressive traffic rollout for stability
  traffic {
    percent         = 100
    latest_revision = true
  }

  # Avoid downtime during updates
  autogenerate_revision_name = true

  lifecycle {
    prevent_destroy = true
  }
}

# IAM binding for Cloud Run service
resource "google_cloud_run_service_iam_binding" "public_access" {
  location = google_cloud_run_service.api.location
  project  = google_cloud_run_service.api.project
  service  = google_cloud_run_service.api.name
  role     = "roles/run.invoker"
  members  = [
    "allUsers", # Public access - restrict as needed
  ]
}

# Cloud Run CPU utilization alert policy
resource "google_monitoring_alert_policy" "cpu_utilization" {
  display_name = "CPU Utilization - ${local.service_name}"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "CPU Utilization high"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${local.service_name}\" AND metric.type = \"run.googleapis.com/container/cpu/utilization\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8 # Alert when CPU utilization exceeds 80%
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_99"
      }
    }
  }

  notification_channels = [] # Add notification channels as needed
  
  documentation {
    content   = "CPU Utilization for ${local.service_name} is exceeding threshold."
    mime_type = "text/markdown"
  }
}

# Outputs
output "service_url" {
  value = google_cloud_run_service.api.status[0].url
  description = "The URL of the deployed Cloud Run service"
}

output "service_name" {
  value = google_cloud_run_service.api.name
  description = "The name of the Cloud Run service"
}

output "service_region" {
  value = google_cloud_run_service.api.location
  description = "The region of the Cloud Run service"
}
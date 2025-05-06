/**
 * # Cloud Run Module
 *
 * This module sets up a Cloud Run service with secure credential management
 * and proper configuration for the AI Orchestra project.
 */

# Variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
}

variable "image" {
  description = "The container image to deploy"
  type        = string
}

variable "service_account_email" {
  description = "The email of the service account to run the service as"
  type        = string
}

variable "redis_host_secret" {
  description = "The name of the Secret Manager secret containing the Redis host"
  type        = string
}

variable "redis_password_secret" {
  description = "The name of the Secret Manager secret containing the Redis password"
  type        = string
}

variable "vertex_api_key_secret" {
  description = "The name of the Secret Manager secret containing the Vertex API key"
  type        = string
}

variable "min_instances" {
  description = "The minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "The maximum number of instances"
  type        = number
  default     = 10
}

variable "cpu" {
  description = "The CPU allocation"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "The memory allocation"
  type        = string
  default     = "512Mi"
}

variable "concurrency" {
  description = "The maximum number of concurrent requests per instance"
  type        = number
  default     = 80
}

variable "timeout_seconds" {
  description = "The request timeout in seconds"
  type        = number
  default     = 300
}

variable "vpc_connector_id" {
  description = "The ID of the VPC connector"
  type        = string
  default     = null
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated access"
  type        = bool
  default     = false
}

variable "environment_variables" {
  description = "Environment variables to set"
  type        = map(string)
  default     = {}
}

# Local variables
locals {
  service_name_with_env = "${var.service_name}${var.env == "prod" ? "" : "-${var.env}"}"
  
  default_environment_variables = {
    ENVIRONMENT = var.env == "prod" ? "production" : var.env == "staging" ? "staging" : "development"
    LOG_LEVEL   = var.env == "prod" ? "INFO" : "DEBUG"
    STANDARD_MODE = "true"
    USE_RECOVERY_MODE = "false"
  }
  
  environment_variables = merge(local.default_environment_variables, var.environment_variables)
}

# Cloud Run service
resource "google_cloud_run_service" "service" {
  name     = local.service_name_with_env
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = var.service_account_email
      
      containers {
        image = var.image
        
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
        
        # Environment variables
        dynamic "env" {
          for_each = local.environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }
        
        # Secret environment variables
        env {
          name = "REDIS_HOST"
          value_from {
            secret_key_ref {
              name = var.redis_host_secret
              key  = "latest"
            }
          }
        }
        
        env {
          name = "REDIS_PASSWORD"
          value_from {
            secret_key_ref {
              name = var.redis_password_secret
              key  = "latest"
            }
          }
        }
        
        env {
          name = "VERTEX_API_KEY"
          value_from {
            secret_key_ref {
              name = var.vertex_api_key_secret
              key  = "latest"
            }
          }
        }
      }
      
      # Container concurrency
      container_concurrency = var.concurrency
      
      # Timeout
      timeout_seconds = var.timeout_seconds
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
        # VPC connector if provided
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector_id != null ? var.vpc_connector_id : null
        # Use direct VPC egress
        "run.googleapis.com/vpc-access-egress" = var.vpc_connector_id != null ? "all-traffic" : null
      }
    }
  }

  # Traffic configuration
  traffic {
    percent         = 100
    latest_revision = true
  }

  # Ignore changes to the image as it will be updated by CI/CD
  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "public" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_service.service.location
  project  = google_cloud_run_service.service.project
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "The URL of the deployed service"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_name" {
  description = "The name of the deployed service"
  value       = google_cloud_run_service.service.name
}

output "service_id" {
  description = "The ID of the deployed service"
  value       = google_cloud_run_service.service.id
}
/**
 * Terraform configuration for deploying the AI Orchestra Admin API to Cloud Run.
 * This configuration provides a secure, scalable deployment with proper
 * IAM permissions and secret management.
 */

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    # Use the following variables when applying:
    # bucket = "${var.project_id}-terraform-state"
    # prefix = "admin-api"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  service_name = "admin-api"
  image_name   = "${var.region}-docker.pkg.dev/${var.project_id}/services/${local.service_name}:${var.image_tag}"
}

# Cloud Run service for admin API - Performance optimized
resource "google_cloud_run_v2_service" "admin_api" {
  name     = "${local.service_name}-${var.env}"
  location = var.region

  template {
    containers {
      image = local.image_name

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = false # Keep CPU active for faster response times
      }

      # Environment variables
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "REGION"
        value = var.region
      }

      env {
        name  = "ENV"
        value = var.env
      }

      # Performance optimization environment variables
      env {
        name  = "WORKERS_PER_CORE"
        value = "2"
      }

      env {
        name  = "MAX_KEEPALIVE"
        value = "120"
      }
      
      env {
        name  = "LOG_LEVEL"
        value = "warning"  # Reduce logging overhead
      }

      # Database URL - use direct environment variable for better performance
      env {
        name = "DATABASE_URL"
        value = "firestore://${var.project_id}"
      }

      # Redis URL direct configuration if enabled
      dynamic "env" {
        for_each = var.redis_enabled ? [1] : []
        content {
          name  = "REDIS_URL"
          value = "redis://localhost:6379/0"  # Use direct value for faster startup
        }
      }

      # Container ports
      ports {
        container_port = 8080
      }

      # Optimized startup probe - faster startup detection
      startup_probe {
        http_get {
          path = "/"
        }
        initial_delay_seconds = 5  # Reduced from 10
        timeout_seconds       = 2  # Reduced from 3
        period_seconds        = 3  # Reduced from 5
        failure_threshold     = 5  # Increased from 3 for more attempts
      }

      # Optimized liveness probe - less frequent checks
      liveness_probe {
        http_get {
          path = "/"
        }
        initial_delay_seconds = 10  # Reduced from 15
        timeout_seconds       = 2   # Reduced from 3
        period_seconds        = 60  # Increased from 30 to reduce overhead
      }
    }

    # Optimized scaling settings
    scaling {
      min_instance_count = max(1, var.min_instances)  # Ensure at least 1 instance is always running
      max_instance_count = var.max_instances
    }

    # Service account to run as
    service_account = google_service_account.admin_api_sa.email

    # VPC Connector (if needed)
    dynamic "vpc_access" {
      for_each = var.vpc_connector != "" ? [1] : []
      content {
        connector = var.vpc_connector
        egress    = "ALL_TRAFFIC"  # Allow all traffic for better connectivity
      }
    }
  }

  # Traffic settings (for blue/green deployment)
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_iam_member.editor_role
  ]
}

# Create service account for the Admin API
resource "google_service_account" "admin_api_sa" {
  account_id   = "admin-api-${var.env}"
  display_name = "Service Account for Admin API (${var.env})"
  description  = "Used by the Admin API Cloud Run service with performance-first configuration"
}

# Grant service account Editor role for simplified permissions and better performance
resource "google_project_iam_member" "editor_role" {
  project = var.project_id
  role    = "roles/editor"  # Broader role for simplified access management
  member  = "serviceAccount:${google_service_account.admin_api_sa.email}"
}

# Database URL secret
resource "google_secret_manager_secret" "database_url" {
  secret_id = "admin-api-database-url-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Grant service account access to database URL secret
resource "google_secret_manager_secret_iam_member" "database_url_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.admin_api_sa.email}"
}

# Redis URL secret (if Redis is enabled)
resource "google_secret_manager_secret" "redis_url" {
  count     = var.redis_enabled ? 1 : 0
  secret_id = "admin-api-redis-url-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Grant service account access to Redis URL secret
resource "google_secret_manager_secret_iam_member" "redis_url_access" {
  count     = var.redis_enabled ? 1 : 0
  project   = var.project_id
  secret_id = google_secret_manager_secret.redis_url[0].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.admin_api_sa.email}"
}

# Cloud Run public access (unauthenticated)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.public_access ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.admin_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.admin_api.uri
}

output "service_status" {
  description = "The status of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.admin_api.status
}
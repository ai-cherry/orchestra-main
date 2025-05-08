# Terraform module for deploying MCP Server to Cloud Run

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy to"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "image" {
  description = "Docker image for the MCP server"
  type        = string
  default     = "gcr.io/${var.project_id}/mcp-server:latest"
}

variable "memory_limit" {
  description = "Memory limit for the Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "cpu_limit" {
  description = "CPU limit for the Cloud Run service"
  type        = string
  default     = "1"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "gemini_api_key_secret_id" {
  description = "Secret ID for the Gemini API key in Secret Manager"
  type        = string
  default     = "mcp-gemini-api-key"
}

# Cloud Run service for MCP Server
resource "google_cloud_run_v2_service" "mcp_server" {
  name     = "mcp-server-${var.env}"
  location = var.region
  
  template {
    containers {
      image = var.image
      
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }
      
      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      
      env {
        name  = "LOG_LEVEL"
        value = upper(var.env) == "PROD" ? "INFO" : "DEBUG"
      }
      
      # Use Secret Manager for API keys
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.gemini_api_key_secret_id
            version = "latest"
          }
        }
      }
      
      # Volume mount for persistent data
      volume_mounts {
        name       = "mcp-data"
        mount_path = "/app/data"
      }
    }
    
    volumes {
      name = "mcp-data"
      cloud_sql_instance {
        instances = []
      }
    }
    
    service_account = var.service_account_email
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.mcp_server.location
  service  = google_cloud_run_v2_service.mcp_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"  # Public access - restrict as needed
}

# Firestore database for MCP server data (if needed)
resource "google_firestore_database" "mcp_database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Secret Manager secret for Gemini API key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = var.gemini_api_key_secret_id
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# IAM binding for Secret Manager access
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

output "mcp_server_url" {
  value = google_cloud_run_v2_service.mcp_server.uri
}
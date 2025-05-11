oterraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  backend "gcs" {
    bucket = "cherry-ai-project-terraform-state" # Replace with your GCS bucket name
    prefix = "admin-interface"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "api_url" {
  description = "URL of the backend API"
  type        = string
}

# Cloud Run service for the frontend admin interface
resource "google_cloud_run_v2_service" "admin_frontend" {
  name     = "ai-orchestra-admin-frontend-${var.env}"
  location = var.region

  template {
    timeout = "300s" # Default timeout
    containers {
      image = "gcr.io/${var.project_id}/ai-orchestra-admin-frontend:latest"
      ports {
        container_port = 80
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Cloud Run service for the backend admin API
resource "google_cloud_run_v2_service" "admin_backend" {
  name     = "ai-orchestra-admin-backend-${var.env}"
  location = var.region

  template {
    # Enable session affinity for WebSockets
    session_affinity = true
    # Set timeout for requests
    timeout = "300s"
    
    containers {
      image = "gcr.io/${var.project_id}/ai-orchestra-admin-backend:latest"
      ports {
        container_port = 8080 # FastAPI default port
      }
      env {
        name = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "REGION"
        value = var.region
      }
      env {
        name = "API_URL"
        value = var.api_url
      }
      # TODO: Add other environment variables or secret mounts as needed
    }
    
    scaling {
      min_instance_count = 0
      max_instance_count = 10 # Adjust based on expected load
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM policy to make the frontend service public (adjust as needed for authentication)
resource "google_cloud_run_v2_service_iam_member" "admin_frontend_public" {
  location = google_cloud_run_v2_service.admin_frontend.location
  project  = google_cloud_run_v2_service.admin_frontend.project
  name     = google_cloud_run_v2_service.admin_frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers" # Make public for now, secure later with authentication
}

# Outputs
output "admin_frontend_url" {
  description = "The URL of the admin frontend service"
  value       = google_cloud_run_v2_service.admin_frontend.uri
}

output "admin_backend_url" {
  description = "The URL of the admin backend service"
  value       = google_cloud_run_v2_service.admin_backend.uri
}
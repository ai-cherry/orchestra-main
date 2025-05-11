# Optimized Cloud Run configuration for AI Orchestra
# Features:
# - Resource optimization
# - Autoscaling configuration
# - CPU throttling
# - Secret management integration
# - Health check configuration

# Cloud Run service for AI Orchestra API
resource "google_cloud_run_service" "ai_orchestra_api" {
  name     = "ai-orchestra-api-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/ai-orchestra-api:latest"
        
        # Resource limits - optimized for cost and performance
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
          # Request less than limits to allow for efficient resource allocation
          requests = {
            cpu    = "500m"
            memory = "256Mi"
          }
        }

        # Environment variables
        env {
          name  = "ENV"
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
        dynamic "env" {
          for_each = var.secrets
          content {
            name = env.key
            value_from {
              secret_key_ref {
                name = env.value.secret_name
                key  = env.value.secret_key
              }
            }
          }
        }
        
        # Port configuration
        ports {
          container_port = 8000
          name           = "http1"
        }
        
        # Startup probe - wait for service to be ready
        startup_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 5
          period_seconds        = 3
          timeout_seconds       = 3
          failure_threshold     = 5
          success_threshold     = 1
        }
        
        # Liveness probe - check if service is alive
        liveness_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          period_seconds    = 30
          timeout_seconds   = 5
          failure_threshold = 3
          success_threshold = 1
        }
      }
      
      # Service account
      service_account_name = google_service_account.ai_orchestra_sa.email
      
      # Container concurrency - number of requests per container instance
      container_concurrency = 80
      
      # Request timeout
      timeout_seconds = 300
    }
    
    metadata {
      annotations = {
        # Autoscaling configuration
        "autoscaling.knative.dev/minScale"      = var.env == "prod" ? "1" : "0"
        "autoscaling.knative.dev/maxScale"      = var.env == "prod" ? "20" : "10"
        
        # CPU throttling - scale down CPU when idle to reduce costs
        "run.googleapis.com/cpu-throttling"     = "true"
        
        # VPC connector - if using VPC
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector_name != "" ? var.vpc_connector_name : null
        
        # Cloud SQL instances - if using Cloud SQL
        "run.googleapis.com/cloudsql-instances"   = var.cloudsql_instance != "" ? var.cloudsql_instance : null
        
        # Client-side throttling - for better performance
        "run.googleapis.com/client-name"          = "ai-orchestra"
        "run.googleapis.com/client-protocol"      = "http1"
        
        # Execution environment
        "run.googleapis.com/execution-environment" = "gen2"
      }
      
      # Labels for better organization and filtering
      labels = {
        "app"         = "ai-orchestra"
        "environment" = var.env
        "managed-by"  = "terraform"
      }
    }
  }

  # Traffic configuration - 100% to latest revision
  traffic {
    percent         = 100
    latest_revision = true
  }

  # Auto-generate revision name
  autogenerate_revision_name = true

  # Depends on service account
  depends_on = [
    google_service_account.ai_orchestra_sa,
    google_secret_manager_secret_iam_member.secret_access
  ]
}

# Service account for Cloud Run
resource "google_service_account" "ai_orchestra_sa" {
  account_id   = "ai-orchestra-sa-${var.env}"
  display_name = "AI Orchestra Service Account (${var.env})"
  project      = var.project_id
}

# IAM binding for service account
resource "google_project_iam_member" "ai_orchestra_sa_roles" {
  for_each = toset([
    "roles/firestore.user",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.ai_orchestra_sa.email}"
}

# IAM binding for secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = each.value.secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ai_orchestra_sa.email}"
}

# IAM policy for Cloud Run service
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# IAM policy binding for Cloud Run service
resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.ai_orchestra_api.location
  project     = google_cloud_run_service.ai_orchestra_api.project
  service     = google_cloud_run_service.ai_orchestra_api.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# Output the service URL
output "ai_orchestra_api_url" {
  value = google_cloud_run_service.ai_orchestra_api.status[0].url
}

# Variables
variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-west4"
}

variable "secrets" {
  description = "Map of environment variable names to secret references"
  type = map(object({
    secret_name = string
    secret_key  = string
  }))
  default = {}
  
  # Example:
  # secrets = {
  #   "API_KEY" = {
  #     secret_name = "api-key"
  #     secret_key  = "latest"
  #   }
  # }
}

variable "vpc_connector_name" {
  description = "Name of the VPC connector to use"
  type        = string
  default     = ""
}

variable "cloudsql_instance" {
  description = "Cloud SQL instance connection name"
  type        = string
  default     = ""
}
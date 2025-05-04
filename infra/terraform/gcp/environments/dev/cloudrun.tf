/**
 * Cloud Run configuration for dev environment
 * Creates orchestrator-api-dev service
 */

# Cloud Run service for the Orchestra API
resource "google_cloud_run_service" "orchestrator_api_dev" {
  name     = "orchestrator-api-dev"
  location = var.region
  
  template {
    spec {
      # Reference the orchestra-runner-sa service account
      service_account_name = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
      
      containers {
        image = "us-docker.pkg.dev/${var.project_id}/orchestra-images/api:latest"
        
        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = "dev"
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        # Secret environment variables
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = "openai-api-key-dev"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "ANTHROPIC_API_KEY"
          value_from {
            secret_key_ref {
              name = "anthropic-api-key-dev"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "GEMINI_API_KEY"
          value_from {
            secret_key_ref {
              name = "gemini-api-key-dev"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "REDIS_AUTH"
          value_from {
            secret_key_ref {
              name = "redis-auth-dev"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "DATABASE_PASSWORD"
          value_from {
            secret_key_ref {
              name = "database-password-dev"
              key  = "latest"
            }
          }
        }
        
        # Resource limits
        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
        
        # Health check
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          period_seconds        = 30
        }
      }
      
      # Container concurrency
      container_concurrency = 80
      
      # Timeout
      timeout_seconds = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# Allow unauthenticated access to the dev service
resource "google_cloud_run_service_iam_member" "orchestrator_api_dev_public" {
  service  = google_cloud_run_service.orchestrator_api_dev.name
  location = google_cloud_run_service.orchestrator_api_dev.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output the service URL
output "orchestrator_api_dev_url" {
  value       = google_cloud_run_service.orchestrator_api_dev.status[0].url
  description = "URL of the orchestrator-api-dev service"
}

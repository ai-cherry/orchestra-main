/**
 * Cloud Run configuration for production environment
 * Creates orchestrator-api-prod service
 */

# Cloud Run service for the Orchestra API
resource "google_cloud_run_service" "orchestrator_api_prod" {
  name     = "orchestrator-api-prod"
  location = var.region
  
  template {
    spec {
      # Reference the orchestra-runner-sa service account
      service_account_name = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
      
      containers {
        image = "us-docker.pkg.dev/${var.project_id}/orchestra-images/api:stable"
        
        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = "prod"
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
              name = "openai-api-key-prod"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "ANTHROPIC_API_KEY"
          value_from {
            secret_key_ref {
              name = "anthropic-api-key-prod"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "GEMINI_API_KEY"
          value_from {
            secret_key_ref {
              name = "gemini-api-key-prod"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "REDIS_AUTH"
          value_from {
            secret_key_ref {
              name = "redis-auth-prod"
              key  = "latest"
            }
          }
        }
        
        env {
          name = "DATABASE_PASSWORD"
          value_from {
            secret_key_ref {
              name = "database-password-prod"
              key  = "latest"
            }
          }
        }
        
        # Production has higher resource limits
        resources {
          limits = {
            cpu    = "2000m"
            memory = "4Gi"
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
        
        # Readiness probe is configured via annotations below
      }
      
      # Lower container concurrency for production (more CPU per request)
      container_concurrency = 50
      
      # Longer timeout for production workloads
      timeout_seconds = 600
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "2"  # Always have at least 2 instances running
        "autoscaling.knative.dev/maxScale" = "20" # Scale up to 20 instances
        "run.googleapis.com/readiness-probe-path" = "/health"
        "run.googleapis.com/readiness-probe-period-seconds" = "10"
        "run.googleapis.com/readiness-probe-initial-delay-seconds" = "5"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# Allow authenticated access only to the production service
resource "google_cloud_run_service_iam_binding" "orchestrator_api_prod_access" {
  service  = google_cloud_run_service.orchestrator_api_prod.name
  location = google_cloud_run_service.orchestrator_api_prod.location
  role     = "roles/run.invoker"
  members  = [
    "serviceAccount:${data.google_service_account.orchestra_runner_sa.email}",
    "serviceAccount:${data.google_service_account.github_deployer.email}"
  ]
}

# Reference the GitHub deployer service account
data "google_service_account" "github_deployer" {
  account_id = "github-actions-deployer"
}

# Output the service URL
output "orchestrator_api_prod_url" {
  value       = google_cloud_run_service.orchestrator_api_prod.status[0].url
  description = "URL of the orchestrator-api-prod service"
}

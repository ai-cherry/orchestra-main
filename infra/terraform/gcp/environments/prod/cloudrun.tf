/**
 * Cloud Run configuration for production environment
 * Creates orchestrator-api-prod and phidata-agent-ui-prod services
 */

# Cloud Run service for the Orchestra API
resource "google_cloud_run_v2_service" "orchestrator_api_prod" {
  name     = "orchestrator-api-prod"
  location = var.region
  
  template {
    service_account = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
    
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra-images/api:latest"
      
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
            secret = "openai-api-key-prod"
            version = "latest"
          }
        }
      }
      
      env {
        name = "ANTHROPIC_API_KEY"
        value_from {
          secret_key_ref {
            secret = "anthropic-api-key-prod"
            version = "latest"
          }
        }
      }
      
      env {
        name = "GEMINI_API_KEY"
        value_from {
          secret_key_ref {
            secret = "gemini-api-key-prod"
            version = "latest"
          }
        }
      }
      
      env {
        name = "REDIS_AUTH"
        value_from {
          secret_key_ref {
            secret = "redis-auth-prod"
            version = "latest"
          }
        }
      }
      
      env {
        name = "DATABASE_PASSWORD"
        value_from {
          secret_key_ref {
            secret = "database-password-prod"
            version = "latest"
          }
        }
      }
      
      # Production resource limits
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
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 20
    }
    
    timeout = "600s"
  }
}

# Cloud Run service for the Phidata Agent UI
resource "google_cloud_run_v2_service" "phidata_agent_ui_prod" {
  name     = "phidata-agent-ui-prod"
  location = var.region
  
  template {
    service_account = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
    
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra-images/ui:main"
      
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
            secret = "openai-api-key-prod"
            version = "latest"
          }
        }
      }
      
      # Production resource limits
      resources {
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    
    timeout = "300s"
  }
}

# Allow unauthenticated access to the orchestrator API prod service
resource "google_cloud_run_service_iam_member" "orchestrator_api_prod_public" {
  project  = var.project_id
  location = var.region
  service  = google_cloud_run_v2_service.orchestrator_api_prod.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow unauthenticated access to the phidata agent UI prod service
resource "google_cloud_run_service_iam_member" "phidata_agent_ui_prod_public" {
  project  = var.project_id
  location = var.region
  service  = google_cloud_run_v2_service.phidata_agent_ui_prod.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output the service URLs
output "orchestrator_api_prod_url" {
  value       = google_cloud_run_v2_service.orchestrator_api_prod.uri
  description = "URL of the orchestrator-api-prod service"
}

output "phidata_agent_ui_prod_url" {
  value       = google_cloud_run_v2_service.phidata_agent_ui_prod.uri
  description = "URL of the phidata-agent-ui-prod service"
}

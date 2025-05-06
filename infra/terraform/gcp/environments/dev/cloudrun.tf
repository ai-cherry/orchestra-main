/**
 * Cloud Run configuration for dev environment
 * Creates orchestrator-api-dev and phidata-agent-ui-dev services
 */

# Cloud Run service for the Orchestra API
resource "google_cloud_run_v2_service" "orchestrator_api_dev" {
  name     = "orchestrator-api-dev"
  location = "us-west4"
  
  template {
    service_account = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
    
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra-images/api:${var.image_tag}"
      
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
            secret = "openai-api-key-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "ANTHROPIC_API_KEY"
        value_from {
          secret_key_ref {
            secret = "anthropic-api-key-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "GEMINI_API_KEY"
        value_from {
          secret_key_ref {
            secret = "gemini-api-key-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "REDIS_AUTH"
        value_from {
          secret_key_ref {
            secret = "redis-auth-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "DATABASE_PASSWORD"
        value_from {
          secret_key_ref {
            secret = "database-password-dev"
            version = "latest"
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
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    
    timeout = "300s"
  }
}

# Cloud Run service for the Phidata Agent UI
resource "google_cloud_run_v2_service" "phidata_agent_ui_dev" {
  name     = "phidata-agent-ui-dev"
  location = "us-west4"
  
  template {
    service_account = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
    
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra-images/ui:${var.image_tag}"
      
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
            secret = "openai-api-key-dev"
            version = "latest"
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
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
    
    timeout = "300s"
  }
}

# Allow unauthenticated access to the orchestrator API dev service
resource "google_cloud_run_service_iam_member" "orchestrator_api_dev_public" {
  project  = var.project_id
  location = "us-west4"
  service  = google_cloud_run_v2_service.orchestrator_api_dev.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow unauthenticated access to the phidata agent UI dev service
resource "google_cloud_run_service_iam_member" "phidata_agent_ui_dev_public" {
  project  = var.project_id
  location = "us-west4"
  service  = google_cloud_run_v2_service.phidata_agent_ui_dev.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output the service URLs
output "orchestrator_api_dev_url" {
  value       = google_cloud_run_v2_service.orchestrator_api_dev.uri
  description = "URL of the orchestrator-api-dev service"
}

output "phidata_agent_ui_dev_url" {
  value       = google_cloud_run_v2_service.phidata_agent_ui_dev.uri
  description = "URL of the phidata-agent-ui-dev service"
}

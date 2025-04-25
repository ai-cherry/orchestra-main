/**
 * Orchestra Cloud Run Services Terraform Configuration
 * 
 * This configuration provisions:
 * - Orchestra API service
 * - Phidata Agent UI service with proper configuration
 */

# Orchestra API Service
resource "google_cloud_run_v2_service" "orchestra_api" {
  name     = "orchestra-api-${var.env}"
  location = var.region
  
  template {
    containers {
      image = "gcr.io/${var.project_id}/orchestra-api:latest"
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.cache.host
      }
      
      env {
        name  = "REDIS_PORT"
        value = google_redis_instance.cache.port
      }
      
      # Reference Redis password from Secret Manager
      env {
        name = "REDIS_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.redis_auth.id
            version = "latest"
          }
        }
      }
    }
    
    service_account = "${var.project_id}@appspot.gserviceaccount.com"
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_redis_instance.cache,
    google_secret_manager_secret.redis_auth
  ]
}

# Phidata Agent UI Service
resource "google_cloud_run_v2_service" "phidata_agent_ui" {
  name     = "phidata-agent-ui-${var.env}"
  location = var.region
  
  template {
    containers {
      # Using the latest stable Phidata Agent UI image
      # Note: Verify this is the correct image and tag for your implementation
      image = "phidata/agent_ui:latest"
      
      ports {
        # Phidata Agent UI typically listens on port 8000
        container_port = 8000
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      # Connect to Orchestra API
      env {
        # PHIDATA_API_URL is the environment variable Phidata Agent UI 
        # uses to connect to the backend API
        name  = "PHIDATA_API_URL"
        value = google_cloud_run_v2_service.orchestra_api.uri
      }
      
      # Additional Phidata configuration variables
      env {
        name  = "PHIDATA_APP_NAME"
        value = "Orchestra"
      }
      
      env {
        name  = "PHIDATA_APP_DESCRIPTION"
        value = "Orchestra AI Agent Platform"
      }
      
      env {
        name  = "PHIDATA_TELEMETRY"
        value = "false"
      }
      
      # If using authentication
      env {
        name  = "PHIDATA_AUTH_ENABLED"
        value = "true"
      }
    }
    
    service_account = "${var.project_id}@appspot.gserviceaccount.com"
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_v2_service.orchestra_api
  ]
}

# IAM - Allow public access to the Phidata Agent UI
resource "google_cloud_run_service_iam_member" "phidata_agent_ui_public" {
  location = google_cloud_run_v2_service.phidata_agent_ui.location
  service  = google_cloud_run_v2_service.phidata_agent_ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output Cloud Run service URLs
output "service_urls" {
  value = {
    api     = google_cloud_run_v2_service.orchestra_api.uri
    ui      = google_cloud_run_v2_service.phidata_agent_ui.uri
  }
}
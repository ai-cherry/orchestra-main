# Cloud Run Services for AI Orchestra Development Environment

# Orchestrator API Service
resource "google_cloud_run_v2_service" "orchestrator_api" {
  name     = "orchestrator-api-dev"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "gcr.io/${var.project_id}/orchestrator-api:${var.image_tag}"
      
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
      
      # Environment variables
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      # Secret environment variables
      env {
        name = "REDIS_HOST"
        value_source {
          secret_key_ref {
            secret  = "redis-host-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "REDIS_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "redis-password-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "VERTEX_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "vertex-api-key-dev"
            version = "latest"
          }
        }
      }
    }
    
    service_account = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM policy for Orchestrator API Service - Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "orchestrator_api_public" {
  location = google_cloud_run_v2_service.orchestrator_api.location
  project  = google_cloud_run_v2_service.orchestrator_api.project
  name     = google_cloud_run_v2_service.orchestrator_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Phidata Agent UI Service
resource "google_cloud_run_v2_service" "phidata_agent_ui" {
  name     = "phidata-agent-ui-dev"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "gcr.io/${var.project_id}/phidata-agent-ui:${var.image_tag}"
      
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
      
      # Environment variables
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      # Secret environment variables
      env {
        name = "API_ENDPOINT"
        value_source {
          secret_key_ref {
            secret  = "api-endpoint-dev"
            version = "latest"
          }
        }
      }
      
      env {
        name = "AUTH_SECRET"
        value_source {
          secret_key_ref {
            secret  = "auth-secret-dev"
            version = "latest"
          }
        }
      }
    }
    
    service_account = "orchestra-runner-sa@${var.project_id}.iam.gserviceaccount.com"
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM policy for Phidata Agent UI Service - Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "phidata_agent_ui_public" {
  location = google_cloud_run_v2_service.phidata_agent_ui.location
  project  = google_cloud_run_v2_service.phidata_agent_ui.project
  name     = google_cloud_run_v2_service.phidata_agent_ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
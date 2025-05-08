# Performance-optimized Cloud Run configuration for AI Orchestra

# MCP Server Cloud Run Service
resource "google_cloud_run_v2_service" "mcp_server" {
  name     = "mcp-server-${var.env}"
  location = var.region
  
  template {
    scaling {
      min_instance_count = 2
      max_instance_count = 20
    }
    
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra/mcp-server:latest"
      
      resources {
        limits = {
          cpu    = "4"
          memory = "16Gi"
        }
        cpu_idle = false  # CPU always allocated
      }
      
      # Environment variables
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      env {
        name  = "REGION"
        value = var.region
      }
      
      # Secret environment variables
      env {
        name = "GCP_MASTER_SERVICE_JSON"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gcp_master_service_json.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "GH_CLASSIC_PAT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gh_classic_pat_token.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "GH_FINE_GRAINED_PAT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gh_fine_grained_pat_token.secret_id
            version = "latest"
          }
        }
      }
      
      # Container concurrency and timeout
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        timeout_seconds = 3
        period_seconds = 5
        failure_threshold = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        period_seconds = 15
        timeout_seconds = 5
        failure_threshold = 3
      }
    }
    
    # Container settings
    max_instance_request_concurrency = 80
    service_account = google_service_account.cloud_run_sa.email
    
    # Execution environment
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    
    # Request timeout
    timeout = "300s"
  }
  
  # Traffic configuration
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  # IAM policy
  depends_on = [
    google_secret_manager_secret.gcp_master_service_json,
    google_secret_manager_secret.gh_classic_pat_token,
    google_secret_manager_secret.gh_fine_grained_pat_token,
    google_service_account.cloud_run_sa
  ]
}

# AI Orchestra UI Cloud Run Service
resource "google_cloud_run_v2_service" "orchestra_ui" {
  name     = "orchestra-ui-${var.env}"
  location = var.region
  
  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }
    
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/orchestra/ui:latest"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
      
      # Environment variables
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      env {
        name  = "API_URL"
        value = google_cloud_run_v2_service.mcp_server.uri
      }
      
      # Container concurrency and timeout
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 3
        timeout_seconds = 2
        period_seconds = 5
        failure_threshold = 3
      }
    }
    
    # Request timeout
    timeout = "60s"
    max_instance_request_concurrency = 80
    service_account = google_service_account.cloud_run_sa.email
  }
  
  # Traffic configuration
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  depends_on = [
    google_cloud_run_v2_service.mcp_server
  ]
}

# Allow unauthenticated access to the MCP Server
resource "google_cloud_run_service_iam_member" "mcp_server_public_access" {
  location = google_cloud_run_v2_service.mcp_server.location
  service  = google_cloud_run_v2_service.mcp_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow unauthenticated access to the Orchestra UI
resource "google_cloud_run_service_iam_member" "orchestra_ui_public_access" {
  location = google_cloud_run_v2_service.orchestra_ui.location
  service  = google_cloud_run_v2_service.orchestra_ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "mcp_server_url" {
  description = "The URL of the MCP Server"
  value       = google_cloud_run_v2_service.mcp_server.uri
}

output "orchestra_ui_url" {
  description = "The URL of the Orchestra UI"
  value       = google_cloud_run_v2_service.orchestra_ui.uri
}
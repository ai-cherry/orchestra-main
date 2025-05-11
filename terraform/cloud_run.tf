# Cloud Run configuration for AI Orchestra
# This file contains all Cloud Run service related resources

# Create Cloud Run service with performance optimizations
resource "google_cloud_run_service" "ai_orchestra" {
  name     = "ai-orchestra-${var.env}"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.cloud_run_service_account.email
      
      containers {
        image = "gcr.io/${var.project_id}/ai-orchestra:latest"
        
        resources {
          limits = {
            cpu    = var.cloud_run_cpu
            memory = var.cloud_run_memory
          }
        }
        
        # Environment variables
        env {
          name  = "ENV"
          value = var.env
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCP_REGION"
          value = var.region
        }
        
        # Secret environment variables
        env {
          name = "SECRET_MANAGER_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.secret_management_key.secret_id
              key  = "latest"
            }
          }
        }
        
        # Performance optimizations
        env {
          name  = "PYTHONOPTIMIZE"
          value = "2"
        }
        
        env {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }
        
        # Startup probe for stability
        startup_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 5
          failure_threshold     = 3
        }
        
        # Liveness probe for stability
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 30
          timeout_seconds       = 5
          period_seconds        = 30
          failure_threshold     = 3
        }
      }
      
      # Concurrency settings for performance
      container_concurrency = var.cloud_run_concurrency
      timeout_seconds       = var.cloud_run_timeout
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = tostring(var.cloud_run_min_instances)
        "autoscaling.knative.dev/maxScale"        = tostring(var.cloud_run_max_instances)
        "run.googleapis.com/cpu-throttling"       = "false"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost"    = "true"
        "run.googleapis.com/vpc-access-egress"    = "all-traffic"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.ai_orchestra_repo,
    google_secret_manager_secret.secret_management_key,
    google_secret_manager_secret_version.initial_version
  ]
}

# Apply the IAM policy to the service
resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.ai_orchestra.location
  project     = google_cloud_run_service.ai_orchestra.project
  service     = google_cloud_run_service.ai_orchestra.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# Create Cloud Scheduler job to keep the service warm
resource "google_cloud_scheduler_job" "keep_warm_job" {
  name        = "ai-orchestra-${var.env}-keep-warm"
  description = "Keep AI Orchestra service warm to prevent cold starts"
  schedule    = var.scheduler_interval
  
  http_target {
    uri         = google_cloud_run_service.ai_orchestra.status[0].url
    http_method = "GET"
    
    headers = {
      "User-Agent" = "Google-Cloud-Scheduler"
    }
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_service.ai_orchestra
  ]
}
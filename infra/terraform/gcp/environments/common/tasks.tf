/**
 * Cloud Tasks resources for Orchestra project
 */

# Cloud Tasks Queue for Orchestra background tasks
resource "google_cloud_tasks_queue" "orchestra_tasks_queue" {
  name     = "${local.env_prefix}-tasks-queue"
  project  = var.project_id
  location = var.region
  
  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 20
  }
  
  retry_config {
    max_attempts = 5
    min_backoff  = "1s"
    max_backoff  = "60s"
    max_retry_duration = "4h"
    max_doublings = 3
  }
  
  # Add stackdriver logging
  stackdriver_logging_config {
    sampling_ratio = 1.0  # Log all tasks
  }
}

# Cloud Tasks Queue for Orchestra scheduled tasks
resource "google_cloud_tasks_queue" "orchestra_scheduled_tasks_queue" {
  name     = "${local.env_prefix}-scheduled-tasks-queue"
  project  = var.project_id
  location = var.region
  
  rate_limits {
    max_concurrent_dispatches = 5
    max_dispatches_per_second = 10
  }
  
  retry_config {
    max_attempts = 3
    min_backoff  = "5s"
    max_backoff  = "300s"
    max_retry_duration = "12h"
    max_doublings = 4
  }
  
  # Add stackdriver logging
  stackdriver_logging_config {
    sampling_ratio = 1.0  # Log all tasks
  }
}

# Cloud Scheduler job for regular maintenance tasks
resource "google_cloud_scheduler_job" "daily_maintenance" {
  name             = "${local.env_prefix}-daily-maintenance"
  project          = var.project_id
  region           = var.region
  description      = "Daily maintenance job for Orchestra"
  schedule         = "0 3 * * *"  # 3 AM every day
  time_zone        = "UTC"
  attempt_deadline = "320s"
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/maintenance-function"
    
    oidc_token {
      service_account_email = google_service_account.orchestra_runner_sa.email
    }
  }
}

# Outputs moved to outputs.tf

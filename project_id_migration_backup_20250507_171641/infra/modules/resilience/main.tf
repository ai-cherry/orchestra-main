/**
 * Resilience Module for Agent Orchestrator
 *
 * This module sets up Cloud Monitoring, Cloud Tasks, and Cloud Scheduler
 * resources for implementing the circuit breaker pattern for the AgentOrchestrator.
 */

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agi-baby-cherry"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_account_email" {
  description = "Service account email for fallback agent"
  type        = string
  default     = "vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
}

variable "task_queue_name" {
  description = "Name of the Cloud Tasks queue for retry operations"
  type        = string
  default     = "agent-retry-queue"
}

variable "app_engine_location" {
  description = "App Engine location for Cloud Tasks"
  type        = string
  default     = "us-central"
}

variable "failure_threshold" {
  description = "Number of consecutive failures before tripping circuit"
  type        = number
  default     = 3
}

variable "alert_notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# Enable required services
resource "google_project_service" "monitoring" {
  project = var.project_id
  service = "monitoring.googleapis.com"
  disable_dependent_services = false
}

resource "google_project_service" "logging" {
  project = var.project_id
  service = "logging.googleapis.com"
  disable_dependent_services = false
}

resource "google_project_service" "cloudtasks" {
  project = var.project_id
  service = "cloudtasks.googleapis.com"
  disable_dependent_services = false
}

resource "google_project_service" "scheduler" {
  project = var.project_id
  service = "cloudscheduler.googleapis.com"
  disable_dependent_services = false
}

resource "google_project_service" "appengine" {
  project = var.project_id
  service = "appengine.googleapis.com"
  disable_dependent_services = false
}

# Create App Engine application (required for Cloud Tasks)
resource "google_app_engine_application" "app" {
  project     = var.project_id
  location_id = var.app_engine_location
  depends_on  = [google_project_service.appengine]
  
  # Add lifecycle block to prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

# Create Cloud Tasks queue for retry operations
resource "google_cloud_tasks_queue" "retry_queue" {
  name     = var.task_queue_name
  location = var.region
  project  = var.project_id
  
  depends_on = [
    google_project_service.cloudtasks,
    google_app_engine_application.app
  ]
  
  rate_limits {
    max_dispatches_per_second = 5
    max_concurrent_dispatches = 10
  }
  
  retry_config {
    max_attempts       = 5
    max_retry_duration = "4s"
    min_backoff        = "1s"
    max_backoff        = "10s"
    max_doublings      = 3
  }
}

# Create log metric for agent failures
resource "google_logging_metric" "agent_failures" {
  name        = "agent_orchestrator_failures"
  description = "Count of agent failures in the orchestrator"
  filter      = "resource.type=\"cloud_run_revision\" AND jsonPayload.incident_type=\"agent_failure\""
  project     = var.project_id
  
  depends_on = [google_project_service.logging]
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "agent_id"
      value_type  = "STRING"
      description = "ID of the agent that failed"
    }
  }
}

# Create log metric for circuit trips
resource "google_logging_metric" "circuit_trips" {
  name        = "agent_circuit_trips"
  description = "Count of circuit trips in the circuit breaker"
  filter      = "resource.type=\"cloud_run_revision\" AND jsonPayload.incident_type=\"circuit_trip\""
  project     = var.project_id
  
  depends_on = [google_project_service.logging]
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "agent_id"
      value_type  = "STRING"
      description = "ID of the agent whose circuit was tripped"
    }
  }
}

# Create log metric for fallback activations
resource "google_logging_metric" "fallback_activations" {
  name        = "agent_fallback_activations"
  description = "Count of fallbacks to vertex-agent"
  filter      = "resource.type=\"cloud_run_revision\" AND jsonPayload.incident_type=\"fallback_activation\""
  project     = var.project_id
  
  depends_on = [google_project_service.logging]
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "original_agent"
      value_type  = "STRING"
      description = "ID of the original agent that failed"
    }
    labels {
      key         = "fallback_agent"
      value_type  = "STRING"
      description = "ID of the fallback agent"
    }
  }
}

# Create alert policy for consecutive failures
resource "google_monitoring_alert_policy" "consecutive_failures" {
  display_name = "Agent Consecutive Failures"
  project      = var.project_id
  combiner     = "OR"
  
  depends_on = [google_project_service.monitoring]
  
  conditions {
    display_name = "Agent failure count exceeds threshold"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.agent_failures.name}\" AND resource.type=\"cloud_run_revision\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.failure_threshold
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
        group_by_fields    = ["metric.label.agent_id"]
      }
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = var.alert_notification_channels
  
  documentation {
    content = <<-EOT
      ## Agent Consecutive Failures Alert
      
      An agent has experienced ${var.failure_threshold} or more consecutive failures.
      
      The circuit breaker has been tripped and requests are being routed to the fallback agent.
      
      ### Investigation Steps:
      
      1. Check Cloud Logging for detailed error information.
      2. Verify the agent configuration.
      3. Examine any recent changes to the agent code or dependencies.
      
      ### Resolution Steps:
      
      1. Fix the underlying issue causing the failures.
      2. Reset the circuit breaker if needed.
      3. Verify the agent is functioning correctly.
    EOT
    mime_type = "text/markdown"
  }
}

# Create alert policy for high fallback rate
resource "google_monitoring_alert_policy" "high_fallback_rate" {
  display_name = "High Fallback Rate to Vertex Agent"
  project      = var.project_id
  combiner     = "OR"
  
  depends_on = [google_project_service.monitoring]
  
  conditions {
    display_name = "Fallback rate exceeds threshold"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.fallback_activations.name}\" AND resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5  # 5 fallbacks in 5 minutes
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = var.alert_notification_channels
  
  documentation {
    content = <<-EOT
      ## High Fallback Rate Alert
      
      The system is experiencing a high rate of fallbacks to the vertex-agent.
      
      This indicates that primary agents are failing at an elevated rate.
      
      ### Investigation Steps:
      
      1. Check which agents are failing most frequently.
      2. Review recent deployments or configuration changes.
      3. Examine Cloud Logging for detailed error information.
      
      ### Resolution Steps:
      
      1. Address any underlying issues with the failing agents.
      2. Consider scaling resources if the issue is load-related.
      3. Verify fallback agent has sufficient capacity to handle the load.
    EOT
    mime_type = "text/markdown"
  }
}

# Create Cloud Scheduler job to check for stuck circuits
resource "google_cloud_scheduler_job" "circuit_checker" {
  name        = "agent-circuit-checker"
  description = "Periodically checks for stuck circuits and resets them if needed"
  schedule    = "*/15 * * * *"  # Every 15 minutes
  project     = var.project_id
  region      = var.region
  
  depends_on = [google_project_service.scheduler]
  
  http_target {
    uri         = "https://orchestra-prod-${var.project_id}.run.app/internal/health/check-circuits"
    http_method = "POST"
    
    oidc_token {
      service_account_email = var.service_account_email
      audience              = "https://orchestra-prod-${var.project_id}.run.app"
    }
  }
}

# IAM binding for vertex-agent service account
resource "google_project_iam_binding" "vertex_agent_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  
  members = [
    "serviceAccount:${var.service_account_email}",
  ]
}

# IAM binding for logging permissions
resource "google_project_iam_binding" "vertex_agent_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  
  members = [
    "serviceAccount:${var.service_account_email}",
  ]
}

# Output values
output "task_queue_id" {
  value       = google_cloud_tasks_queue.retry_queue.id
  description = "ID of the created Cloud Tasks queue"
}

output "agent_failures_metric" {
  value       = google_logging_metric.agent_failures.id
  description = "ID of the agent failures metric"
}

output "circuit_trips_metric" {
  value       = google_logging_metric.circuit_trips.id
  description = "ID of the circuit trips metric"
}

output "fallback_activations_metric" {
  value       = google_logging_metric.fallback_activations.id
  description = "ID of the fallback activations metric"
}

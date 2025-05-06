// Advanced Monitoring System with LLM Analysis and Auto-Scaling
// Created: May 1, 2025

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

variable "service_names" {
  description = "Map of service names to their criticality (critical or non-critical)"
  type        = map(string)
}

variable "alert_notification_emails" {
  description = "List of email addresses to notify for alerts"
  type        = list(string)
  default     = []
}

variable "github_repo" {
  description = "GitHub repository name (org/repo) for issue creation"
  type        = string
}

variable "github_token_secret_id" {
  description = "Secret Manager secret ID for GitHub access token"
  type        = string
}

variable "vertex_ai_region" {
  description = "GCP region for Vertex AI resources"
  type        = string
  default     = "us-central1"
}

variable "log_analysis_model" {
  description = "Vertex AI model to use for log analysis"
  type        = string
  default     = "text-bison@002"
}

variable "scaling_prediction_model" {
  description = "Vertex AI model for predictive scaling"
  type        = string
  default     = "forecast-timeseries"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com"
  ])
  
  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create notification channel for email alerts
resource "google_monitoring_notification_channel" "email" {
  count        = length(var.alert_notification_emails)
  display_name = "Orchestra Advanced Alert - ${var.alert_notification_emails[count.index]}"
  type         = "email"
  
  labels = {
    email_address = var.alert_notification_emails[count.index]
  }
  
  user_labels = {
    environment = var.env
    system      = "advanced-monitoring"
  }
}

# Cloud Storage bucket for log exports
resource "google_storage_bucket" "log_archive" {
  name     = "${var.project_id}-log-archive-${var.env}"
  location = var.region
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 30  # Archive logs older than 30 days
    }
    action {
      type = "ARCHIVE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 365  # Delete logs older than 1 year
    }
    action {
      type = "DELETE"
    }
  }
}

# Log sink for exporting logs
resource "google_logging_project_sink" "log_export" {
  name        = "advanced-monitoring-log-export-${var.env}"
  destination = "storage.googleapis.com/${google_storage_bucket.log_archive.name}"
  filter      = "resource.type=\"cloud_run_revision\" OR resource.type=\"cloud_function\" OR severity>=WARNING"

  unique_writer_identity = true
}

# Grant sink service account permissions to write to bucket
resource "google_storage_bucket_iam_binding" "log_writer" {
  bucket = google_storage_bucket.log_archive.name
  role   = "roles/storage.objectCreator"
  
  members = [
    google_logging_project_sink.log_export.writer_identity,
  ]
}

# LLM-based log analysis function
resource "google_cloudfunctions_function" "log_analyzer" {
  name        = "llm-log-analyzer-${var.env}"
  description = "Analyzes logs with LLMs to detect issues and suggest fixes"
  runtime     = "python310"
  
  available_memory_mb   = 1024
  source_archive_bucket = google_storage_bucket.log_archive.name
  source_archive_object = google_storage_bucket_object.log_analyzer_code.name
  entry_point           = "analyze_logs"
  
  environment_variables = {
    PROJECT_ID       = var.project_id
    ENVIRONMENT      = var.env
    VERTEX_AI_REGION = var.vertex_ai_region
    MODEL_ID         = var.log_analysis_model
    GITHUB_REPO      = var.github_repo
  }

  secret_environment_variables {
    key        = "GITHUB_TOKEN"
    project_id = var.project_id
    secret     = var.github_token_secret_id
    version    = "latest"
  }
  
  service_account_email = google_service_account.log_analyzer_sa.email
  
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.log_archive.name
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Service account for log analyzer
resource "google_service_account" "log_analyzer_sa" {
  account_id   = "log-analyzer-sa-${var.env}"
  display_name = "Log Analyzer Service Account"
  
  description = "Service account for LLM-based log analysis and GitHub issue creation"
}

# Source code for log analyzer function
resource "google_storage_bucket_object" "log_analyzer_code" {
  name   = "log-analyzer-${var.env}.zip"
  bucket = google_storage_bucket.log_archive.name
  source = "path/to/log_analyzer.zip"  # This file needs to be created by the build process
}

# Grant necessary permissions to log analyzer service account
resource "google_project_iam_binding" "log_analyzer_permissions" {
  for_each = toset([
    "roles/logging.viewer",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor"
  ])
  
  project = var.project_id
  role    = each.key
  
  members = [
    "serviceAccount:${google_service_account.log_analyzer_sa.email}",
  ]
}

# Cloud Run job for GitHub issue creation
resource "google_cloud_run_v2_job" "github_issue_creator" {
  name     = "github-issue-creator-${var.env}"
  location = var.region
  
  template {
    template {
      containers {
        image = "gcr.io/${var.project_id}/github-issue-creator:latest"
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.env
        }
        
        env {
          name  = "GITHUB_REPO"
          value = var.github_repo
        }
        
        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.anomaly_detection.name
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
        
        volume_mounts {
          name       = "github-token"
          mount_path = "/secrets"
        }
      }
      
      volumes {
        name = "github-token"
        secret {
          secret       = var.github_token_secret_id
          items {
            key  = "latest"
            path = "github-token"
          }
        }
      }
      
      service_account = google_service_account.github_issue_sa.email
      timeout         = "300s"
    }
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Service account for GitHub issue creator
resource "google_service_account" "github_issue_sa" {
  account_id   = "github-issue-sa-${var.env}"
  display_name = "GitHub Issue Creator Service Account"
  
  description = "Service account for GitHub issue creation"
}

# PubSub topic for anomaly detection
resource "google_pubsub_topic" "anomaly_detection" {
  name = "anomaly-detection-${var.env}"
}

# Vertex AI Prediction Service for Scale-to-Zero and Predictive Scaling
resource "google_cloud_run_v2_service" "predictive_scaling_service" {
  name     = "predictive-scaling-service-${var.env}"
  location = var.region
  
  template {
    containers {
      image = "gcr.io/${var.project_id}/predictive-scaling:latest"
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      
      env {
        name  = "VERTEX_AI_REGION"
        value = var.vertex_ai_region
      }
      
      env {
        name  = "PREDICTION_MODEL"
        value = var.scaling_prediction_model
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }
    
    service_account = google_service_account.scaling_service_sa.email
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Service account for predictive scaling service
resource "google_service_account" "scaling_service_sa" {
  account_id   = "predictive-scaling-sa-${var.env}"
  display_name = "Predictive Scaling Service Account"
  
  description = "Service account for Vertex AI-based predictive scaling"
}

# Grant necessary permissions to predictive scaling service account
resource "google_project_iam_binding" "scaling_service_permissions" {
  for_each = toset([
    "roles/run.admin",
    "roles/aiplatform.user",
    "roles/monitoring.viewer"
  ])
  
  project = var.project_id
  role    = each.key
  
  members = [
    "serviceAccount:${google_service_account.scaling_service_sa.email}",
  ]
}

# Dynamic Scaling Policies for Each Service
resource "google_cloud_run_v2_service" "service_scaling_config" {
  for_each = { for k, v in var.service_names : k => v if v == "non-critical" }
  
  name     = each.key
  location = var.region
  
  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
  
  # This is applying the scaling config to existing services, not creating new ones
  lifecycle {
    ignore_changes = [
      template[0].containers,
      template[0].volumes,
      client,
      client_version,
      annotations,
      labels,
      binary_authorization,
      template[0].service_account,
    ]
  }
}

# Create Alert Policies with LLM-Powered Alerting
resource "google_monitoring_alert_policy" "llm_enhanced_alerts" {
  for_each     = var.service_names
  display_name = "LLM-Enhanced Alert - ${each.key} - ${var.env}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Anomaly Detection with LLM Analysis"
    
    condition_monitoring_query_language {
      query = <<-EOT
      fetch cloud_run_revision
      | filter resource.labels.service_name == '${each.key}'
      | {
          metric run.googleapis.com/request_count
          | align rate(1m)
          | group_by [resource.service_name], [value_request_count: sum(value.request_count)]
          | condition val() > 0;
          metric run.googleapis.com/request_latencies
          | align delta(1m)
          | group_by [resource.service_name], [value_latency: percentile(value.request_latencies, 95)]
          | condition val() > ${each.value == "critical" ? 2000 : 5000}
      }
      EOT
      
      duration = "300s"
      
      trigger {
        count = 1
      }
    }
  }
  
  conditions {
    display_name = "Error Rate Increase"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${each.key}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.01  # 1% error rate
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.labels.service_name"]
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  documentation {
    content = <<-EOT
    ## AI-Enhanced Alert for ${each.key}

    This alert combines traditional metrics with AI analysis to provide deeper insights.

    ### Impact Assessment
    The service ${each.key} in ${var.env} environment is experiencing issues that our AI has analyzed.

    ### Next Steps
    1. Check the GitHub issues automatically created for this anomaly
    2. Review the AI-suggested fixes in the issue description
    3. Check Logs Explorer for raw logs with filter:
       resource.type="cloud_run_revision" AND resource.labels.service_name="${each.key}" AND severity>=WARNING
    
    ### Auto-remediation
    For non-critical services, automatic scale-to-zero may have been applied.
    Predictive scaling has adjusted capacity based on Vertex AI forecasts.
    EOT
    
    mime_type = "text/markdown"
  }
  
  # Notification channels
  notification_channels = [
    for channel in google_monitoring_notification_channel.email : channel.name
  ]
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Cloud Scheduler job to trigger predictive scaling
resource "google_cloud_scheduler_job" "predictive_scaling_job" {
  name             = "predictive-scaling-job-${var.env}"
  description      = "Triggers predictive scaling analysis every hour"
  schedule         = "0 * * * *"  # Every hour
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"
  
  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.predictive_scaling_service.uri}/predict"
    
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Service account for Cloud Scheduler
resource "google_service_account" "scheduler_sa" {
  account_id   = "scheduler-sa-${var.env}"
  display_name = "Cloud Scheduler Service Account"
  
  description = "Service account for invoking predictive scaling service"
}

# Grant necessary permissions to scheduler service account
resource "google_project_iam_binding" "scheduler_permissions" {
  project = var.project_id
  role    = "roles/run.invoker"
  
  members = [
    "serviceAccount:${google_service_account.scheduler_sa.email}",
  ]
}

# Outputs
output "log_archive_bucket" {
  value       = google_storage_bucket.log_archive.name
  description = "Name of the log archive bucket"
}

output "log_analyzer_function" {
  value       = google_cloudfunctions_function.log_analyzer.name
  description = "Name of the LLM-powered log analyzer function"
}

output "github_issue_creator_job" {
  value       = google_cloud_run_v2_job.github_issue_creator.name
  description = "Name of the GitHub issue creator job"
}

output "predictive_scaling_service" {
  value       = google_cloud_run_v2_service.predictive_scaling_service.name
  description = "Name of the predictive scaling service"
}

output "anomaly_detection_topic" {
  value       = google_pubsub_topic.anomaly_detection.name
  description = "Name of the anomaly detection PubSub topic"
}
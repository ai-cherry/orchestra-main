# monitoring.tf
# Monitoring configuration for AI Orchestra GCP Migration

# Latency alert policy for Cloud Run service
resource "google_monitoring_alert_policy" "latency_alert" {
  display_name = "${var.service_prefix} - High Latency Alert"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "High latency detected"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 500  # 500 milliseconds
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }

  # Notification channels can be added here when available
  # notification_channels = [
  #   "projects/${var.project_id}/notificationChannels/${var.notification_channel_id}",
  # ]

  user_labels = {
    service     = var.cloud_run_service_name
    environment = var.env
  }

  depends_on = [google_project_service.required_apis]
}

# Error rate alert policy for Cloud Run service
resource "google_monitoring_alert_policy" "error_rate_alert" {
  display_name = "${var.service_prefix} - High Error Rate Alert"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "High error rate detected"
    condition_threshold {
      filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      
      denominator_filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_count\""
      
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05  # 5% error rate
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      denominator_aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  user_labels = {
    service     = var.cloud_run_service_name
    environment = var.env
  }

  depends_on = [google_project_service.required_apis]
}

# Uptime check for the service
resource "google_monitoring_uptime_check_config" "uptime_check" {
  display_name = "${var.service_prefix} - Uptime Check"
  timeout      = "10s"
  period       = "60s"
  project      = var.project_id

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = google_cloud_run_service.api_service.status[0].url
    }
  }

  depends_on = [google_cloud_run_service.api_service]
}

# Dashboard for Cloud Run service metrics
resource "google_monitoring_dashboard" "service_dashboard" {
  dashboard_json = jsonencode({
    displayName = "${var.service_prefix} - Service Dashboard"
    gridLayout = {
      widgets = [
        {
          title = "Request Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_count\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
              legendTemplate = "Request Count"
            }]
          }
        },
        {
          title = "Latency (95th percentile)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_PERCENTILE_95"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
              legendTemplate = "Latency"
            }]
          }
        },
        {
          title = "Error Rate"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
              legendTemplate = "5xx Errors"
            }]
          }
        },
        {
          title = "Instance Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/container/instance_count\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
              legendTemplate = "Instance Count"
            }]
          }
        }
      ]
    }
  })
  project = var.project_id

  depends_on = [google_cloud_run_service.api_service]
}
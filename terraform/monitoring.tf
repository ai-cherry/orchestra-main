# Monitoring configuration for AI Orchestra
# This file contains all monitoring and alerting related resources

# Create Cloud Monitoring alert policy for performance monitoring
resource "google_monitoring_alert_policy" "high_latency_alert" {
  display_name = "AI Orchestra ${var.env} High Latency Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High latency"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.latency_threshold_ms
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }

  notification_channels = []  # Add notification channels as needed
  
  depends_on = [google_project_service.required_apis]
}

# Create CPU utilization alert
resource "google_monitoring_alert_policy" "high_cpu_alert" {
  display_name = "AI Orchestra ${var.env} High CPU Utilization Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High CPU utilization"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/container/cpu/utilization\""
      duration        = "300s"  # 5 minutes
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8     # 80% utilization
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Create memory utilization alert
resource "google_monitoring_alert_policy" "high_memory_alert" {
  display_name = "AI Orchestra ${var.env} High Memory Utilization Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High memory utilization"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/container/memory/utilization\""
      duration        = "300s"  # 5 minutes
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8     # 80% utilization
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Create error rate alert
resource "google_monitoring_alert_policy" "high_error_rate_alert" {
  display_name = "AI Orchestra ${var.env} High Error Rate Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High error rate"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"4xx\" OR metric.labels.response_code_class = \"5xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5  # More than 5 errors per minute
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Create dashboard for monitoring
resource "google_monitoring_dashboard" "ai_orchestra_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "AI Orchestra ${var.env} Dashboard",
  "gridLayout": {
    "widgets": [
      {
        "title": "Request Latency",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/request_latencies\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_PERCENTILE_95",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "CPU Utilization",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/container/cpu/utilization\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Memory Utilization",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/container/memory/utilization\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Request Count",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ai-orchestra-${var.env}\" AND metric.type = \"run.googleapis.com/request_count\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              }
            }
          ]
        }
      }
    ]
  }
}
EOF

  depends_on = [google_project_service.required_apis]
}
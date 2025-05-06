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

variable "service_name" {
  description = "Name of the Cloud Run service to monitor"
  type        = string
}

variable "alert_notification_emails" {
  description = "List of email addresses to notify for alerts"
  type        = list(string)
  default     = []
}

variable "enable_slo_alerts" {
  description = "Enable SLO-based alerts"
  type        = bool
  default     = true
}

# Enable Cloud Monitoring API
resource "google_project_service" "monitoring_api" {
  project = var.project_id
  service = "monitoring.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create notification channel for email alerts
resource "google_monitoring_notification_channel" "email" {
  count        = length(var.alert_notification_emails)
  display_name = "Orchestra Email Alert - ${var.alert_notification_emails[count.index]}"
  type         = "email"
  
  labels = {
    email_address = var.alert_notification_emails[count.index]
  }
  
  user_labels = {
    environment = var.env
  }
}

# Alert Policy for High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate - ${var.service_name} - ${var.env}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Error Rate > 5% for 5 minutes"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"4xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05  # 5%
      
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
    ## High Error Rate Alert

    The ${var.service_name} service in ${var.env} environment is experiencing a high rate of 4xx errors.

    ### Impact
    User requests are failing at an abnormal rate.

    ### Possible Causes
    * Invalid input from users
    * Service misconfiguration
    * Authentication/authorization issues

    ### Resolution Steps
    1. Check Cloud Logging for detailed error messages
    2. Review recent deployments or configuration changes
    3. Verify dependencies (LLM services, databases) are responding normally
    4. Check for rate limits on external services
    EOT
    
    mime_type = "text/markdown"
  }
  
  # File an incident
  alert_strategy {
    auto_close = "1800s"  # Auto-close after 30 minutes of resolution
    
    notification_rate_limit {
      period = "300s"  # Limit notifications to once every 5 minutes
    }
  }
  
  # Notification channels
  notification_channels = [
    for channel in google_monitoring_notification_channel.email : channel.name
  ]
  
  depends_on = [
    google_project_service.monitoring_api
  ]
}

# Alert Policy for High Latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "High Latency - ${var.service_name} - ${var.env}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "P95 Latency > 2s for 10 minutes"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "600s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.env == "prod" ? 2000 : 5000  # 2s for prod, 5s for non-prod (in ms)
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
        group_by_fields      = ["resource.labels.service_name"]
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  documentation {
    content = <<-EOT
    ## High Latency Alert

    The ${var.service_name} service in ${var.env} environment is experiencing high request latency.

    ### Impact
    Users are experiencing slow response times.

    ### Possible Causes
    * Increased traffic load
    * LLM provider delays
    * Database performance issues
    * Resource constraints

    ### Resolution Steps
    1. Check Cloud Logging for slow requests
    2. Verify LLM provider status (Portkey/OpenRouter dashboards)
    3. Check database performance and connection pool stats
    4. Consider scaling up resources if load is the issue
    EOT
    
    mime_type = "text/markdown"
  }
  
  # Notification channels
  notification_channels = [
    for channel in google_monitoring_notification_channel.email : channel.name
  ]
  
  depends_on = [
    google_project_service.monitoring_api
  ]
}

# Dashboard for service monitoring
resource "google_monitoring_dashboard" "service_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "${var.service_name} - ${var.env} Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Request Count",
        "xyChart": {
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Error Rate",
        "xyChart": {
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"4xx\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM"
                  }
                },
                "unitOverride": "1"
              }
            }
          ]
        }
      },
      {
        "title": "Latency (95th percentile)",
        "xyChart": {
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_PERCENTILE_95"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Instance Count",
        "xyChart": {
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/container/instance_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
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
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/container/memory/utilizations\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                },
                "unitOverride": "10^2.%"
              }
            }
          ]
        }
      },
      {
        "title": "CPU Utilization",
        "xyChart": {
          "chartOptions": {
            "mode": "COLOR"
          },
          "dataSets": [
            {
              "minAlignmentPeriod": "60s",
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/container/cpu/utilizations\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                },
                "unitOverride": "10^2.%"
              }
            }
          ]
        }
      }
    ]
  }
}
EOF

  depends_on = [
    google_project_service.monitoring_api
  ]
}

# Define SLO (Service Level Objective) for availability
resource "google_monitoring_slo" "availability_slo" {
  count = var.enable_slo_alerts ? 1 : 0
  
  service                     = var.service_name
  slo_id                      = "orchestra-availability-slo-${var.env}"
  display_name                = "${var.service_name} Availability SLO - ${var.env}"
  goal                        = var.env == "prod" ? 0.995 : 0.99  # 99.5% for prod, 99% for non-prod
  calendar_period             = "DAY"
  
  basic_sli {
    availability {
      enabled = true
    }
  }

  depends_on = [
    google_project_service.monitoring_api
  ]
}

# Define SLO (Service Level Objective) for latency
resource "google_monitoring_slo" "latency_slo" {
  count = var.enable_slo_alerts ? 1 : 0
  
  service                     = var.service_name
  slo_id                      = "orchestra-latency-slo-${var.env}"
  display_name                = "${var.service_name} Latency SLO - ${var.env}"
  goal                        = 0.95  # 95% of requests should meet the latency threshold
  calendar_period             = "DAY"
  
  request_based_sli {
    distribution_cut {
      distribution_filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      range {
        max = var.env == "prod" ? 2000 : 5000  # 2s for prod, 5s for non-prod (in ms)
      }
    }
  }

  depends_on = [
    google_project_service.monitoring_api
  ]
}

# Create SLO Alert Policies
resource "google_monitoring_alert_policy" "slo_burn_rate_alert" {
  count        = var.enable_slo_alerts ? 1 : 0
  display_name = "SLO Burn Rate Alert - ${var.service_name} - ${var.env}"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Fast burn rate - availability SLO"
    
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${google_monitoring_slo.availability_slo[0].name}\", \"1h\")"
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10  # Burn rate threshold
      
      trigger {
        count = 1
      }
    }
  }
  
  documentation {
    content = <<-EOT
    ## SLO Budget Burn Rate Alert

    The ${var.service_name} service in ${var.env} environment is consuming its error budget too quickly.

    ### Impact
    The service is at risk of missing its SLO targets.

    ### Possible Causes
    * Sudden increase in errors
    * Performance degradation
    * External dependency issues

    ### Resolution Steps
    1. Check recent error logs
    2. Investigate performance metrics
    3. Verify health of dependencies
    4. Consider rolling back recent changes
    EOT
    
    mime_type = "text/markdown"
  }
  
  # Notification channels
  notification_channels = [
    for channel in google_monitoring_notification_channel.email : channel.name
  ]
  
  depends_on = [
    google_monitoring_slo.availability_slo
  ]
}

# Custom log-based metrics and alerts (additional potential monitoring)
resource "google_logging_metric" "llm_error_metric" {
  name        = "custom.googleapis.com/orchestrator/llm_integration_errors_${var.env}"
  filter      = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND textPayload:\"LLM client error\""
  description = "Count of LLM integration errors"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "severity"
      value_type  = "STRING"
      description = "The severity of the log entry"
    }
  }
  label_extractors = {
    "severity" = "EXTRACT(severity)"
  }
}

output "dashboard_name" {
  value       = google_monitoring_dashboard.service_dashboard.id
  description = "The ID of the created monitoring dashboard"
}

output "notification_channels" {
  value       = [for channel in google_monitoring_notification_channel.email : channel.name]
  description = "The notification channels created"
}

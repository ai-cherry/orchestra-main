# modules/monitoring/main.tf
# Comprehensive monitoring setup for AI Orchestra resources on GCP
# 
# This module sets up monitoring for all deployed resources including:
# - Cloud Run services
# - AlloyDB clusters
# - Vertex AI endpoints
# - PubSub topics
# - Cloud Storage buckets
# - Custom metrics for business operations

# Required providers
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.50.0"
    }
  }
}

locals {
  # Generate dashboards based on enabled resource types
  enable_cloud_run_dashboard     = contains(var.resource_types, "cloud_run")
  enable_alloydb_dashboard       = contains(var.resource_types, "alloydb")
  enable_vertex_ai_dashboard     = contains(var.resource_types, "vertex_ai")
  enable_vector_search_dashboard = contains(var.resource_types, "vector_search")
  
  # Common dashboard settings
  common_dashboard_settings = {
    project_id   = var.project_id
    environment  = var.environment
    service_name = var.service_prefix
  }
}

# Alerting policy for Cloud Run latency
resource "google_monitoring_alert_policy" "cloud_run_latency" {
  count        = var.enable_latency_alerts && local.enable_cloud_run_dashboard ? 1 : 0
  
  project      = var.project_id
  display_name = "${var.service_prefix} - Cloud Run Latency Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High Latency for Cloud Run services"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/request_latencies\" AND metric.labels.response_code_class = \"2xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.latency_threshold_ms
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  user_labels = {
    service     = var.service_prefix
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Alerting policy for Cloud Run error rates
resource "google_monitoring_alert_policy" "cloud_run_error_rate" {
  count        = var.enable_error_rate_alerts && local.enable_cloud_run_dashboard ? 1 : 0
  
  project      = var.project_id
  display_name = "${var.service_prefix} - Cloud Run Error Rate Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High Error Rate for Cloud Run services"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.error_rate_threshold_percent / 100.0  # Convert to percentage
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      denominator_filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/request_count\""
      
      denominator_aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  user_labels = {
    service     = var.service_prefix
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Alerting policy for AlloyDB CPU usage
resource "google_monitoring_alert_policy" "alloydb_cpu_usage" {
  count        = var.enable_resource_usage_alerts && local.enable_alloydb_dashboard ? 1 : 0
  
  project      = var.project_id
  display_name = "${var.service_prefix} - AlloyDB CPU Usage Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High CPU Usage for AlloyDB"
    condition_threshold {
      filter          = "resource.type = \"alloydb.googleapis.com/Instance\" AND metric.type = \"alloydb.googleapis.com/instance/cpu/utilization\""
      duration        = "300s"  # 5 minutes
      comparison      = "COMPARISON_GT"
      threshold_value = var.cpu_usage_threshold_percent / 100.0  # Convert to percentage
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  user_labels = {
    service     = var.service_prefix
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Alerting policy for Vertex AI endpoint prediction errors
resource "google_monitoring_alert_policy" "vertex_ai_errors" {
  count        = var.enable_error_rate_alerts && local.enable_vertex_ai_dashboard ? 1 : 0
  
  project      = var.project_id
  display_name = "${var.service_prefix} - Vertex AI Endpoint Errors"
  combiner     = "OR"
  
  conditions {
    display_name = "High Error Rate for Vertex AI Endpoints"
    condition_threshold {
      filter          = "resource.type = \"aiplatform.googleapis.com/Endpoint\" AND metric.type = \"aiplatform.googleapis.com/prediction/errors\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.error_rate_threshold_percent / 100.0  # Convert to percentage
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      denominator_filter = "resource.type = \"aiplatform.googleapis.com/Endpoint\" AND metric.type = \"aiplatform.googleapis.com/prediction/request_count\""
      
      denominator_aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  user_labels = {
    service     = var.service_prefix
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Uptime checks for Cloud Run services
resource "google_monitoring_uptime_check_config" "cloud_run_uptime" {
  count          = var.enable_uptime_checks && local.enable_cloud_run_dashboard ? 1 : 0
  
  project        = var.project_id
  display_name   = "${var.service_prefix} - Admin API Uptime Check"
  timeout        = "10s"
  period         = "60s"
  
  http_check {
    path             = "/health"
    port             = "443"
    use_ssl          = true
    validate_ssl     = true
    request_method   = "GET"
    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = "${var.service_prefix}-admin-api-${var.project_id}.${var.region}.run.app"
    }
  }
  
  content_matchers {
    content = "ok"
    matcher = "CONTAINS_STRING"
  }
}

# Dashboard for Cloud Run services
resource "google_monitoring_dashboard" "cloud_run_dashboard" {
  count          = local.enable_cloud_run_dashboard ? 1 : 0
  
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "${var.service_prefix} - Cloud Run Dashboard"
    
    gridLayout = {
      widgets = [
        {
          title = "Request Latency (95th percentile)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/request_latencies\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_PERCENTILE_95"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Latency (ms)"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Request Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/request_count\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Requests per second"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Error Rate"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Error rate"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Instance Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_prefix}-admin-api\" AND metric.type = \"run.googleapis.com/container/instance_count\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Instance count"
              scale = "LINEAR"
            }
          }
        }
      ]
    }
  })
}

# Dashboard for AlloyDB
resource "google_monitoring_dashboard" "alloydb_dashboard" {
  count          = local.enable_alloydb_dashboard ? 1 : 0
  
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "${var.service_prefix} - AlloyDB Dashboard"
    
    gridLayout = {
      widgets = [
        {
          title = "CPU Utilization"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"alloydb.googleapis.com/Instance\" AND metric.type = \"alloydb.googleapis.com/instance/cpu/utilization\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "CPU Utilization"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Memory Utilization"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"alloydb.googleapis.com/Instance\" AND metric.type = \"alloydb.googleapis.com/instance/memory/utilization\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Memory Utilization"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Active Connections"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"alloydb.googleapis.com/Instance\" AND metric.type = \"alloydb.googleapis.com/instance/postgresql/num_backends\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Connection count"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Disk Usage"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"alloydb.googleapis.com/Instance\" AND metric.type = \"alloydb.googleapis.com/instance/disk/bytes_used\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Disk usage (bytes)"
              scale = "LINEAR"
            }
          }
        }
      ]
    }
  })
}

# Dashboard for Vertex AI
resource "google_monitoring_dashboard" "vertex_ai_dashboard" {
  count          = local.enable_vertex_ai_dashboard ? 1 : 0
  
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "${var.service_prefix} - Vertex AI Dashboard"
    
    gridLayout = {
      widgets = [
        {
          title = "Prediction Requests"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"aiplatform.googleapis.com/Endpoint\" AND metric.type = \"aiplatform.googleapis.com/prediction/request_count\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Requests per second"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Prediction Latency"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"aiplatform.googleapis.com/Endpoint\" AND metric.type = \"aiplatform.googleapis.com/prediction/prediction_latencies\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_PERCENTILE_95"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Latency (ms)"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Prediction Errors"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type = \"aiplatform.googleapis.com/Endpoint\" AND metric.type = \"aiplatform.googleapis.com/prediction/errors\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    alignmentPeriod = "60s"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Errors per second"
              scale = "LINEAR"
            }
          }
        }
      ]
    }
  })
}

# Metric descriptors for custom metrics
resource "google_monitoring_metric_descriptor" "vector_search_latency" {
  count       = var.enable_custom_metrics && local.enable_vector_search_dashboard ? 1 : 0
  
  project      = var.project_id
  description  = "Vector search operation latency"
  display_name = "Vector Search Latency"
  type         = "custom.googleapis.com/ai_orchestra/vector_search/latency"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"
  unit         = "ms"
  
  labels {
    key          = "index_name"
    description  = "Name of the vector index"
    value_type   = "STRING"
  }
  
  labels {
    key          = "operation_type"
    description  = "Type of vector search operation"
    value_type   = "STRING"
  }
}

resource "google_monitoring_metric_descriptor" "model_inference_latency" {
  count       = var.enable_custom_metrics && local.enable_vertex_ai_dashboard ? 1 : 0
  
  project      = var.project_id
  description  = "Model inference operation latency"
  display_name = "Model Inference Latency"
  type         = "custom.googleapis.com/ai_orchestra/model/inference_latency"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"
  unit         = "ms"
  
  labels {
    key          = "model_name"
    description  = "Name of the AI model"
    value_type   = "STRING"
  }
  
  labels {
    key          = "operation_type"
    description  = "Type of model operation"
    value_type   = "STRING"
  }
}

# Dashboard for vector search metrics
resource "google_monitoring_dashboard" "vector_search_dashboard" {
  count          = var.enable_custom_metrics && local.enable_vector_search_dashboard ? 1 : 0
  
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "${var.service_prefix} - Vector Search Dashboard"
    
    gridLayout = {
      widgets = [
        {
          title = "Vector Search Latency"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type = \"custom.googleapis.com/ai_orchestra/vector_search/latency\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_PERCENTILE_95"
                    alignmentPeriod = "60s"
                    crossSeriesReducer = "REDUCE_MEAN"
                    groupByFields = ["metric.labels.index_name"]
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Latency (ms)"
              scale = "LINEAR"
            }
          }
        }
      ]
    }
  })
}
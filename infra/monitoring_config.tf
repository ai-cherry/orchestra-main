# Terraform configuration for monitoring AGI Baby Cherry workloads
# Focused on Redis-AlloyDB sync performance and Hybrid IDE health

# Import the monitoring module
module "monitoring" {
  source     = "github.com/GoogleCloudPlatform/terraform-google-monitoring//modules/policies"
  project_id = var.project_id
  
  # Enable alert notifications (via Pub/Sub, email, etc.)
  notification_channels = [
    {
      display_name = "AGI-Baby-Cherry-Alerts"
      type         = "email"
      labels = {
        email_address = "alerts@cherry-ai-project.example.com"
      }
    }
  ]
  
  alert_policies = [
    # Redis-AlloyDB Sync Latency Alert
    {
      display_name = "Redis-AlloyDB Sync Latency"
      documentation = {
        content   = "Redis to AlloyDB sync latency exceeded threshold. Target is <5ms P99 latency."
        mime_type = "text/markdown"
      }
      conditions = [{
        display_name = "High sync latency"
        condition_threshold = {
          filter          = "metric.type=\"custom.googleapis.com/sync_latency\" resource.type=\"global\""
          comparison      = "COMPARISON_GT"
          threshold_value = 5  # 5 ms latency threshold
          duration        = "60s"
          aggregations = [{
            alignment_period     = "60s"
            per_series_aligner   = "ALIGN_PERCENTILE_99"
            cross_series_reducer = "REDUCE_MEAN"
          }]
        }
      }]
      severity           = "WARNING"
      notification_rate_limit = {
        period = "300s"
      }
      alerts_suppressor = {
        suppression_duration = "1800s"
        suppression_ratio    = 0.5
      }
    },
    
    # CPU Usage Alert for Hybrid IDE
    {
      display_name = "Hybrid IDE High CPU Usage"
      documentation = {
        content   = "High CPU usage detected on Hybrid IDE instances. This may impact development performance."
        mime_type = "text/markdown"
      }
      conditions = [{
        display_name = "High CPU usage"
        condition_threshold = {
          filter          = "metric.type=\"compute.googleapis.com/instance/cpu/utilization\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")"
          comparison      = "COMPARISON_GT"
          threshold_value = 0.8  # 80% CPU utilization
          duration        = "300s"
          aggregations = [{
            alignment_period   = "60s"
            per_series_aligner = "ALIGN_MEAN"
          }]
        }
      }]
      severity           = "WARNING"
      notification_rate_limit = {
        period = "1800s"
      }
    },
    
    # Memory Usage Alert for Hybrid IDE
    {
      display_name = "Hybrid IDE High Memory Usage"
      documentation = {
        content   = "High memory usage detected on Hybrid IDE instances. This may impact development performance."
        mime_type = "text/markdown"
      }
      conditions = [{
        display_name = "High memory usage"
        condition_threshold = {
          filter          = "metric.type=\"compute.googleapis.com/instance/memory/percent_used\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")"
          comparison      = "COMPARISON_GT"
          threshold_value = 0.85  # 85% memory utilization
          duration        = "300s"
          aggregations = [{
            alignment_period   = "60s"
            per_series_aligner = "ALIGN_MEAN"
          }]
        }
      }]
      severity           = "WARNING"
      notification_rate_limit = {
        period = "1800s"
      }
    },
    
    # Redis Connection Errors
    {
      display_name = "Redis Connection Errors"
      documentation = {
        content   = "Redis connection errors detected. This may impact agent memory access and sync operations."
        mime_type = "text/markdown"
      }
      conditions = [{
        display_name = "Redis connection errors"
        condition_threshold = {
          filter          = "metric.type=\"custom.googleapis.com/redis_connection_errors\" resource.type=\"global\""
          comparison      = "COMPARISON_GT"
          threshold_value = 0  # Any errors
          duration        = "60s"
          aggregations = [{
            alignment_period   = "60s"
            per_series_aligner = "ALIGN_SUM"
          }]
        }
      }]
      severity           = "ALERT"
      notification_rate_limit = {
        period = "300s"
      }
    },
    
    # AlloyDB Long-Running Queries
    {
      display_name = "AlloyDB Long-Running Queries"
      documentation = {
        content   = "Long-running queries detected in AlloyDB. This may impact database performance and sync operations."
        mime_type = "text/markdown"
      }
      conditions = [{
        display_name = "Long-running queries"
        condition_threshold = {
          filter          = "metric.type=\"alloydb.googleapis.com/database/postgresql/query_duration\" resource.type=\"alloydb.googleapis.com/Instance\""
          comparison      = "COMPARISON_GT"
          threshold_value = 5000  # 5000 ms (5 seconds)
          duration        = "300s"
          aggregations = [{
            alignment_period   = "60s"
            per_series_aligner = "ALIGN_PERCENTILE_95"
          }]
        }
      }]
      severity           = "WARNING"
      notification_rate_limit = {
        period = "1800s"
      }
    }
  ]
}

# Custom Dashboard for Redis-AlloyDB Sync Performance
resource "google_monitoring_dashboard" "redis_alloydb_sync_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "Redis-AlloyDB Sync Performance",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Sync Latency (P99)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/sync_latency\" resource.type=\"global\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_PERCENTILE_99",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }
          ],
          "yAxis": {
            "label": "Latency (ms)",
            "scale": "LINEAR"
          },
          "thresholds": [
            {
              "value": 5,
              "label": "P99 Latency Target (5ms)",
              "targetAxis": "Y1",
              "color": "RED"
            }
          ]
        }
      },
      {
        "title": "Records Synced per Minute",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/records_synced\" resource.type=\"global\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }
          ],
          "yAxis": {
            "label": "Records per minute",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Sync Errors",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/sync_errors\" resource.type=\"global\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }
          ],
          "yAxis": {
            "label": "Error count",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Database Connection Status",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/db_connection_status\" resource.type=\"global\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }
          ],
          "yAxis": {
            "label": "Connection status (1=connected, 0=disconnected)",
            "scale": "LINEAR"
          }
        }
      }
    ]
  }
}
EOF

  project = var.project_id
}

# Performance Test Results Dashboard
resource "google_monitoring_dashboard" "performance_test_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "Hybrid IDE Performance Test Results",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "IDE Stress Test - CPU Usage",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"compute.googleapis.com/instance/cpu/utilization\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }
          ],
          "yAxis": {
            "label": "CPU utilization",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "IDE Stress Test - Memory Usage",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"compute.googleapis.com/instance/memory/percent_used\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }
          ],
          "yAxis": {
            "label": "Memory utilization",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "IDE Stress Test - Disk I/O",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"compute.googleapis.com/instance/disk/read_bytes_count\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1",
              "legendTemplate": "Read bytes"
            },
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"compute.googleapis.com/instance/disk/write_bytes_count\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1",
              "legendTemplate": "Write bytes"
            }
          ],
          "yAxis": {
            "label": "Bytes/sec",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "IDE Stress Test - Network I/O",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"compute.googleapis.com/instance/network/received_bytes_count\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1",
              "legendTemplate": "Received bytes"
            },
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"compute.googleapis.com/instance/network/sent_bytes_count\" resource.type=\"gce_instance\" metadata.system_labels.name=starts_with(\"hybrid-workstation\")",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1",
              "legendTemplate": "Sent bytes"
            }
          ],
          "yAxis": {
            "label": "Bytes/sec",
            "scale": "LINEAR"
          }
        }
      }
    ]
  }
}
EOF

  project = var.project_id
}

# Output dashboard URLs
output "monitoring_dashboard_urls" {
  description = "URLs for monitoring dashboards"
  value = {
    "redis_alloydb_sync" = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.redis_alloydb_sync_dashboard.id}?project=${var.project_id}"
    "performance_test"   = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.performance_test_dashboard.id}?project=${var.project_id}"
  }
}

/**
 * BigQuery Cost Tracking Dashboard for Orchestra
 * 
 * This Terraform module creates a BigQuery dataset and tables for 
 * cost analysis, as well as budget alerts when costs exceed thresholds.
 */

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "billing_account_id" {
  description = "Billing account ID for budget configuration"
  type        = string
}

variable "monthly_budget" {
  description = "Monthly budget amount in USD"
  type        = number
  default     = 1000
}

variable "budget_alert_thresholds" {
  description = "List of budget alert thresholds (0.0 to 1.0)"
  type        = list(number)
  default     = [0.5, 0.8, 0.9, 1.0]
}

variable "alert_pubsub_topic" {
  description = "Optional existing Pub/Sub topic for budget alerts"
  type        = string
  default     = ""
}

variable "notification_emails" {
  description = "Email addresses to notify for budget alerts"
  type        = list(string)
  default     = []
}

# BigQuery Dataset for Cost Analysis
resource "google_bigquery_dataset" "cost_metrics" {
  dataset_id    = "cost_metrics"
  friendly_name = "Orchestra Cost Metrics"
  description   = "Dataset containing cost metrics and usage data for Orchestra"
  location      = var.location
  project       = var.project_id
  
  default_table_expiration_ms = 7776000000  # 90 days
  
  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }
  
  access {
    role          = "READER"
    special_group = "projectReaders"
  }
  
  access {
    role          = "WRITER"
    special_group = "projectWriters"
  }
  
  labels = {
    environment = "production"
    purpose     = "cost_monitoring"
  }
}

# Table for Workbench Usage
resource "google_bigquery_table" "workbench_usage" {
  dataset_id = google_bigquery_dataset.cost_metrics.dataset_id
  table_id   = "workbench_usage"
  project    = var.project_id
  
  description = "Vertex AI Workbench usage and cost metrics"
  
  time_partitioning {
    type          = "DAY"
    field         = "usage_date"
    expiration_ms = 15552000000  # 180 days
  }
  
  schema = <<EOF
[
  {
    "name": "usage_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique identifier for the usage record"
  },
  {
    "name": "instance_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Vertex Workbench instance ID"
  },
  {
    "name": "usage_date",
    "type": "DATE",
    "mode": "REQUIRED",
    "description": "Date of the usage record"
  },
  {
    "name": "start_time",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Start time of the usage period"
  },
  {
    "name": "end_time",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "End time of the usage period"
  },
  {
    "name": "cpu_usage_hours",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "CPU usage in hours"
  },
  {
    "name": "memory_usage_gb_hours",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Memory usage in GB-hours"
  },
  {
    "name": "gpu_usage_hours",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "GPU usage in hours"
  },
  {
    "name": "estimated_cost_usd",
    "type": "FLOAT",
    "mode": "REQUIRED",
    "description": "Estimated cost in USD"
  },
  {
    "name": "user_id",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "User ID that generated the usage"
  },
  {
    "name": "project_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "GCP Project ID"
  }
]
EOF

  labels = {
    environment = "production"
    data_type   = "workbench_usage"
  }
}

# Table for Memory Storage Costs
resource "google_bigquery_table" "memory_storage_costs" {
  dataset_id = google_bigquery_dataset.cost_metrics.dataset_id
  table_id   = "memory_storage_costs"
  project    = var.project_id
  
  description = "Memory storage usage and costs (Redis, AlloyDB)"
  
  time_partitioning {
    type          = "DAY"
    field         = "usage_date"
    expiration_ms = 15552000000  # 180 days
  }
  
  schema = <<EOF
[
  {
    "name": "record_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique identifier for the record"
  },
  {
    "name": "usage_date",
    "type": "DATE",
    "mode": "REQUIRED",
    "description": "Date of the usage record"
  },
  {
    "name": "storage_type",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Type of storage (Redis, AlloyDB)"
  },
  {
    "name": "storage_instance_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Storage instance identifier"
  },
  {
    "name": "storage_size_gb",
    "type": "FLOAT",
    "mode": "REQUIRED",
    "description": "Storage size in GB"
  },
  {
    "name": "request_count",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Number of requests"
  },
  {
    "name": "egress_gb",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Data egress in GB"
  },
  {
    "name": "estimated_cost_usd",
    "type": "FLOAT",
    "mode": "REQUIRED",
    "description": "Estimated cost in USD"
  },
  {
    "name": "project_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "GCP Project ID"
  }
]
EOF

  labels = {
    environment = "production"
    data_type   = "memory_storage_costs"
  }
}

# Create a Pub/Sub topic for budget alerts if not provided
resource "google_pubsub_topic" "budget_alerts" {
  count   = var.alert_pubsub_topic == "" ? 1 : 0
  name    = "budget-alerts"
  project = var.project_id
  
  labels = {
    purpose = "budget_notifications"
  }
}

# Local variable for pubsub topic
locals {
  pubsub_topic = var.alert_pubsub_topic != "" ? var.alert_pubsub_topic : google_pubsub_topic.budget_alerts[0].id
}

# Budget configuration
resource "google_billing_budget" "budget" {
  billing_account = var.billing_account_id
  display_name    = "Orchestra Project Budget"
  
  budget_filter {
    projects = ["projects/${var.project_id}"]
  }
  
  amount {
    specified_amount {
      currency_code = "USD"
      units         = var.monthly_budget
    }
  }
  
  # Create a threshold rule for each threshold percentage
  dynamic "threshold_rules" {
    for_each = var.budget_alert_thresholds
    content {
      threshold_percent = threshold_rules.value
      spend_basis       = threshold_rules.value == 1.0 ? "FORECASTED_SPEND" : "CURRENT_SPEND"
    }
  }
  
  # Configure all update rules
  all_updates_rule {
    pubsub_topic = local.pubsub_topic
    
    # Add email notifications if provided
    dynamic "monitoring_notification_channels" {
      for_each = length(var.notification_emails) > 0 ? [1] : []
      content {
        email = var.notification_emails
      }
    }
  }
}

# Data Transfer Jobs for Billing Export

# Billing export to BigQuery job
resource "google_bigquery_data_transfer_config" "billing_export" {
  display_name           = "Billing Export to BigQuery"
  data_source_id         = "billing"
  destination_dataset_id = google_bigquery_dataset.cost_metrics.dataset_id
  location               = var.location
  project                = var.project_id
  
  params = {
    billing_account        = var.billing_account_id
    records_update_option  = "OVERWRITE"
  }
  
  schedule = "every 24 hours"
}

# SQL to create a view for memory system costs
resource "google_bigquery_table" "memory_system_costs_view" {
  dataset_id = google_bigquery_dataset.cost_metrics.dataset_id
  table_id   = "memory_system_costs_view"
  project    = var.project_id
  
  view {
    query = <<-EOF
      SELECT
        service.description as service,
        sku.description as sku,
        usage_start_time,
        usage_end_time,
        project.id as project_id,
        cost,
        currency,
        usage.amount as usage_amount,
        usage.unit as usage_unit,
        CASE
          WHEN sku.description LIKE '%Redis%' OR service.description = 'Cloud Memorystore' THEN 'Redis'
          WHEN sku.description LIKE '%AlloyDB%' OR service.description = 'AlloyDB' THEN 'AlloyDB'
          WHEN sku.description LIKE '%Vertex%' OR service.description = 'Vertex AI' THEN 'Vertex AI'
          ELSE 'Other'
        END as memory_component
      FROM
        `${google_bigquery_dataset.cost_metrics.project}.${google_bigquery_dataset.cost_metrics.dataset_id}.billing_data`
      WHERE
        (service.description = 'Cloud Memorystore' OR
         service.description = 'AlloyDB' OR
         service.description = 'Vertex AI' OR
         sku.description LIKE '%Redis%' OR
         sku.description LIKE '%AlloyDB%' OR
         sku.description LIKE '%Vertex%')
      ORDER BY
        usage_start_time DESC
    EOF
    use_legacy_sql = false
  }
  
  depends_on = [
    google_bigquery_data_transfer_config.billing_export
  ]
}

# Outputs
output "dataset_id" {
  value       = google_bigquery_dataset.cost_metrics.dataset_id
  description = "BigQuery dataset ID for cost metrics"
}

output "budget_id" {
  value       = google_billing_budget.budget.id
  description = "Budget ID for the Orchestra project"
}

output "budget_alert_pubsub_topic" {
  value       = local.pubsub_topic
  description = "Pub/Sub topic for budget alerts"
}

output "dashboard_creation_command" {
  value       = "gcloud monitoring dashboards create --config-from-file=dashboard.json"
  description = "Command to create the monitoring dashboard"
}

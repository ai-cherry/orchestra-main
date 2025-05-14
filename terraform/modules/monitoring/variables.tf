# modules/monitoring/variables.tf
# Variables for the monitoring module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "service_prefix" {
  description = "Prefix for service names"
  type        = string
  default     = "ai-orchestra"
}

variable "resource_types" {
  description = "List of resource types to monitor (cloud_run, alloydb, vertex_ai, vector_search)"
  type        = list(string)
  default     = ["cloud_run", "alloydb", "vertex_ai", "vector_search"]
}

variable "notification_channels" {
  description = "List of notification channel IDs to send alerts to"
  type        = list(string)
  default     = []
}

variable "enable_latency_alerts" {
  description = "Enable latency alert policies"
  type        = bool
  default     = true
}

variable "enable_error_rate_alerts" {
  description = "Enable error rate alert policies"
  type        = bool
  default     = true
}

variable "enable_resource_usage_alerts" {
  description = "Enable resource usage alert policies (CPU, memory, disk)"
  type        = bool
  default     = true
}

variable "enable_uptime_checks" {
  description = "Enable uptime check configurations"
  type        = bool
  default     = true
}

variable "enable_custom_metrics" {
  description = "Enable custom metric descriptors and dashboards"
  type        = bool
  default     = true
}

variable "latency_threshold_ms" {
  description = "Threshold for latency alerts in milliseconds"
  type        = number
  default     = 500
}

variable "error_rate_threshold_percent" {
  description = "Threshold for error rate alerts in percentage"
  type        = number
  default     = 5
}

variable "cpu_usage_threshold_percent" {
  description = "Threshold for CPU usage alerts in percentage"
  type        = number
  default     = 80
}

variable "memory_usage_threshold_percent" {
  description = "Threshold for memory usage alerts in percentage"
  type        = number
  default     = 80
}

variable "dashboard_refresh_interval" {
  description = "Dashboard refresh interval in seconds"
  type        = number
  default     = 300
}

variable "monitoring_scope" {
  description = "Scope of monitoring (service, project, organization)"
  type        = string
  default     = "service"
}

# Variables for cost tracking

variable "billing_account_id" {
  description = "Billing account ID for budget configuration"
  type        = string
  default     = ""
  sensitive   = true
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
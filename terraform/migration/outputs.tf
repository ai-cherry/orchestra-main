# outputs.tf
# Output values for AI Orchestra GCP Migration

# Cloud Run service URL
output "service_url" {
  value       = google_cloud_run_service.api_service.status[0].url
  description = "URL of the deployed Cloud Run service"
}

# Service account email
output "service_account_email" {
  value       = google_service_account.service_account.email
  description = "Email of the service account used by the Cloud Run service"
}

# Secret ID
output "api_key_secret_id" {
  value       = google_secret_manager_secret.api_key.id
  description = "ID of the API key secret in Secret Manager"
}

# Cloud Run service name
output "cloud_run_service_name" {
  value       = google_cloud_run_service.api_service.name
  description = "Name of the deployed Cloud Run service"
}

# Dashboard URL
output "monitoring_dashboard_url" {
  value       = "https://console.cloud.google.com/monitoring/dashboards/builder/${replace(google_monitoring_dashboard.service_dashboard.id, "/", "~2F")}?project=${var.project_id}"
  description = "URL to access the monitoring dashboard"
}

# Uptime check URL
output "uptime_check_url" {
  value       = "https://console.cloud.google.com/monitoring/uptime?project=${var.project_id}"
  description = "URL to access the uptime check dashboard"
}

# Alerts URL
output "alerts_url" {
  value       = "https://console.cloud.google.com/monitoring/alerting?project=${var.project_id}"
  description = "URL to access the alerts dashboard"
}

# Project ID
output "project_id" {
  value       = var.project_id
  description = "The project ID where resources were deployed"
}

# Region
output "region" {
  value       = var.region
  description = "The region where resources were deployed"
}

# Environment
output "environment" {
  value       = var.env
  description = "The deployment environment"
}
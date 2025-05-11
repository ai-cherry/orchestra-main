# Outputs for AI Orchestra performance-optimized deployment
# This file centralizes all outputs for better organization

# Output the service URL
output "service_url" {
  value       = google_cloud_run_service.ai_orchestra.status[0].url
  description = "The URL of the deployed Cloud Run service"
}

# Output the service account email
output "cloud_run_service_account_email" {
  value       = google_service_account.cloud_run_service_account.email
  description = "The email of the service account used by the Cloud Run service"
}

# Output the secret ID
output "secret_id" {
  value       = google_secret_manager_secret.secret_management_key.id
  description = "The ID of the Secret Manager secret for authentication"
}

# Output the artifact repository URL
output "artifact_repository_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ai_orchestra_repo.repository_id}"
  description = "The URL of the Artifact Registry repository"
}

# Output the monitoring dashboard URL
output "monitoring_dashboard_url" {
  value       = "https://console.cloud.google.com/monitoring/dashboards/builder/${google_monitoring_dashboard.ai_orchestra_dashboard.id}?project=${var.project_id}"
  description = "The URL of the monitoring dashboard"
}

# Output the environment
output "environment" {
  value       = var.env
  description = "The environment (dev, staging, prod)"
}

# Output the region
output "region" {
  value       = var.region
  description = "The GCP region"
}

# Output the project ID
output "project_id" {
  value       = var.project_id
  description = "The GCP project ID"
}

# Output the Cloud Run service name
output "service_name" {
  value       = google_cloud_run_service.ai_orchestra.name
  description = "The name of the Cloud Run service"
}

# Output the Cloud Run service revision
output "service_revision" {
  value       = google_cloud_run_service.ai_orchestra.status[0].latest_created_revision_name
  description = "The latest revision of the Cloud Run service"
}
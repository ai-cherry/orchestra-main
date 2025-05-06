output "project_id" {
  description = "The project ID"
  value       = "cherry-ai.me"
}

output "project_number" {
  description = "The project number"
  value       = "525398941159"
}

output "region" {
  description = "The region where resources are deployed"
  value       = var.region
}

output "service_account_email" {
  description = "The email of the service account"
  value       = "vertex-agent@cherry-ai.me.iam.gserviceaccount.com"
}

output "artifact_registry_repository" {
  description = "The Artifact Registry repository URL"
  value       = "us-central1-docker.pkg.dev/cherry-ai.me/orchestra"
}

output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.orchestra_api.status[0].url
}

output "model_bucket" {
  description = "The GCS bucket for model storage"
  value       = "gs://cherry-ai-me-model-artifacts"
}
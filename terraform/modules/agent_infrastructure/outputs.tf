# Outputs for the agent infrastructure module

output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.orchestra_api.uri
}

output "service_account_email" {
  description = "The email of the service account used by the Cloud Run service"
  value       = var.service_account_create ? google_service_account.orchestra_sa[0].email : var.service_account_name
}

output "redis_host" {
  description = "The host of the Redis instance"
  value       = google_redis_instance.orchestra_cache.host
}

output "redis_port" {
  description = "The port of the Redis instance"
  value       = google_redis_instance.orchestra_cache.port
}

output "firestore_database" {
  description = "The name of the Firestore database"
  value       = google_firestore_database.orchestra_db.name
}

output "storage_bucket" {
  description = "The name of the storage bucket"
  value       = google_storage_bucket.orchestra_artifacts.name
}

output "secret_names" {
  description = "The names of the created secrets"
  value       = var.create_secrets ? [for secret in google_secret_manager_secret.api_keys : secret.name] : []
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}